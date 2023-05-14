import telebot
import schedule
from threading import Thread, Event
from time import sleep
from openweathermap_parser import OpenweathermapParser
from plot_weather_graph import PlotBuilder
from logger import logger


class WeatherMailer:
    """
    Mailer of weather data via Telegram using the OpenWeatherMap API.
    """
    def __init__(self, city, lat, lon, openweathermap_api_key, bot_api_key, chat_id):
        """
        :param city: str, the name of the city for which weather data will be retrieved.
        :param openweathermap_api_key: str, The API key for the OpenWeatherMap service
        :param bot_api_key: str, The API key for the Telegram bot
        :param chat_id: The ID of the Telegram chat where weather data will be sent
        """
        self.city = city
        self.lat = lat
        self.lon = lon
        self.openweathermap_api_key = openweathermap_api_key
        self.bot = telebot.TeleBot(bot_api_key)
        self.chat_id = chat_id
        self.weather_dict = None
        self.plot_path = None
        self.scheduler = schedule.Scheduler()
        self._thread = Thread(target=self.schedule_checker)
        self._stop_flag = Event()

    def send_weather_forecast(self):
        """
        Request weather from openweathermap.org and send the report
        """
        # Get weather forecast and build plot
        owmparser = OpenweathermapParser(api_key=self.openweathermap_api_key)
        self.weather_dict = owmparser.get_weather_dict(self.lat, self.lon)

        self.plot_path = PlotBuilder(self.weather_dict).plot_weather_ts()
        with open(self.plot_path, 'rb') as f:
            self.bot.send_photo(self.chat_id, f, caption="Have a nice day!", disable_notification=True)

    def alert_umbrella(self):
        """
        Send alert if rain is going to be
        """
        try:
            if any(w in self.weather_dict['main'] for w in ["Rain", "Thunderstorm", "Drizzle"]):
                self.bot.send_message(self.chat_id,
                                      "☔️☂️Looks like it's going to rain today, don't forget to bring an umbrella!",
                                      disable_notification=False)
        except KeyError as e:
            logger.error({e})

    def make_schedule(self, report_time, alert_time):
        """
        Makes a schedule to send message
        :param report_time: str, time of weather report e.g. "08:00"
        :param alert_time: str, time of rain alert e.g. "08:30"
        """
        self.scheduler.clear()
        self.scheduler.every().day.at(report_time).do(self.send_weather_forecast)
        self.scheduler.every().day.at(alert_time).do(self.alert_umbrella)
        # self.scheduler.every(10).seconds.do(self.send_weather_forecast)
        # self.scheduler.every(10).seconds.do(self.alert_umbrella)

    def schedule_checker(self, time_step=1):
        """
        Checks the `schedule` library for pending jobs.
        """
        while not self._stop_flag.is_set():
            self.scheduler.run_pending()
            sleep(time_step)

    def start_thread(self):
        """Start thread"""
        logger.info('Starting thread')
        self._thread.start()

    def stop_thread(self):
        """Stop runnning thread"""
        if self._thread.is_alive():
            logger.info('Stopping thread')
            self._stop_flag.set()
            self._thread.join()
            return
