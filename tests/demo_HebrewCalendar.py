import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import HebrewCalendar as HebrewCalendar

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    hebrew_calendar = HebrewCalendar.HebrewCalendar()
    hebrew_date_str = hebrew_calendar.get_hebrew_date_str()
    logging.info(f"Hebrew date: {hebrew_date_str}")
    logging.info(f"holiday: {hebrew_calendar.get_holiday()}")
    # hebrew_year_month = hebrew_calendar.hebrew_date_string(True)
    # logging.info(f"Hebrew date: {hebrew_year_month}")
