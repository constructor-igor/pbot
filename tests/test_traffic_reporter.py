"""
Tests for TrafficReporter
─────────────────────────
Run (unit only, no API):
    python -m unittest test_traffic_reporter.py -v

Run with real Google Maps API (requires GOOGLE_MAPS_API_KEY env var):
    GOOGLE_MAPS_API_KEY=xxx python -m unittest test_traffic_reporter.TestRealAPI -v
"""

import os
import sys
import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from TrafficReporter import TrafficReporter, ROUTES

# ── Helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def make_reporter(**kwargs) -> TrafficReporter:
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return TrafficReporter(
        bot                 = bot,
        channel_id          = -1001193789881,
        google_maps_api_key = "fake_key",
        **kwargs,
    )


# Realistic API response for N routes (Routes API flat list format)
def make_api_response(delays_sec: list[int], durations_sec: list[int]) -> list:
    """
    Build a fake Routes API computeRouteMatrix response.
    Returns a flat list — diagonal elements only (originIndex == destinationIndex).
    duration       = dur + delay  (with traffic)
    staticDuration = dur          (without traffic, baseline)
    """
    elements = []
    for i, (dur, delay) in enumerate(zip(durations_sec, delays_sec)):
        dur_traffic = max(0, dur + delay)
        elements.append({
            "originIndex":      i,
            "destinationIndex": i,
            "status":           {},                          # empty = OK (gRPC code 0)
            "duration":         f"{dur_traffic}s",
            "staticDuration":   f"{dur}s",
        })
    return elements


# ── TestDelayEmoji ────────────────────────────────────────────────────────────

class TestDelayEmoji(unittest.TestCase):

    def test_green_at_zero(self):
        self.assertEqual(TrafficReporter._delay_emoji(0),  "🟢")

    def test_green_at_5(self):
        self.assertEqual(TrafficReporter._delay_emoji(5),  "🟢")

    def test_yellow_at_6(self):
        self.assertEqual(TrafficReporter._delay_emoji(6),  "🟡")

    def test_yellow_at_15(self):
        self.assertEqual(TrafficReporter._delay_emoji(15), "🟡")

    def test_red_at_16(self):
        self.assertEqual(TrafficReporter._delay_emoji(16), "🔴")

    def test_red_at_60(self):
        self.assertEqual(TrafficReporter._delay_emoji(60), "🔴")


# ── TestBuildMessage ──────────────────────────────────────────────────────────

