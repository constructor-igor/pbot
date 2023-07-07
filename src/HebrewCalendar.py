from pyluach import dates, hebrewcal, parshios

#
# https://pypi.org/project/pyluach/
#

class HebrewCalendar:
    def __init__(self):
        None
    def get_hebrew_date(self):
        today = dates.HebrewDate.today()
        return today
    def get_hebrew_date_str(self):
        today = self.get_hebrew_date()
        # get hebrew year from today in hebrew number
        # today_year = today.year
        today_year = today.year
        today_hebrew_year = today.hebrew_year()
        month = hebrewcal.Month(today.year, today.month)
        # curr_month = month.month_name()
        parsha_eng = parshios.getparsha_string(today, israel=True)
        parsha_heb = parshios.getparsha_string(today, israel=True, hebrew=True)

        return f"{today.day}.{today.month} {today.year} ({today.month_name()}), {today_hebrew_year}\nParsha (Israel)={parsha_eng}({parsha_heb})"
    def get_holiday(self, date=None, hebrew=True):
        if date==None:
            date = self.get_hebrew_date()
        return date.holiday(hebrew=hebrew)
