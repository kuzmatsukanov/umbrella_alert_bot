from ui_handler import UIBuilder
import os
from dotenv import load_dotenv
load_dotenv()


def main():
    """Run the bot."""
    ui = UIBuilder(os.getenv('TELEGRAMBOT_TOKEN'))
    ui.application.run_polling()


if __name__ == '__main__':
    main()
