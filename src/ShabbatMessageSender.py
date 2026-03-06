"""
ShabbatMessageSender
────────────────────
Каждую пятницу в 11:00 отправляет в Telegram-канал сообщение вида:

  📅 28 февраля (10 адара 5786)  Суббота — недельная глава Тецаве
  🕯 Зажигание свечей: 17:17
  ✨ Выход субботы: 18:13
  🌤 Погода: 6°–16°  Малооблачно
  
  Будь в курсе событий Модиина! Подписывайся 👉 t.me/modiin_ru

Запускать: python ShabbatMessageSender.py
или подключить к scheduler (APScheduler / cron).
"""

import requests
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from WeatherClient import WeatherClient

logger = logging.getLogger(__name__)


# ── Hebrew month names in Russian ────────────────────────────────────────────
HEBREW_MONTHS_RU: dict[str, str] = {
    "Nisan":    "нисана",   "Iyyar":     "ияра",
    "Sivan":    "сивана",   "Tamuz":     "тамуза",
    "Av":       "ава",      "Elul":      "элула",
    "Tishrei":  "тишрея",   "Cheshvan":  "хешвана",
    "Kislev":   "кислева",  "Tevet":     "тевета",
    "Shvat":    "швата",    "Adar":      "адара",
    "Adar I":   "адара I",  "Adar II":   "адара II",
}

# ── Russian month names (full) ────────────────────────────────────────────────
MONTHS_RU: list[str] = [
    "", "января","февраля","марта","апреля","мая","июня",
    "июля","августа","сентября","октября","ноября","декабря",
]

# ── Weather description translation (OWM → Russian) ──────────────────────────
WEATHER_DESC_RU: dict[str, str] = {
    "clear sky":           "Ясно",
    "few clouds":          "Малооблачно",
    "scattered clouds":    "Переменная облачность",
    "broken clouds":       "Облачно",
    "overcast clouds":     "Пасмурно",
    "light rain":          "Небольшой дождь",
    "moderate rain":       "Дождь",
    "heavy intensity rain":"Сильный дождь",
    "shower rain":         "Ливень",
    "thunderstorm":        "Гроза",
    "snow":                "Снег",
    "mist":                "Дымка",
    "fog":                 "Туман",
    "haze":                "Мгла",
    "dust":                "Пыль",
    "sand":                "Песчаная буря",
}