class TestBuildMessage(unittest.TestCase):

    def setUp(self):
        self.reporter = make_reporter()
        self.results = [
            {"label": "Модиин → Тель-Авив",  "minutes": 45, "delay_minutes": 18},
            {"label": "Модиин → Иерусалим",  "minutes": 32, "delay_minutes": 7},
            {"label": "Модиин → Реховот",    "minutes": 22, "delay_minutes": 0},
        ]

    def test_starts_with_car_emoji(self):
        msg = self.reporter._build_message(self.results)
        self.assertTrue(msg.startswith("🚗"))

    def test_contains_time(self):
        msg = self.reporter._build_message(self.results)
        now = datetime.now().strftime("%H:%M")
        self.assertIn(now, msg)

    def test_contains_all_route_labels(self):
        msg = self.reporter._build_message(self.results)
        self.assertIn("Модиин → Тель-Авив", msg)
        self.assertIn("Модиин → Иерусалим", msg)
        self.assertIn("Модиин → Реховот",   msg)

    def test_red_emoji_for_heavy_delay(self):
        msg = self.reporter._build_message(self.results)
        # Тель-Авив: delay=18 → 🔴
        lines = msg.split("\n")
        ta_line = next(l for l in lines if "Тель-Авив" in l)
        self.assertIn("🔴", ta_line)

    def test_yellow_emoji_for_moderate_delay(self):
        msg = self.reporter._build_message(self.results)
        lines = msg.split("\n")
        jer_line = next(l for l in lines if "Иерусалим" in l)
        self.assertIn("🟡", jer_line)

    def test_green_emoji_for_no_delay(self):
        msg = self.reporter._build_message(self.results)
        lines = msg.split("\n")
        rek_line = next(l for l in lines if "Реховот" in l)
        self.assertIn("🟢", rek_line)

    def test_delay_shown_as_plus_minutes(self):
        msg = self.reporter._build_message(self.results)
        self.assertIn("+18 мин", msg)
        self.assertIn("+7 мин",  msg)

    def test_no_delay_shows_norma(self):
        msg = self.reporter._build_message(self.results)
        lines = msg.split("\n")
        rek_line = next(l for l in lines if "Реховот" in l)
        self.assertIn("норма", rek_line)

    def test_travel_time_shown(self):
        msg = self.reporter._build_message(self.results)
        self.assertIn("45 мин", msg)
        self.assertIn("32 мин", msg)
        self.assertIn("22 мин", msg)

    def test_full_message_snapshot(self):
        """Snapshot test — pin exact message format."""
        fixed_time = datetime(2026, 3, 9, 8, 0, 0)
        with patch("TrafficReporter.datetime") as mock_dt:
            mock_dt.now.return_value = fixed_time
            msg = self.reporter._build_message(self.results)

        lines = msg.split("\n")
        self.assertEqual(lines[0], "🚗 Пробки сейчас (08:00)")
        self.assertEqual(lines[1], "")
        self.assertIn("Модиин → Тель-Авив",  lines[2])
        self.assertIn("45 мин",              lines[2])
        self.assertIn("🔴",                  lines[2])
        self.assertIn("+18 мин",             lines[2])
        self.assertIn("Модиин → Иерусалим",  lines[3])
        self.assertIn("🟡",                  lines[3])
        self.assertIn("Модиин → Реховот",    lines[4])
        self.assertIn("🟢",                  lines[4])
        self.assertIn("норма",               lines[4])


# ── TestFetchAllRoutes ────────────────────────────────────────────────────────

class TestFetchAllRoutes(unittest.TestCase):

    def setUp(self):
        self.reporter = make_reporter()

    def test_parses_three_routes(self):
        api_resp = make_api_response(
            delays_sec    = [18*60, 7*60, 0],
            durations_sec = [27*60, 25*60, 20*60],
        )
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = api_resp
            mock_post.return_value.raise_for_status   = MagicMock()
            results = self.reporter._fetch_all_routes()

        self.assertEqual(len(results), 3)

    def test_correct_minutes_calculated(self):
        api_resp = make_api_response(
            delays_sec    = [18*60, 7*60, 0],
            durations_sec = [27*60, 25*60, 20*60],
        )
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = api_resp
            mock_post.return_value.raise_for_status   = MagicMock()
            results = self.reporter._fetch_all_routes()

        # duration_in_traffic = duration + delay
        self.assertEqual(results[0]["minutes"],       27 + 18)   # 45
        self.assertEqual(results[1]["minutes"],       25 + 7)    # 32
        self.assertEqual(results[2]["minutes"],       20)

    def test_correct_delay_calculated(self):
        api_resp = make_api_response(
            delays_sec    = [18*60, 7*60, 3*60],
            durations_sec = [27*60, 25*60, 20*60],
        )
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = api_resp
            mock_post.return_value.raise_for_status   = MagicMock()
            results = self.reporter._fetch_all_routes()

        self.assertEqual(results[0]["delay_minutes"], 18)
        self.assertEqual(results[1]["delay_minutes"], 7)
        self.assertEqual(results[2]["delay_minutes"], 3)

    def test_returns_empty_on_api_error(self):
        # Routes API returns non-list on auth error (e.g. {"error": {...}})
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = {"error": {"status": "PERMISSION_DENIED"}}
            mock_post.return_value.raise_for_status   = MagicMock()
            results = self.reporter._fetch_all_routes()

        self.assertEqual(results, [])

    def test_negative_delay_clamped_to_zero(self):
        """If traffic is faster than baseline, delay should be 0, not negative."""
        api_resp = make_api_response(
            delays_sec    = [-5*60, 0, 0],   # faster than normal
            durations_sec = [27*60, 25*60, 20*60],
        )
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = api_resp
            mock_post.return_value.raise_for_status   = MagicMock()
            results = self.reporter._fetch_all_routes()

        self.assertGreaterEqual(results[0]["delay_minutes"], 0)

    def test_single_api_call_for_all_routes(self):
        """All routes must be fetched in ONE API call to save quota."""
        api_resp = make_api_response([0, 0, 0], [20*60, 25*60, 15*60])
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = api_resp
            mock_post.return_value.raise_for_status   = MagicMock()
            self.reporter._fetch_all_routes()

        self.assertEqual(mock_post.call_count, 1)

    def test_all_three_route_labels_present(self):
        api_resp = make_api_response([0, 0, 0], [20*60, 25*60, 15*60])
        with patch("TrafficReporter.requests.post") as mock_post:
            mock_post.return_value.json.return_value = api_resp
            mock_post.return_value.raise_for_status   = MagicMock()
            results = self.reporter._fetch_all_routes()

        labels = [r["label"] for r in results]
        self.assertIn("Модиин → Тель-Авив",  labels)
        self.assertIn("Модиин → Иерусалим",  labels)
        self.assertIn("Модиин → Реховот",    labels)


