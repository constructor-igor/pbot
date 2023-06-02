import datetime
from datetime import timezone, timedelta
import requests
from config import configuration
#
# https://openweathermap.org/current
#

class WeatherClient():
    def __init__(self, weather_api_key):
        self.weather_api_key = weather_api_key
    def get_weather(self, location_name):
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={location_name}&units=metric&appid={self.weather_api_key}")
        data = response.json()
        if data["cod"] != 200:
            raise Exception(data["message"])
        else:
            location_name = data["name"]
            cur_temp = data["main"]["temp"]
            time_zone = data["timezone"]
            tz = timezone(timedelta(seconds=time_zone))
            sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"], tz)
            sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"], tz)
            # sunset_timestamp = f"{datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M')}"
            # sunrise_timestamp = f"{datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M')}"
            return location_name, cur_temp, sunrise_timestamp, sunset_timestamp


# import datetime
# from datetime import timezone, timedelta
# import requests

# class WeatherClient():
#     weather_api_key = "YOUR_API_KEY"

#     def __init__(self):
#         pass

#     def get_weather_forecast(self, location_name):
#         response = requests.get(f"http://api.openweathermap.org/data/2.5/forecast?q={location_name}&units=metric&appid={self.weather_api_key}")
#         data = response.json()
#         if data["cod"] != "200":
#             raise Exception(data["message"])
#         else:
#             location_name = data["city"]["name"]
#             forecast_data = data["list"][:7]  # Get the forecast for the next 7 days
#             forecast = []
#             time_zone = data["city"]["timezone"]
#             tz = timezone(timedelta(seconds=time_zone))
#             for forecast_item in forecast_data:
#                 timestamp = datetime.datetime.fromtimestamp(forecast_item["dt"], tz)
#                 temperature = forecast_item["main"]["temp"]
#                 weather = forecast_item["weather"][0]["description"]
#                 forecast.append({"timestamp": timestamp, "temperature": temperature, "weather": weather})
#             return location_name, forecast
