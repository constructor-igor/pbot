"""
Tests for ShabbatMessageSender
Run: python -m unittest test_shabbat_message_sender.py -v
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import unittest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ShabbatMessageSender import ShabbatMessageSender


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def make_bot() -> AsyncMock:
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    return bot


def make_weather_client() -> MagicMock:
    wc = MagicMock()
    today    = datetime.now().date()
    saturday = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
    wc.get_forecast.return_value = [
        (saturday, {
            "min_temp":    6.2,
            "max_temp":   16.4,
            "description": "few clouds",
            "icon":        "02d",
        })
    ]
    return wc


SHABBAT_DATA = {
    "candles":      "17:17",
    "havdalah":     "18:13",
    "parasha":      "Тецаве",
    "shabbat_date": date(2026, 2, 28),
    "hebrew_date":  "10 адара 5786",
}


# ── Base mixin: creates sender before each test ───────────────────────────────

class SenderMixin:
    def setUp(self):
        self.bot = make_bot()
        self.wc  = make_weather_client()
        self.sender = ShabbatMessageSender(bot = self.bot, weather_client = self.wc, channel_link   = "t.me/modiin_ru")
        # fresh copy so tests can mutate it independently
        self.shabbat_data = dict(SHABBAT_DATA)


# ── TestFormatHelpers ─────────────────────────────────────────────────────────

class TestFormatHelpers(SenderMixin, unittest.TestCase):

    def test_format_hebrew_date_standard(self):
        self.assertEqual(self.sender._format_hebrew_date("10 Adar 5786"), "10 адара 5786")

    def test_format_hebrew_date_adar_ii(self):
        self.assertEqual(self.sender._format_hebrew_date("5 Adar II 5784"), "5 адара II 5784")

    def test_format_hebrew_date_tishrei(self):
        self.assertEqual(self.sender._format_hebrew_date("1 Tishrei 5785"), "1 тишрея 5785")

    def test_format_hebrew_date_empty(self):
        self.assertEqual(self.sender._format_hebrew_date(""), "")

    def test_translate_parasha_known(self):
        self.assertEqual(self.sender._translate_parasha("Tetzaveh"),          "Тецаве")
        self.assertEqual(self.sender._translate_parasha("Ki Tisa"),           "Ки тиса")
        self.assertEqual(self.sender._translate_parasha("Vayakhel-Pekudei"), "Ваякhэль-Пекудей")

    def test_translate_parasha_unknown_passthrough(self):
        self.assertEqual(self.sender._translate_parasha("UnknownParasha"), "UnknownParasha")

    def test_translate_weather_known(self):
        self.assertEqual(self.sender._translate_weather("few clouds"), "Малооблачно")
        self.assertEqual(self.sender._translate_weather("light rain"),  "Небольшой дождь")
        self.assertEqual(self.sender._translate_weather("clear sky"),   "Ясно")

    def test_translate_weather_case_insensitive(self):
        self.assertEqual(self.sender._translate_weather("Few Clouds"), "Малооблачно")

    def test_translate_weather_unknown_capitalizes(self):
        self.assertEqual(self.sender._translate_weather("windy storm"), "Windy storm")


# ── TestFetchWeekendForecast ──────────────────────────────────────────────────

class TestFetchWeekendForecast(SenderMixin, unittest.TestCase):

    def test_returns_saturday_data(self):
        t_min, t_max, desc = self.sender._fetch_weekend_forecast()
        self.assertEqual(t_min, 6)
        self.assertEqual(t_max, 16)
        self.assertEqual(desc,  "Малооблачно")
        self.wc.get_forecast.assert_called_once_with("Modiin")

    def test_fallback_when_saturday_missing(self):
        """If Saturday not in forecast, should return first available day."""
        today = datetime.now().date()
        self.wc.get_forecast.return_value = [
            (today, {"min_temp": 10.0, "max_temp": 20.0, "description": "clear sky", "icon": "01d"})
        ]
        t_min, t_max, desc = self.sender._fetch_weekend_forecast()
        self.assertEqual(t_min, 10)
        self.assertEqual(t_max, 20)
        self.assertEqual(desc,  "Ясно")

    def test_fallback_when_forecast_empty(self):
        self.wc.get_forecast.return_value = []
        self.assertEqual(self.sender._fetch_weekend_forecast(), (0, 0, "—"))

    def test_temperatures_are_rounded(self):
        today    = datetime.now().date()
        saturday = today + timedelta(days=(5 - today.weekday()) % 7 or 7)
        self.wc.get_forecast.return_value = [
            (saturday, {"min_temp": 6.7, "max_temp": 15.3, "description": "clear sky", "icon": "01d"})
        ]
        t_min, t_max, _ = self.sender._fetch_weekend_forecast()
        self.assertEqual(t_min, 7)
        self.assertEqual(t_max, 15)


# ── TestBuildMessage ──────────────────────────────────────────────────────────

class TestBuildMessage(SenderMixin, unittest.TestCase):

    def test_message_contains_all_fields(self):
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Малооблачно")):
            msg = self.sender._build_message()

        self.assertIn("28 февраля",    msg)
        self.assertIn("10 адара 5786", msg)
        self.assertIn("Тецаве",        msg)
        self.assertIn("17:17",         msg)
        self.assertIn("18:13",         msg)
        self.assertIn("6°–16°",        msg)
        self.assertIn("малооблачно",   msg)
        self.assertIn("t.me/modiin_ru",msg)

    def test_message_structure_order(self):
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Малооблачно")):
            msg = self.sender._build_message()

        lines = msg.split("\n")
        self.assertIn("февраля", lines[0])
        parasha_idx = next(i for i, l in enumerate(lines) if "Тецаве" in l)
        candles_idx = next(i for i, l in enumerate(lines) if "17:17"  in l)
        self.assertLess(parasha_idx, candles_idx)

    def test_message_fallback_date_when_no_shabbat_date(self):
        self.shabbat_data["shabbat_date"] = None
        self.shabbat_data["parasha"]      = "Берешит"
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(10, 20, "Ясно")):
            msg = self.sender._build_message()
        self.assertIn("Берешит", msg)

    def test_missing_parasha_shows_dash(self):
        self.shabbat_data["parasha"] = None
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Ясно")):
            msg = self.sender._build_message()
        self.assertIn("—", msg)


# ── TestSendMethods ───────────────────────────────────────────────────────────

class TestSendMethods(SenderMixin, unittest.TestCase):

    def test_send_calls_bot_send_message(self):
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Малооблачно")):
            run(self.sender.send())

        self.bot.send_message.assert_called_once()
        kw = self.bot.send_message.call_args.kwargs
        self.assertEqual(kw["chat_id"],    -1001193789881)
        self.assertEqual(kw["parse_mode"], "HTML")
        self.assertIn("Тецаве", kw["text"])

    def test_send_message_text_is_string(self):
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Малооблачно")):
            run(self.sender.send())

        sent_text = self.bot.send_message.call_args.kwargs["text"]
        self.assertIsInstance(sent_text, str)
        self.assertGreater(len(sent_text), 50)

    def test_send_if_friday_sends_on_friday(self):
        friday = datetime(2026, 2, 27, 11, 0, 0)   # known Friday
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
             patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Малооблачно")), \
             patch("ShabbatMessageSender.datetime") as mock_dt:
            mock_dt.now.return_value = friday
            mock_dt.strptime         = datetime.strptime
            mock_dt.fromisoformat    = datetime.fromisoformat
            result = run(self.sender.send_if_friday())

        self.assertTrue(result)
        self.bot.send_message.assert_called_once()

    def test_send_if_friday_skips_on_other_days(self):
        thursday = datetime(2026, 2, 26, 11, 0, 0)  # known Thursday
        with patch("ShabbatMessageSender.datetime") as mock_dt:
            mock_dt.now.return_value = thursday
            result = run(self.sender.send_if_friday())

        self.assertFalse(result)
        self.bot.send_message.assert_not_called()

    def test_full_message_text(self):
        expected = (
            "🗓 28 февраля • 10 адара 5786\n"
            "\n"
            "🕍 Суббота — недельная глава Тецаве\n"
            "\n"
            "🕯 Зажигание свечей: 17:17\n"
            "🌙 Выход субботы: 18:13\n"
            "\n"
            "🌤 Погода в субботу: 6°–16°, малооблачно\n"
            "\n"
            "✅ Будь в курсе событий Модиина!\n"
            "Подписывайся 👉 t.me/modiin_ru"
        )
        with patch.object(self.sender, '_fetch_shabbat_data', return_value=self.shabbat_data), \
            patch.object(self.sender, '_fetch_weekend_forecast', return_value=(6, 16, "Малооблачно")):
            msg = self.sender._build_message()
        self.assertEqual(msg, expected)

if __name__ == "__main__":
    unittest.main(verbosity=2)