import os
# import datetime
from datetime import datetime, timedelta
import logging
import re
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ParseMode
import asyncio

from utils import bytes_to_mb
from config import configuration
from UserSetting import UserSetting
from GoogleDriveDownloader import GoogleDriveDownloader
from YoutubeDownloader import YoutubeDownloader
from WeatherClient import WeatherClient
from HebrewProcessing import HebrewProcessing
from HebrewCalendar import HebrewCalendar
from CalendarImageBuilder import CalendarImageBuilder
from ExchangeRates import ExchangeRates
from IsraelMetrologyService import IsraelMetrologyService


TAMMUZ: int = 4
AV: int = 5

# Define user states
class UserStatus(StatesGroup):
    MAIN_MENU = State()  # Main menu state
    GEMATRYA = State()  # Gematrya calculation state

log_folder_path = configuration.log_folder_path
if not os.path.exists(log_folder_path):
    os.makedirs(log_folder_path)
data_folder = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..\\data"))

# logging to console and file
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.basicConfig(level=logging.INFO, filename=os.path.join(log_folder_path, "bot.log"), format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Starting bot...")
logging.info(f"Log folder: {log_folder_path}")
logging.info(f"Data folder: {data_folder}")

bot = Bot(token=configuration.bot_api_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
user_settings = UserSetting()

def russian_month_name(month):
    month_names = [
        'Январь', 'Февраль', 'Март', 'Апрель',
        'Май', 'Июнь', 'Июль', 'Август',
        'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]
    return month_names[month - 1]

def russian_day_name(day):
    day_names = [
        'Понедельник', 'Вторник', 'Среда', 'Четверг',
        'Пятница', 'Суббота', 'Воскресенье'
    ]
    return day_names[day]

def modiin_hello_message():
    specific_date = datetime(year=2023, month=10, day=7)
    current_date = datetime.now()
    number_of_days = (current_date - specific_date).days + 1

    day_of_week = russian_day_name(current_date.weekday())
    day_of_month = current_date.day
    month = russian_month_name(current_date.month)
    year = current_date.year
    formatted_date = f'{day_of_week}, {day_of_month} {month} {year}'

    weather_client = WeatherClient(configuration.weather_api_key)
    source_location_name = user_settings.default_location
    location_name, cur_temp, sunrise_timestamp, sunset_timestamp = weather_client.get_weather(source_location_name)
    weather_message = f"Сейчас {cur_temp}C. Восход: {sunrise_timestamp}, закат: {sunset_timestamp}."

    forecast_list = weather_client.get_forecast(source_location_name)
    forecast = '\n'.join([f"{date} - {temp['min_temp']}..{temp['max_temp']} C, {temp['description']}" for date, temp in forecast_list])

    return f"Сегодня {formatted_date}. {number_of_days} день войны.\n{weather_message}\n{forecast}"


def message_log(message, custom=""):
    user = message['from']
    logging.info(f"{custom}Message from {user.id} ({user.first_name}, {user.username}): {message.text}")

def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/today"))
    keyboard.add(KeyboardButton("/calendar"))
    keyboard.add(KeyboardButton("/weather"))
    keyboard.add(KeyboardButton("/forecast"))
    keyboard.add(KeyboardButton("/beaches"))
    keyboard.add(KeyboardButton("/gematria"))
    return keyboard

def contains_hebrew_chars(text):
    pattern = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]+')  # Range of Hebrew characters
    return bool(re.search(pattern, text))

async def startup(dispatcher: Dispatcher):
    # await bot.send_message(configuration.chat_id=369737554, text='Hello', reply_markup=get_main_menu())
    # await state.finish()  # Clear any existing state
    # await UserStatus.MAIN_MENU.set()  # Set the user state to main menu
    None

async def shutdown(dispatcher: Dispatcher):
    await storage.close()
    await bot.close()

async def modiin_hello_command(message: types.Message, state: FSMContext):
     chat_id = -1001193789881
     await bot.send_message(chat_id, modiin_hello_message(), parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=["start"])
async def start_command(message: types.Message, state: FSMContext):
    message_log(message, "[start_command] ")
    await state.finish()  # Clear any existing state
    await UserStatus.MAIN_MENU.set()  # Set the user state to main menu
    await message.reply("Hi, Select command from menu", reply_markup=get_main_menu())

@dp.message_handler(commands=["today"])
async def show_date(message: types.Message):
    message_log(message, "[show_date]")
    current_date = datetime.now()
    gregorian_date = current_date.strftime("%Y-%m-%d")  # Format: YYYY-MM-DD

    hebrew_calendar = HebrewCalendar()
    # hebrew_date = hebrew_calendar.get_hebrew_date()
    hebrew_date_str = hebrew_calendar.get_hebrew_date_str()

    response = f"Gregorian date: {gregorian_date}\nHebrew date: {hebrew_date_str}"

    rates = ExchangeRates(configuration.rates_access_token)
    rates = rates.get_rate(base_currency='USD', target_currencies=['ILS', 'EUR'])
    response += f'\n1 USD = {rates["ILS"]} ILS  / 1 EUR = {rates["ILS"]/rates["EUR"]} ILS'
    # logging.info(f'1 USD = {rates["ILS"]} ILS  / {rates["EUR"]} EUR')
    # logging.info(f'1 EUR = {rates["ILS"]/rates["EUR"]} ILS')
    # response = f"Gregorian date: {gregorian_date}"
    await message.reply(response)

    today = hebrew_calendar.get_hebrew_date()
    if (today.month == TAMMUZ and today.day >=17) or (today.month == AV and today.day <= 9):
        with open(os.path.join(data_folder, "3weeks.jpg"), "rb") as photo_file:
            await message.bot.send_photo(message.chat.id, photo_file, caption="('меж теснин') - три скорбные недели с 17 тамуза до 9 ава (https://vaikra.com/)")

@dp.message_handler(commands=["calendar"])
async def show_calendar(message: types.Message):
    message_log(message, "[show_calendar]")
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    calendar_image_file = os.path.join(data_folder, "calendar.jpg")
    calendar_image_builder = CalendarImageBuilder()
    calendar_image_builder.build_calendar_image(year, month, {}, calendar_image_file)
    with open(calendar_image_file, "rb") as photo_file:
        await message.bot.send_photo(message.chat.id, photo_file, caption="Calendar")

@dp.message_handler(commands=["weather"])
async def process_weather_command(message: types.Message):
    message_log(message, "[process_weather_command] ")
    weather_client = WeatherClient(configuration.weather_api_key)
    source_location_name = user_settings.default_location
    location_name, cur_temp, sunrise_timestamp, sunset_timestamp = weather_client.get_weather(source_location_name)
    await message.reply(f"Weather in {location_name} now is {cur_temp}C\nSunrise: {sunrise_timestamp}\nSunset: {sunset_timestamp}\n\n{configuration.bot_name}")

@dp.message_handler(commands=["forecast"])
async def process_forecast_command(message: types.Message):
    message_log(message, "[process_forecast_command] ")
    weather_client = WeatherClient(configuration.weather_api_key)
    location = user_settings.default_location
    forecast_list = weather_client.get_forecast(location)
    forecast = '\n'.join([f"{date} - {temp['min_temp']}..{temp['max_temp']} degrees, {temp['description']}" for date, temp in forecast_list])
    await message.reply(f"{forecast}\n\n{configuration.bot_name}")

@dp.message_handler(commands=["beaches"])
async def process_beaches_command(message: types.Message):
    message_log(message, "[process_beaches_command] ")
    ims = IsraelMetrologyService()
    ims.dwoanload_data()
    ims.parse_data()
    beaches_status = ims.get_beaches_status()
    full_status = ""
    for beach in beaches_status:
        full_status += f"{beach.beach_name} - {beach.get_status(beach.status)}\n"
    await message.reply(full_status)

@dp.message_handler(commands=["gematria"])
async def gematrya_command(message: types.Message, state: FSMContext):
    message_log(message, "[gematrya_command] ")
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/back"))
    await message.answer("Enter the text to calculate gematrya or type /back to return to the main menu:", reply_markup=keyboard)
    await UserStatus.GEMATRYA.set()  # Set the user state to gematrya calculation

async def channel_command(message: types.Message):
    message_log(message, "[channel_command] ")
    message_text = message.text
    message_items = message_text.split()
    channel_name = ''
    channel_id = ''
    if len(message_items) > 1:
        channel_name = message_items[1]
        try:
            chat = await bot.get_chat(channel_name)
            channel_id = chat.id
            error = ''
        except Exception as e:
            error = f" -- get_chat failed for '{channel_name}' with {e}"
    await message.reply(f"channel info: name='{channel_name}', id={channel_id}{error}")

@dp.message_handler(state=UserStatus.GEMATRYA)
async def process_gematria(message: types.Message, state: FSMContext):
    message_log(message, "[process_gematria] ")
    if message.text in ('/back', 'back'):
        await message.reply("Select command in menu", reply_markup=get_main_menu())
        await UserStatus.MAIN_MENU.set()
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("/back"))
        hp = HebrewProcessing()
        await message.reply(hp.process(message.text), reply_markup=keyboard)

@dp.message_handler(state=UserStatus.MAIN_MENU)
async def main_menu_commands(message: types.Message, state: FSMContext):
    message_log(message, "[main_menu_commands] ")
    if message.text == "/modiin":
        await modiin_hello_command(message, state)
    if message.text == "/start":
        await start_command(message, state)
    if message.text == "/today":
        await show_date(message)
    elif message.text == "/calendar":
        await show_calendar(message)
    elif message.text == "/weather":
        await process_weather_command(message)
    elif message.text == "/forecast":
        await process_forecast_command(message)
    elif message.text == "/beaches":
        await process_beaches_command(message)
    elif message.text == "/gematria":
        await gematrya_command(message, state)
    elif message.text.startswith("/channel"):
        await channel_command(message)
    else:
        await process_message(message, state)

@dp.message_handler()
async def process_message(message: types.Message, state: FSMContext):
    message_log(message, custom="[process_message] ")
    if message.text == "date":
        await show_date(message)
    elif message.text.startswith("https://drive.google.com"):
        gdd = GoogleDriveDownloader()
        file_size = gdd.download(message.text, "episode.mp3")
        await message.reply(f"Downloaded {message.text} with size {bytes_to_mb(file_size)}")
    elif "youtu.be" in message.text or "youtube.com" in message.text:
        yd = YoutubeDownloader()
        file_size = yd.download(message.text, "")
        await message.reply(f"Downloaded {message.text} with size {bytes_to_mb(file_size)}")
    # elif contains_hebrew_chars(message.text):
    #     hp = HebrewProcessing()
    #     await message.reply(hp.process(message.text))
    else:
        weather_client = WeatherClient(configuration.weather_api_key)
        source_location_name = message.text
        try:
            location_name, cur_temp, sunrise_timestamp, sunset_timestamp = weather_client.get_weather(source_location_name)
            await message.reply(f"Weather in {location_name} now is {cur_temp}C\nSunrise: {sunrise_timestamp}\nSunset: {sunset_timestamp}\n\n{configuration.bot_name}")
        except Exception as e:
            logging.error(f"get_weather failed for '{source_location_name}' with {e}")
            await message.reply(f"Location '{source_location_name}' not found")

async def forward_message(message: types.Message):
    logging.info(message)
    await bot.forward_message(chat_id=configuration.chat_id, from_chat_id=message.chat.id, message_id=message.message_id)

@dp.message_handler(chat_id=-1001203517764)
async def handle_messages(message: types.Message):
    # Handle messages in the CumtaAlertsChannel and forward them to the destination channel
    await forward_message(message)

@dp.message_handler(chat_id=-1001740956434)
async def handle_messages(message: types.Message):
    # Handle messages in the CumtaAlertsChannel and forward them to the destination channel
    await forward_message(message)

@dp.message_handler(chat_id=-1001509885343)
async def handle_messages(message: types.Message):
    # Handle messages in the CumtaAlertsChannel and forward them to the destination channel
    await forward_message(message)

class SchedulerMessage():
    def __init__(self, bot):
        self.bot = bot
        self.loop = asyncio.get_event_loop()
    def add_event(self, hour, minutes, message_func):
        self.loop.create_task(self.send_scheduled_message(hour, minutes, message_func))
    async def send_scheduled_message(self, hour, minutes, message_func):
        while True:
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=minutes, second=0, microsecond=0)
            time_until_target = target_time - now
            if time_until_target.total_seconds() < 0:
                target_time += timedelta(days=1)
            await asyncio.sleep((target_time - datetime.now()).total_seconds())
            modiin_group_id = -1001193789881
            await bot.send_message(modiin_group_id, message_func(), parse_mode=ParseMode.MARKDOWN)
            logging.info("Scheduled message sent.")


def start_bot():
    scheduler_message = SchedulerMessage(bot)
    scheduler_message.add_event(hour=7, minutes=0, message_func=modiin_hello_message)
	# С помощью метода executor.start_polling опрашиваем
    # Dispatcher: ожидаем команду /start
    # executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)
    executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)

# modiin group: 1001193789881

if __name__ == "__main__":
    start_bot()