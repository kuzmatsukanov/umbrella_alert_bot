import os
from threading import Thread

from weather_mailer import WeatherMailer
from dotenv import load_dotenv
load_dotenv()


def main():
    """
    Sets up and runs the weather reporting schedule.
    """
    wm = WeatherMailer(city='Tel Aviv',
                       openweathermap_api_key=os.getenv('OPENWEATHERMAP_TOKEN'),
                       bot_api_key=os.getenv('TELEGRAMBOT_TOKEN'),
                       chat_id=os.getenv('TELEGRAM_CHAT_ID_ME'))
    wm.make_schedule(report_time="08:00", alert_time="08:30")
    # Start to run the schedule
    Thread(target=wm.schedule_checker()).start()


if __name__ == '__main__':
    main()
