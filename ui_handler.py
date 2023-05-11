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
import os
from dotenv import load_dotenv
load_dotenv()
from weather_mailer import WeatherMailer

class UIHandler:
    def __init__(self):
        self.CHOOSING, self.TYPING_REPLY, self.TYPING_CHOICE = range(3)
        self.reply_keyboard = [
            ["City", "Report time", "Alert time"],
            ["Done"],
        ]
        self.markup = ReplyKeyboardMarkup(self.reply_keyboard, one_time_keyboard=True)
        pass

    def launch_mailer_bot(self):
        """Launch the WeatherMailerBot"""
        self.wm = WeatherMailer(city=self.user_data['city'],
                               openweathermap_api_key=os.getenv('OPENWEATHERMAP_TOKEN'),
                               bot_api_key=os.getenv('TELEGRAMBOT_TOKEN'),
                               chat_id=os.getenv('TELEGRAM_CHAT_ID_ME'))
        self.wm.make_schedule(report_time=int(self.user_data['report time']), alert_time=int(10))
        # Start to run the schedule
        self.wm.start_thread()
        return
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start the conversation, display any stored data and ask user for input."""
        reply_text = "👋 Hi! Please provide the following information:\n" \
                     "🏙️ City\n" \
                     "⏰️ Weather report time\n" \
                     "☂️ Umbrella alert time"
        await update.message.reply_text(reply_text, reply_markup=self.markup)

        # Start the MailerBot
        self.user_data = context.user_data
        self.launch_mailer_bot()
        return self.CHOOSING


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
        ##########
        # TODO Check if input is relevant
        # if text.isdigit():
        #     context.user_data[category] = text.lower()
        # else:
        #     reply_message = "I do not understand it. Please try to specify the time again (e.g. 08:00)"
        #     await update.message.reply_text(reply_text, reply_markup=self.markup)
        #     return self.CHOOSING
        ##########
        context.user_data[category] = text.lower()
        del context.user_data["choice"]

        reply_text = f"Configuration:\n" \
                     f"City: {context.user_data['city']}\n" \
                     f"Report time: {context.user_data['report time']}\n" \
                     f"Alert time: {context.user_data['alert time']}"
        await update.message.reply_text(reply_text, reply_markup=self.markup)

        # Update the settings in the MailerBot
        self.wm.city = context.user_data['city']
        self.wm.make_schedule(report_time=int(context.user_data['report time']), alert_time=int(10))
        return self.CHOOSING


    async def done(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Display the gathered info and end the conversation."""
        if "choice" in context.user_data:
            del context.user_data["choice"]

        await update.message.reply_text(
            "🌞Good luck!",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END


class UIBuilder:
    def __init__(self, bot_api_key):
        # Get setting of converstation handler
        self.ui = UIHandler()

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
