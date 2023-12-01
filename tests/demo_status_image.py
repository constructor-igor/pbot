import sys, os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import configuration
from LocationStatusImageBuilder import LocationStatusImageBuilder
from WeatherClient import WeatherClient

def russian_day_name(day):
    day_names = [
        'Понедельник', 'Вторник', 'Среда', 'Четверг',
        'Пятница', 'Суббота', 'Воскресенье'
    ]
    return day_names[day]

def russian_ordinal(number: int):
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

# def status_image_building(location: str, temperature_now: float, sunrise_timestamp, sunset_timestamp, target_image_path: str):
#     months = {
#         'January': 'Января', 'February': 'Февраля', 'March': 'Марта', 'April': 'Апреля',
#         'May': 'Мая', 'June': 'Июня', 'July': 'Июля', 'August': 'Августа',
#         'September': 'Сентября', 'October': 'Октября', 'November': 'Ноября', 'December': 'Декабря'
#     }
#     # Get the current date
#     current_date = datetime.now()
#     current_date_str = current_date.strftime("%d %B %Y")
#     # Replace English month name with Russian
#     for eng, rus in months.items():
#         current_date_str = current_date_str.replace(eng, rus)
#     day_of_week = russian_day_name(current_date.weekday())

#     specific_date = datetime(year=2023, month=10, day=7)
#     number_of_days = (current_date - specific_date).days + 1

#     # Create a new image with white background
#     img = Image.new('RGB', (500, 300), color = (73, 109, 137))
#     img = Image.new('RGB', (550, 300), color = (83, 190, 137))

#     d = ImageDraw.Draw(img)

#     # Use a truetype font
#     fnt = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)

#     # Add text to image
#     d.text((10,10), f"{location}", font=fnt, fill=(255, 255, 100))
#     d.text((10,40), f"Сегодня {day_of_week}, {current_date_str} года, {russian_ordinal(number_of_days)} день войны", font=fnt, fill=(255, 255, 255))
#     d.text((10,70), f"Сейчас {temperature_now}°, восход: {sunrise_timestamp}, закат: {sunset_timestamp}.", font=fnt, fill=(255, 255, 255))

#     # Save the image
#     img.save(target_image_path)

if __name__ == '__main__':
    # status_image_building("Модиин", 25.0, "06:40", "16:38", "status_image.png")

    weather_client = WeatherClient(configuration.weather_api_key)
    builder = LocationStatusImageBuilder("Modiin", weather_client)
    builder.build("status_image.png")