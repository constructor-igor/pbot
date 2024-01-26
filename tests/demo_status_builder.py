
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import configuration
from WeatherClient import WeatherClient
from LocationStatusImageBuilder import LocationStatusImageBuilder


if __name__ == "__main__":
    weather_client = WeatherClient(configuration.weather_api_key)
    status_builder = LocationStatusImageBuilder('Modiin', weather_client)
    status_builder.build('.\\tests\\test.png')