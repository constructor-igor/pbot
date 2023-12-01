from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from WeatherClient import WeatherClient

class Localizations_Ru:
    def __init__(self) -> None:
        self.months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        self.day_names = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    def get_date(self, specific_date: datetime)->str:
        year = specific_date.year
        month = specific_date.month
        day = specific_date.day
    def get_day_of_week(self, specifica_date: datetime)->str:
        return self.day_names[specifica_date.weekday()]
    def russian_ordinal(self, number: int):
        last_digit = number % 10
        last_two_digits = number % 100

        if last_two_digits in range(11, 15):
            return str(number) + '-ый'
        elif last_digit == 1:
            return str(number) + '-ый'
        elif last_digit in range(2, 5):
            return str(number) + '-ой'
        else:
            return str(number) + '-ый'

class LocationStatusImageBuilder:
    def __init__(self, location: str, weather_client: WeatherClient):
        self.location:str = location
        self.weather_client: WeatherClient = weather_client
        self.localization = Localizations_Ru()

    def build(self, target_image_path: str):
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        day = current_date.day

        specific_date = datetime(year=2023, month=10, day=7)
        number_of_war_days = (current_date - specific_date).days + 1

        day_of_week: str = self.localization.get_day_of_week(current_date)
        date_str: str = f"{day} {self.localization.months[month-1]} {year} года"
        war_day_str: str = f"{self.localization.russian_ordinal(number_of_war_days)} день войны"

        location_name, cur_temp, sunrise_timestamp, sunset_timestamp = self.weather_client.get_weather(self.location)

        forecast_list = self.weather_client.get_forecast(self.location)
        forecast = '\n'.join([f"{date} - {temp['min_temp']}..{temp['max_temp']} C, {temp['description']}" for date, temp in forecast_list])

        # Create a new image with white background
        # img = Image.new('RGB', (500, 300), color = (73, 109, 137))
        width = 750
        height = 500
        offset = 10
        with Image.new('RGB', (width, height), color = (83, 190, 137)) as img:
            d = ImageDraw.Draw(img)

            # Use a truetype font
            fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)

            # Add text to image
            d.text((offset, 10), f"{self.location}", font=fnt, fill=(255, 255, 100))
            d.text((offset, 40), f"Сегодня {day_of_week}, {date_str}, {war_day_str}", font=fnt, fill=(255, 255, 255))
            d.text((offset, 70), f"Сейчас {cur_temp}°, восход: {sunrise_timestamp}, закат: {sunset_timestamp}.", font=fnt, fill=(255, 255, 255))
            y_pos = 100
            for forecast_item in forecast_list:
                f_date, f_temp = forecast_item
                d.text((offset, y_pos), f"{self.localization.get_day_of_week(f_date)} {f_temp['min_temp']}°..{f_temp['max_temp']}°", font=fnt, fill=(255, 255, 255))
                y_pos += 30

            d.line([(offset, height-50), (width-offset, height-50)], fill=(255, 255, 255), width=2)
            d.text((20, height-40), f"t.me/modiin_ru", font=fnt, fill=(255, 255, 255))
            # Save the image
            img.save(target_image_path)
