from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)
from openweathermap_parser import OpenweathermapParser
from weather_mailer import WeatherMailer
import json
import re
import os
from logger import logger
from dotenv import load_dotenv
load_dotenv()


class UIHandler:
    def __init__(self, openweathermap_api_key):
        self._openweathermap_api_key = openweathermap_api_key
        self.CHOOSING, self.TYPING_REPLY, self.TYPING_CHOICE = range(3)
        self.reply_keyboard = [
            ["City", "Report time", "Alert time"],
            ["Done"],
        ]
        self.markup = ReplyKeyboardMarkup(self.reply_keyboard, one_time_keyboard=True)
        self.wm = None
        self.user_data = {}
        self._chat_id = None

    def launch_mailer_bot(self):
        """Launch the WeatherMailerBot"""
        self.wm = WeatherMailer(city=self.user_data['city'],
                                openweathermap_api_key=os.getenv('OPENWEATHERMAP_TOKEN'),
                                bot_api_key=os.getenv('TELEGRAMBOT_TOKEN'),
                                chat_id=self._chat_id)
        self.wm.make_schedule(report_time=int(10), alert_time=int(10))

        # Start to run the schedule
        self.wm.start_thread()
        return

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the conversation, display any stored data and ask user for input."""
        # Set default values if there is no user settnigs
        self.user_data['city'] = context.user_data.get('city', 'London')
        self.user_data['report time'] = context.user_data.get('report time', 10)
        self.user_data['alert time'] = context.user_data.get('alert time', '08:30')

        # Start the conversation
        reply_text = \
            "👋 Welcome to our daily weather forecast bot! I will send you a weather report every morning and" \
            "remind you to bring an umbrella if needed. " \
            "Please provide your settings for the following parameters:\n" \
            f"🏙️ City: {self.user_data['city']}\n" \
            f"⏰️ Report time: {self.user_data['report time']}\n" \
            f"☂️ Umbrella alert time: {self.user_data['alert time']}\n\n" \
            "To update your settings, use the menu buttons below. If you need help, use the '/help' command."
        await update.message.reply_text(reply_text, reply_markup=self.markup)

        # Start the MailerBot
        self._chat_id = update.message.chat_id
        self.launch_mailer_bot()
        return self.CHOOSING

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Stop bot to send the wheather reports."""
        self.wm.stop_thread()
        return await self.done(update, context)

    async def regular_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Ask the user for info about the selected predefined choice."""
        text = update.message.text.lower()
        context.user_data["choice"] = text
        if context.user_data.get(text):
            reply_text = f"Enter {text} (current: {context.user_data[text]}):"
        else:
            reply_text = f"Enter {text}:"
        await update.message.reply_text(reply_text)
        return self.TYPING_REPLY

    async def received_information(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Store info provided by user and ask for the next category."""
        text = update.message.text
        category = context.user_data["choice"]
        if category == "city":
            return await self._handle_city_input(category, text, update, context)
        elif category == "report time" or category == "alert time":
            return await self._handle_time_input(category, text, update, context)

    @staticmethod
    async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display the gathered info and end the conversation."""
        if "choice" in context.user_data:
            del context.user_data["choice"]

        await update.message.reply_text(
            "🌞Good luck!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    @staticmethod
    def _is_time_format(s):
        """
        Check if s is in format between[00:00 - 23:59]
        :param s: (str)
        :return: (bool)
        """
        time_re = re.compile(r'^(([01]\d|2[0-3]):([0-5]\d)|23:59)$')
        return bool(time_re.match(s))

    async def _handle_city_input(self, category, text, update, context):
        # Check if City name is relevant
        owmparser = OpenweathermapParser(city=text, api_key=self._openweathermap_api_key)
        response = owmparser.request_openweathermap_by_city()
        response_text_dict = json.loads(response.text)
        if response_text_dict['cod'] == "401":
            logger.error(response_text_dict['message'])
            reply_text = "Sorry, technical problems"
            await update.message.reply_text(reply_text, reply_markup=self.markup)
            return self.CHOOSING
        elif response_text_dict['cod'] == "404":
            logger.error(f"Failed to find the input city: {text}")
            reply_text = "City is not found. Please try again or choose location"
            await update.message.reply_text(reply_text, reply_markup=self.markup)
            return self.CHOOSING

        # Update the user settings
        context.user_data[category] = text.lower()
        del context.user_data["choice"]

        self.user_data[category] = context.user_data[category]
        reply_text = f"Configuration:\n" \
                     f"City: {self.user_data['city']}\n" \
                     f"Report time: {self.user_data['report time']}\n" \
                     f"Alert time: {self.user_data['alert time']}"
        await update.message.reply_text(reply_text, reply_markup=self.markup)

        # Update the settings in the MailerBot
        self.wm.city = self.user_data['city']
        return self.CHOOSING

    async def _handle_time_input(self, category, text, update, context):
        if not self._is_time_format(text):
            reply_text = "Please specify the time again between 00:00 - 23:59 (e.g. 08:00)"
            await update.message.reply_text(reply_text, reply_markup=self.markup)
            return self.CHOOSING

        context.user_data[category] = text.lower()
        del context.user_data["choice"]

        self.user_data[category] = context.user_data[category]
        reply_text = f"Configuration:\n" \
                     f"City: {self.user_data['city']}\n" \
                     f"Report time: {self.user_data['report time']}\n" \
                     f"Alert time: {self.user_data['alert time']}"
        await update.message.reply_text(reply_text, reply_markup=self.markup)

        # Update the settings in the MailerBot
        self.wm.make_schedule(report_time=int(self.user_data['report time']), alert_time=self.user_data['report time'])
        return self.CHOOSING


class UIBuilder:
    def __init__(self, bot_api_key, openweathermap_api_key):
        # Get setting of converstation handler
        self.ui = UIHandler(openweathermap_api_key)

        # Create the Application and pass it your bot's token.
        self.persistence = PicklePersistence(filepath="conversationbot")
        self.application = Application.builder().token(bot_api_key).persistence(self.persistence).build()

        # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
        self.conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.ui.start)],
            states={
                self.ui.CHOOSING: [
                    MessageHandler(
                        filters.Regex("^(City|Report time|Alert time)$"), self.ui.regular_choice
                    ),
                    CommandHandler("stop", self.ui.stop),
                ],
                self.ui.TYPING_CHOICE: [
                    MessageHandler(
                        filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")), self.ui.regular_choice
                    )
                ],
                self.ui.TYPING_REPLY: [
                    MessageHandler(
                        filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                        self.ui.received_information,
                    )
                ],
            },
            fallbacks=[MessageHandler(filters.Regex("^Done$"), self.ui.done)],
            name="my_conversation",
            persistent=True,
        )
        self.application.add_handler(self.conv_handler)
        pass
