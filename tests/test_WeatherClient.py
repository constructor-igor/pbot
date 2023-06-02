import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import logging

from config import configuration
import WeatherClient as WeatherClient

if __name__ == "__main__":
    location = 'Modiin'
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting test WeatherClient")
    weather_client = WeatherClient.WeatherClient(configuration.weather_api_key)
    weather = weather_client.get_weather(location)
    location_name, cur_temp, sunrise_timestamp, sunset_timestamp = weather
    logging.info(f"weather in '{location_name}' is {cur_temp} degrees, sunrise at {sunrise_timestamp}, sunset at {sunset_timestamp}")
    forecast_list = weather_client.get_forecast(location)
    for forecast in forecast_list:
        date, temp = forecast
        max_temp = temp['max_temp']
        min_temp = temp['min_temp']
        description = temp['description']
        logging.info(f"forecast in {location}: {date} - {min_temp}..{max_temp} degrees, {description}")
    logging.info("Finished test WeatherClient")
