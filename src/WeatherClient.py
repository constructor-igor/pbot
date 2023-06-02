import datetime
from datetime import timezone, timedelta
import requests
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
    def get_forecast(self, location_name):
        response = requests.get(f"http://api.openweathermap.org/data/2.5/forecast?q={location_name}&units=metric&appid={self.weather_api_key}")
        data = response.json()
        if data["cod"] != "200":
            raise Exception(data["message"])
        else:
            forecast_data = data["list"]
            forecast = {}
            for forecast_item in forecast_data:
                timestamp = forecast_item["dt"]
                date = datetime.datetime.fromtimestamp(timestamp).date()
                temperature = forecast_item["main"]["temp"]
                weather_description = forecast_item["weather"][0]["description"]
                if date in forecast:
                    forecast[date]["max_temp"] = max(forecast[date]["max_temp"], temperature)
                    forecast[date]["min_temp"] = min(forecast[date]["min_temp"], temperature)
                else:
                    forecast[date] = {"max_temp": temperature, "min_temp": temperature, "description": weather_description}
            sorted_forecast = sorted(forecast.items(), key=lambda x: x[0])
            return sorted_forecast