# ── TestSendLogic ─────────────────────────────────────────────────────────────

class TestSendLogic(unittest.TestCase):

    def setUp(self):
        self.reporter = make_reporter()

    def _patch_fetch(self, results):
        return patch.object(self.reporter, "_fetch_all_routes", return_value=results)

    def test_sends_when_delay_above_threshold(self):
        results = [
            {"label": "Модиин → Тель-Авив",  "minutes": 45, "delay_minutes": 20},
            {"label": "Модиин → Иерусалим",  "minutes": 32, "delay_minutes": 5},
            {"label": "Модиин → Реховот",    "minutes": 22, "delay_minutes": 2},
        ]
        with self._patch_fetch(results):
            sent = run(self.reporter.send())
        self.assertTrue(sent)
        self.reporter.bot.send_message.assert_called_once()

    def test_silent_when_all_delays_below_threshold(self):
        results = [
            {"label": "Модиин → Тель-Авив",  "minutes": 30, "delay_minutes": 5},
            {"label": "Модиин → Иерусалим",  "minutes": 25, "delay_minutes": 3},
            {"label": "Модиин → Реховот",    "minutes": 20, "delay_minutes": 0},
        ]
        with self._patch_fetch(results):
            sent = run(self.reporter.send())
        self.assertFalse(sent)
        self.reporter.bot.send_message.assert_not_called()

    def test_silent_on_friday(self):
        friday = datetime(2026, 3, 6, 8, 0)
        with patch("TrafficReporter.datetime") as mock_dt, self._patch_fetch([]):
            mock_dt.now.return_value = friday
            sent = run(self.reporter.send())
        self.assertFalse(sent)
        self.reporter.bot.send_message.assert_not_called()

    def test_silent_on_saturday(self):
        saturday = datetime(2026, 3, 7, 8, 0)
        with patch("TrafficReporter.datetime") as mock_dt, self._patch_fetch([]):
            mock_dt.now.return_value = saturday
            sent = run(self.reporter.send())
        self.assertFalse(sent)

    def test_sends_on_sunday(self):
        sunday = datetime(2026, 3, 8, 8, 0)   # weekday()=6
        results = [{"label": "Модиин → Тель-Авив", "minutes": 50, "delay_minutes": 25}]
        with patch("TrafficReporter.datetime") as mock_dt, self._patch_fetch(results):
            mock_dt.now.return_value = sunday   # sunday.weekday() == 6, not in (4,5)
            sent = run(self.reporter.send())
        self.assertTrue(sent)

    def test_silent_when_no_data(self):
        with self._patch_fetch([]):
            sent = run(self.reporter.send())
        self.assertFalse(sent)
        self.reporter.bot.send_message.assert_not_called()

    def test_send_uses_correct_channel_id(self):
        results = [{"label": "Модиин → Тель-Авив", "minutes": 50, "delay_minutes": 20}]
        with self._patch_fetch(results):
            run(self.reporter.send())
        call_kwargs = self.reporter.bot.send_message.call_args.kwargs
        self.assertEqual(call_kwargs["chat_id"], -1001193789881)

    def test_exact_threshold_boundary(self):
        """Delay == MIN_DELAY_MINUTES should send (threshold is inclusive)."""
        results = [{"label": "Модиин → Тель-Авив", "minutes": 40,
                    "delay_minutes": self.reporter.MIN_DELAY_MINUTES}]
        with self._patch_fetch(results):
            sent = run(self.reporter.send())
        self.assertTrue(sent)

    def test_one_below_threshold_silent(self):
        """Delay == MIN_DELAY_MINUTES - 1 should NOT send."""
        results = [{"label": "Модиин → Тель-Авив", "minutes": 40,
                    "delay_minutes": self.reporter.MIN_DELAY_MINUTES - 1}]
        with self._patch_fetch(results):
            sent = run(self.reporter.send())
        self.assertFalse(sent)


