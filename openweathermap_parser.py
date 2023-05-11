import requests
from logger import logger


class OpenweathermapParser:
    def __init__(self, city, api_key):
        """
        Get data with a 3-day weather forecast with 3h time resolution
        :param city: str, e.g. 'Tel Aviv'
        :param api_key: str, api_key for api.openweathermap.org
        """
        self.city = city
        self._api_key = api_key
        self.weather_forecast = None
        self.weather_dict = None
        self.request_weather_data()
        self.get_weather_dict()

    def request_weather_data(self, max_attempts=10):
        """
        Requests weather data from the OpenWeatherMap API.
        :param max_attempts: int, maximum number of attempts to make the request (default=10)
        :return: dict, weather data or None
        """
        self.weather_forecast = None
        for attempt in range(1, max_attempts):
            try:
                url = 'http://api.openweathermap.org/data/2.5/forecast?q={}&appid={}&units=metric'.format(self.city,
                                                                                                          self._api_key)
                response = requests.get(url)
                self.weather_forecast = response.json()
                logger.info("Successfully fetched weather forecast on attempt {}".format(attempt))
                return
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt}: Failed to fetch weather forecast. Error message: {e}")
                continue
        logger.error("Failed to fetch weather forecast after {} attempts.".format(max_attempts))

    def get_weather_dict(self):
        """
        Extracts relevant weather data from the current weather forecast
        :return: dict, dictionary containing weather data for the first 7 time steps (3 hours each) or None.
        """
        if self.weather_forecast is None:
            return None
        weather_ts = self.weather_forecast['list'][0:7]
        self.weather_dict = {
            'temp_ts': [],
            'temp_feels_like_ts': [],
            'time_ts': [],
            'icon_ts': [],
            'main': [],
            'description': [],
            'time_sunrise': self.weather_forecast['city']['sunrise'],
            'time_sunset': self.weather_forecast['city']['sunset'],
            'city': self.weather_forecast['city']['name']
        }
        for weather in weather_ts:
            self.weather_dict['temp_ts'].append(weather['main']['temp'])
            self.weather_dict['temp_feels_like_ts'].append(weather['main']['feels_like'])
            self.weather_dict['time_ts'].append(weather['dt'])
            self.weather_dict['icon_ts'].append(weather['weather'][0]['icon'])
            self.weather_dict['main'].append(weather['weather'][0]['main'])
            self.weather_dict['description'].append(weather['weather'][0]['description'])
