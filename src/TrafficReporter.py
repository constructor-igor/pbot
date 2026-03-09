"""
TrafficReporter
───────────────
Утреннее сообщение о пробках по трём маршрутам из Модиина.
Использует Google Maps Routes API (computeRouteMatrix) — новый API с 2025.

Отправляется только если хотя бы один маршрут задержан >= MIN_DELAY_MINUTES.
Пятница и суббота пропускаются автоматически.

Пример сообщения:
  🚗 Пробки сейчас (08:00)

  Модиин → Тель-Авив      45 мин  🔴 +18 мин
  Модиин → Иерусалим      32 мин  🟡 +7 мин
  Модиин → Реховот        22 мин  🟢 норма

API отличия от старого Distance Matrix:
  - POST с JSON body вместо GET с параметрами
  - Ключ в заголовке X-Goog-Api-Key
  - Обязательный заголовок X-Goog-FieldMask
  - duration     = время С учётом трафика (routingPreference: TRAFFIC_AWARE)
  - static_duration = время БЕЗ трафика (базовое)
  - Ответ — плоский список с originIndex + destinationIndex
"""

import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Координаты Модиина и городов назначения (latLng точнее чем адрес)
ROUTES = [
    {
        "label":       "Модиин → Тель-Авив",
        "origin":      {"latitude": 31.8969, "longitude": 34.9838},   # Modi'in center
        "destination": {"latitude": 32.0853, "longitude": 34.7818},   # Tel Aviv center
    },
    {
        "label":       "Модиин → Иерусалим",
        "origin":      {"latitude": 31.8969, "longitude": 34.9838},
        "destination": {"latitude": 31.7683, "longitude": 35.2137},   # Jerusalem center
    },
    {
        "label":       "Модиин → Реховот",
        "origin":      {"latitude": 31.8969, "longitude": 34.9838},
        "destination": {"latitude": 31.8928, "longitude": 34.8113},   # Rehovot center
    },
]

ROUTES_API_URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"


class TrafficReporter:

    MIN_DELAY_MINUTES: int = 10

    def __init__(
        self,
        bot,
        channel_id: int | str,
        google_maps_api_key: str,
        routes: list[dict] | None = None,
    ) -> None:
        self.bot        = bot
        self.channel_id = channel_id
        self.api_key    = google_maps_api_key
        self.routes     = routes or ROUTES

    # ── public ───────────────────────────────────────────────────────────────

    async def send(self) -> bool:
        """Fetch and send if delays >= MIN_DELAY_MINUTES. Skip Fri/Sat."""
        if datetime.now().weekday() in (4, 5):
            logger.info("Weekend — skipping traffic report.")
            return False

        results = self._fetch_all_routes()
        if not results:
            logger.warning("No traffic data received.")
            return False

        max_delay = max(r["delay_minutes"] for r in results)
        if max_delay < self.MIN_DELAY_MINUTES:
            logger.info("Traffic clear (max delay %d min), skipping.", max_delay)
            return False

        await self.bot.send_message(chat_id=self.channel_id,
                                    text=self._build_message(results))
        logger.info("Traffic message sent (max delay %d min).", max_delay)
        return True

    def build_message(self) -> str:
        """Sync wrapper for SchedulerMessage."""
        results = self._fetch_all_routes()
        if not results:
            return ""
        if max(r["delay_minutes"] for r in results) < self.MIN_DELAY_MINUTES:
            return ""
        return self._build_message(results)

    # ── private: fetching ────────────────────────────────────────────────────

    def _fetch_all_routes(self) -> list[dict]:
        """
        Single POST to Routes API computeRouteMatrix.

        Request structure:
          origins:      list of waypoints (one per route, same origin for all)
          destinations: list of waypoints (one per route)
          routingPreference: TRAFFIC_AWARE — duration includes traffic
          travelMode:   DRIVE

        Response: flat list of elements, each with:
          originIndex, destinationIndex,
          duration       ("123s" — WITH traffic),
          static_duration ("100s" — WITHOUT traffic, the baseline)
        """
        origins = [
            {"waypoint": {"location": {"latLng": r["origin"]}}}
            for r in self.routes
        ]
        destinations = [
            {"waypoint": {"location": {"latLng": r["destination"]}}}
            for r in self.routes
        ]

        body = {
            "origins":            origins,
            "destinations":       destinations,
            "travelMode":         "DRIVE",
            "routingPreference":  "TRAFFIC_AWARE",
        }
        headers = {
            "Content-Type":     "application/json",
            "X-Goog-Api-Key":   self.api_key,
            # Request only the fields we need — reduces cost and payload
            "X-Goog-FieldMask": "originIndex,destinationIndex,status,duration,staticDuration",
        }

        resp = requests.post(ROUTES_API_URL, json=body, headers=headers, timeout=10)
        resp.raise_for_status()

        # Response is a JSON array (streamed, but requests reads it fully)
        elements = resp.json()
        if not isinstance(elements, list):
            logger.error("Unexpected Routes API response: %s", elements)
            return []

        # Build lookup: (originIndex, destinationIndex) → element
        # We only care about diagonal: origin[i] → destination[i]
        lookup = {}
        for el in elements:
            key = (el.get("originIndex", 0), el.get("destinationIndex", 0))
            lookup[key] = el

        results = []
        for i, route in enumerate(self.routes):
            el = lookup.get((i, i))
            if not el:
                logger.warning("No element for route %s", route["label"])
                continue

            status = el.get("status", {})
            if status.get("code", 0) != 0:   # 0 = OK in gRPC status
                logger.warning("Route %s error: %s", route["label"], status)
                continue

            # duration / staticDuration come as strings like "1234s"
            dur_traffic = self._parse_duration(el.get("duration",       "0s"))
            dur_static  = self._parse_duration(el.get("staticDuration", "0s"))
            delay_sec   = max(0, dur_traffic - dur_static)

            results.append({
                "label":         route["label"],
                "minutes":       round(dur_traffic / 60),
                "delay_minutes": round(delay_sec   / 60),
            })

        return results

    @staticmethod
    def _parse_duration(duration_str: str) -> int:
        """Convert '1234s' → 1234 (seconds)."""
        return int(duration_str.rstrip("s"))

    # ── private: formatting ──────────────────────────────────────────────────

    def _build_message(self, results: list[dict]) -> str:
        now = datetime.now().strftime("%H:%M")
        lines = [f"🚗 Пробки сейчас ({now})", ""]
        for r in results:
            emoji     = self._delay_emoji(r["delay_minutes"])
            delay_str = f"+{r['delay_minutes']} мин" if r["delay_minutes"] > 0 else "норма"
            lines.append(f"{r['label']}    {r['minutes']} мин  {emoji} {delay_str}")
        return "\n".join(lines)

    @staticmethod
    def _delay_emoji(delay: int) -> str:
        if delay <= 5:  return "🟢"
        if delay <= 15: return "🟡"
        return "🔴"