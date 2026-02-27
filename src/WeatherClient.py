from typing import Tuple
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
        # Step 1: get current temp + icon (needed to fill in early-morning gap)
        current_resp = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={location_name}&units=metric&appid={self.weather_api_key}"
        )
        current_data = current_resp.json()
        today        = datetime.date.today()
        current_temp = current_data["main"]["temp"]
        today_icon   = current_data["weather"][0]["icon"]
        today_desc   = current_data["weather"][0]["description"]

        # Step 2: 5-day / 3-hour forecast
        # Each 3h item has temp_max/temp_min for that slot — use them for best daily range
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/forecast"
            f"?q={location_name}&units=metric&appid={self.weather_api_key}"
        )
        data = response.json()
        if data["cod"] != "200":
            raise Exception(data["message"])

        forecast = {}
        for item in data["list"]:
            date     = datetime.datetime.fromtimestamp(item["dt"]).date()
            # temp_max/temp_min per slot are more accurate than temp alone
            slot_max = item["main"].get("temp_max", item["main"]["temp"])
            slot_min = item["main"].get("temp_min", item["main"]["temp"])
            desc     = item["weather"][0]["description"]
            icon     = item["weather"][0]["icon"]
            if date in forecast:
                forecast[date]["max_temp"] = max(forecast[date]["max_temp"], slot_max)
                forecast[date]["min_temp"] = min(forecast[date]["min_temp"], slot_min)
            else:
                forecast[date] = {"max_temp": slot_max, "min_temp": slot_min,
                                  "description": desc, "icon": icon}

        # Step 3: include current actual temp in today's range
        # (at 07:00 the forecast starts from 09:00, missing the morning reading)
        if today in forecast:
            forecast[today]["min_temp"]    = min(forecast[today]["min_temp"], current_temp)
            forecast[today]["max_temp"]    = max(forecast[today]["max_temp"], current_temp)
            forecast[today]["icon"]        = today_icon
            forecast[today]["description"] = today_desc
        else:
            forecast[today] = {"max_temp": current_temp, "min_temp": current_temp,
                               "description": today_desc, "icon": today_icon}

        return sorted(forecast.items(), key=lambda x: x[0])
    
    def get_air_quality(self, lat: float = 31.8969, lon: float = 34.9838) -> Tuple[int, str, float, float]:
        """
        Returns: (aqi, label, pm2_5, pm10)
        aqi: 1=Good, 2=Fair, 3=Moderate, 4=Poor, 5=Very Poor
        """
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={self.weather_api_key}"
        )
        data = response.json()
        components = data["list"][0]["components"]
        aqi  = data["list"][0]["main"]["aqi"]
        pm25 = components["pm2_5"]
        pm10 = components["pm10"]
    
        labels: dict[int, str] = {
            1: "Отличное 🟢",
            2: "Хорошее 🟡",
            3: "Умеренное 🟠",
            4: "Плохое 🔴",
            5: "Опасное 🟣",
        }
        return aqi, labels[aqi], pm25, pm10