class ShabbatMessageSender:
    """Collects Shabbat data and sends a weekly Friday message to a Telegram channel."""

    # Hebcal GeoNames ID for Modiin-Maccabim-Reut
    MODIIN_GEONAME_ID: int = 282926
    HEBCAL_SHABBAT_URL: str = "https://www.hebcal.com/shabbat"

    def __init__(self, bot: Bot, weather_client: WeatherClient, channel_link: str = "t.me/modiin_ru") -> None:
        self.bot          = bot
        self.channel_id   = -1001193789881
        self.wc           = weather_client
        self.channel_link = channel_link

    # ── public ───────────────────────────────────────────────────────────────

    async def send_if_friday(self) -> bool:
        """Call this method every day at 11:00. Sends only on Fridays. Returns True if sent."""
        if datetime.now().weekday() != 4:   # 4 = Friday
            logger.info("Not Friday, skipping Shabbat message.")
            return False
        await self.send()
        return True

    async def send(self) -> None:
        """Build and send the Shabbat message unconditionally."""
        text = self._build_message()
        await self._send_telegram(text)
        logger.info("Shabbat message sent.")

    # ── private: data fetching ────────────────────────────────────────────────

    def _fetch_shabbat_data(self) -> dict:
        """
        Fetch candle lighting, havdalah and parasha from Hebcal.
        Returns dict with keys: candles, havdalah, parasha, shabbat_date, hebrew_date
        """
        params = {
            "cfg":        "json",
            "geonameid":  self.MODIIN_GEONAME_ID,
            "M":          "on",       # havdalah at nightfall (tzeit)
            "lg":         "s",        # Sephardic transliteration
            "leyning":    "off",      # skip aliyot details
        }
        resp = requests.get(self.HEBCAL_SHABBAT_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        result: dict = {
            "candles":      None,   # "17:17"
            "havdalah":     None,   # "18:13"
            "parasha":      None,   # "Тецаве"
            "shabbat_date": None,   # datetime of Saturday
            "hebrew_date":  None,   # "10 адара 5786"
        }

        for item in data.get("items", []):
            cat = item.get("category", "")

            if cat == "candles":
                dt = datetime.fromisoformat(item["date"])
                result["candles"] = dt.strftime("%H:%M")

            elif cat == "havdalah":
                dt = datetime.fromisoformat(item["date"])
                result["havdalah"] = dt.strftime("%H:%M")
                # shabbat is the day of havdalah
                result["shabbat_date"] = dt.date() + timedelta(days=0)

            elif cat == "parashat":
                # item["title"] = "Parashat Tetzaveh" — strip prefix
                title: str = item.get("title", "")
                parasha_en = title.replace("Parashat ", "").replace("Parasha ", "").strip()
                result["parasha"] = self._translate_parasha(parasha_en)

                # Hebrew date of Shabbat
                hdate: str = item.get("hdate", "")   # e.g. "10 Adar 5786"
                result["hebrew_date"]  = self._format_hebrew_date(hdate)
                result["shabbat_date"] = datetime.strptime(item["date"], "%Y-%m-%d").date()

        return result

    def _fetch_weekend_forecast(self) -> tuple[int, int, str]:
        """
        Returns (min_temp, max_temp, description_ru) for Saturday.
        Uses WeatherClient.get_forecast() — reuses existing logic including
        current-temp correction and icon data.
        """
        from datetime import date as date_type
        today    = datetime.now().date()
        saturday = today + timedelta(days=(5 - today.weekday()) % 7 or 7)

        forecast = self.wc.get_forecast("Modiin")   # list of (date, {min,max,desc,icon})

        for f_date, f_data in forecast:
            if f_date == saturday:
                desc_ru = self._translate_weather(f_data.get("description", ""))
                return round(f_data["min_temp"]), round(f_data["max_temp"]), desc_ru

        # fallback — Saturday not in forecast (too far ahead), use first available day
        if forecast:
            _, f_data = forecast[0]
            desc_ru = self._translate_weather(f_data.get("description", ""))
            return round(f_data["min_temp"]), round(f_data["max_temp"]), desc_ru

        return 0, 0, "—"

    # ── private: formatting ───────────────────────────────────────────────────

    def _build_message(self) -> str:
        shabbat = self._fetch_shabbat_data()
        t_min, t_max, weather_desc = self._fetch_weekend_forecast()

        today = datetime.now()
        greg_date = f"{today.day} {MONTHS_RU[today.month]}"

        from HebrewCalendar import HebrewCalendar
        hebrew_date = HebrewCalendar().get_hebrew_date_short_ru()

        # Gregorian date of Saturday
        # sat = shabbat["shabbat_date"]
        # if sat:
        #     greg_date = f"{sat.day} {MONTHS_RU[sat.month]}"
        # else:
        #     tomorrow = datetime.now().date() + timedelta(days=1)
        #     greg_date = f"{tomorrow.day} {MONTHS_RU[tomorrow.month]}"

        # hebrew_date = shabbat["hebrew_date"] or ""
        parasha     = shabbat["parasha"]     or "—"
        candles     = shabbat["candles"]     or "—"
        havdalah    = shabbat["havdalah"]    or "—"

        lines = [
            f"🗓 {greg_date} • {hebrew_date}",
            "",
            f"🕍 Суббота — недельная глава {parasha}",
            "",
            f"🕯 Зажигание свечей: {candles}",
            f"🌙 Выход субботы: {havdalah}",
            "",
            f"🌤 Погода в субботу: {t_min}°–{t_max}°, {weather_desc.lower()}",
            "",
            f"✅ Будь в курсе событий Модиина!",
            f"Подписывайся 👉 {self.channel_link}",
        ]
        return "\n".join(lines)

    def _translate_parasha(self, name_en: str) -> str:
        """Transliterate parasha name to Russian (basic mapping for most common ones)."""
        table: dict[str, str] = {
            "Bereshit":      "Берешит",    "Noach":        "Ноах",
            "Lech-Lecha":    "Лех-леха",   "Vayera":       "Ваера",
            "Chayei Sara":   "Хаей Сара",  "Toldot":       "Толдот",
            "Vayetzei":      "Ваецэ",      "Vayishlach":   "Ваишлах",
            "Vayeshev":      "Ваешев",     "Miketz":       "Микец",
            "Vayigash":      "Ваигаш",     "Vayechi":      "Ваехи",
            "Shemot":        "Шмот",       "Vaera":        "Ваэра",
            "Bo":            "Бо",         "Beshalach":    "Бешалах",
            "Yitro":         "Итро",       "Mishpatim":    "Мишпатим",
            "Terumah":       "Трума",      "Tetzaveh":     "Тецаве",
            "Ki Tisa":       "Ки тиса",    "Vayakhel":     "Ваякhэль",
            "Pekudei":       "Пекудей",    "Vayakhel-Pekudei": "Ваякhэль-Пекудей",
            "Vayikra":       "Ваикра",     "Tzav":         "Цав",
            "Shmini":        "Шмини",      "Tazria":       "Тазрия",
            "Metzora":       "Мецора",     "Tazria-Metzora": "Тазрия-Мецора",
            "Achrei Mot":    "Ахарей мот", "Kedoshim":     "Кдошим",
            "Achrei Mot-Kedoshim": "Ахарей мот-Кдошим",
            "Emor":          "Эмор",       "Behar":        "Бехар",
            "Bechukotai":    "Бехукотай",  "Behar-Bechukotai": "Бехар-Бехукотай",
            "Bamidbar":      "Бамидбар",   "Nasso":        "Насо",
            "Beha'alotcha":  "Бехаалотха", "Sh'lach":      "Шлах",
            "Korach":        "Корах",      "Chukat":       "Хукат",
            "Balak":         "Балак",      "Chukat-Balak": "Хукат-Балак",
            "Pinchas":       "Пинхас",     "Matot":        "Матот",
            "Masei":         "Масей",      "Matot-Masei":  "Матот-Масей",
            "Devarim":       "Дварим",     "Vaetchanan":   "Ваэтханан",
            "Eikev":         "Экев",       "Re'eh":        "Реэ",
            "Shoftim":       "Шофтим",     "Ki Teitzei":   "Ки тецэ",
            "Ki Tavo":       "Ки таво",    "Nitzavim":     "Ницавим",
            "Vayeilech":     "Ваелех",     "Nitzavim-Vayeilech": "Ницавим-Ваелех",
            "Ha'Azinu":      "Хаазину",    "Vezot HaBerakhah": "Везот хабраха",
        }
        return table.get(name_en, name_en)

    def _translate_weather(self, desc_en: str) -> str:
        return WEATHER_DESC_RU.get(desc_en.lower(), desc_en.capitalize())

    def _format_hebrew_date(self, hdate: str) -> str:
        """Convert '10 Adar 5786' → '10 адара 5786'."""
        if not hdate:
            return ""
        parts = hdate.split()
        if len(parts) == 3:
            day, month_en, year = parts
            # handle double-word months like "Adar II"
            month_ru = HEBREW_MONTHS_RU.get(month_en, month_en.lower())
            return f"{day} {month_ru} {year}"
        if len(parts) == 4:   # e.g. "10 Adar II 5786"
            day, m1, m2, year = parts
            month_ru = HEBREW_MONTHS_RU.get(f"{m1} {m2}", f"{m1} {m2}".lower())
            return f"{day} {month_ru} {year}"
        return hdate

    # ── private: Telegram ────────────────────────────────────────────────────

    async def _send_telegram(self, text: str) -> None:
        await self.bot.send_message(
            chat_id    = self.channel_id,
            text       = text,
            parse_mode = "HTML",
        )
        logger.info("Shabbat message delivered to %s", self.channel_id)


# ── Example usage / standalone runner ────────────────────────────────────────

if __name__ == "__main__":
    import os, asyncio
    from aiogram import Bot

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    bot    = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    # wc  = WeatherClient(os.environ["OWM_API_KEY"])

    sender = ShabbatMessageSender(
        bot            = bot,
        channel_id     = os.environ["TELEGRAM_CHANNEL_ID"],
        weather_client = None,  # replace with real WeatherClient instance
    )

    # Preview without sending
    print(sender._build_message())

    # Send (uncomment to actually post)
    # asyncio.run(sender.send())