# ── TestRealAPI ───────────────────────────────────────────────────────────────

@unittest.skipUnless(
    os.environ.get("GOOGLE_MAPS_API_KEY"),
    "Set GOOGLE_MAPS_API_KEY env var to run real API tests"
)
class TestRealAPI(unittest.TestCase):
    """
    Integration tests — hit the real Google Maps API.
    Run with: GOOGLE_MAPS_API_KEY=xxx python -m unittest test_traffic_reporter.TestRealAPI -v
    """

    def setUp(self):
        self.reporter = TrafficReporter(
            bot                 = AsyncMock(),
            channel_id          = -1,
            google_maps_api_key = os.environ["GOOGLE_MAPS_API_KEY"],
        )

    def test_real_api_returns_three_routes(self):
        results = self.reporter._fetch_all_routes()
        self.assertEqual(len(results), 3, f"Expected 3 routes, got: {results}")

    def test_real_api_labels_match(self):
        results = self.reporter._fetch_all_routes()
        labels = [r["label"] for r in results]
        self.assertIn("Модиин → Тель-Авив",  labels)
        self.assertIn("Модиин → Иерусалим",  labels)
        self.assertIn("Модиин → Реховот",    labels)

    def test_real_api_minutes_are_realistic(self):
        results = self.reporter._fetch_all_routes()
        for r in results:
            # Modiin to any of these cities should take 15–120 min
            self.assertGreater(r["minutes"], 15,
                f"{r['label']}: {r['minutes']} мин кажется слишком мало")
            self.assertLess(r["minutes"], 120,
                f"{r['label']}: {r['minutes']} мин кажется слишком много")

    def test_real_api_delay_not_negative(self):
        results = self.reporter._fetch_all_routes()
        for r in results:
            self.assertGreaterEqual(r["delay_minutes"], 0,
                f"{r['label']}: delay отрицательный = {r['delay_minutes']}")

    def test_real_message_text_is_valid(self):
        results = self.reporter._fetch_all_routes()
        msg = self.reporter._build_message(results)

        print("\n── Реальное сообщение о пробках ──")
        print(msg)
        print("─" * 40)

        self.assertTrue(msg.startswith("🚗"))
        self.assertIn("Модиин → Тель-Авив",  msg)
        self.assertIn("Модиин → Иерусалим",  msg)
        self.assertIn("Модиин → Реховот",    msg)
        self.assertIn("мин",                 msg)
        # Each line must contain exactly one traffic emoji
        route_lines = [l for l in msg.split("\n") if "Модиин" in l]
        self.assertEqual(len(route_lines), 3)
        for line in route_lines:
            has_emoji = any(e in line for e in ("🟢", "🟡", "🔴"))
            self.assertTrue(has_emoji, f"No traffic emoji in line: {line!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
