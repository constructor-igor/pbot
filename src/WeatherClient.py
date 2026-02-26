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
            sunrise_time = sunrise_timestamp.strftime('%H:%M')
            sunset_time = sunset_timestamp.strftime('%H:%M')
            return location_name, cur_temp, sunrise_time, sunset_time

    def get_forecast(self, location_name):
        # Get today's true min/max from current weather endpoint.
        # OWM /forecast gives only future 3-hour steps, so early in the morning
        # today's range is incomplete. /weather has the daily temp_min/temp_max
        # which is a full-day estimate from the forecast model.
        current_resp = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={location_name}&units=metric&appid={self.weather_api_key}"
        )
        current_data = current_resp.json()
        today = datetime.date.today()
        today_min  = current_data["main"]["temp_min"]
        today_max  = current_data["main"]["temp_max"]
        today_icon = current_data["weather"][0]["icon"]
        today_desc = current_data["weather"][0]["description"]

        # Get 5-day / 3-hour forecast
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?q={location_name}&units=metric&appid={self.weather_api_key}"
        )
        data = response.json()
        if data["cod"] != "200":
            raise Exception(data["message"])

        forecast = {}
        for item in data["list"]:
            date = datetime.datetime.fromtimestamp(item["dt"]).date()
            temp = item["main"]["temp"]
            desc = item["weather"][0]["description"]
            icon = item["weather"][0]["icon"]
            if date in forecast:
                forecast[date]["max_temp"] = max(forecast[date]["max_temp"], temp)
                forecast[date]["min_temp"] = min(forecast[date]["min_temp"], temp)
            else:
                forecast[date] = {"max_temp": temp, "min_temp": temp,
                                  "description": desc, "icon": icon}

        # Override today with accurate full-day min/max from current weather model
        if today in forecast:
            forecast[today]["min_temp"]   = min(forecast[today]["min_temp"], today_min)
            forecast[today]["max_temp"]   = max(forecast[today]["max_temp"], today_max)
            forecast[today]["icon"]        = today_icon
            forecast[today]["description"] = today_desc
        else:
            forecast[today] = {"max_temp": today_max, "min_temp": today_min,
                               "description": today_desc, "icon": today_icon}

        return sorted(forecast.items(), key=lambda x: x[0])