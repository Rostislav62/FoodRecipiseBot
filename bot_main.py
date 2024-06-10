# bot_main.py
# для корректной работы этого бота я загнузил эти пакеты
# pip install aiogram==2.21 aiohttp==3.8.1 googletrans==4.0.0-rc1

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from token_data import BOT_TOKEN
from recipes_handler import start_category_search, category_chosen, option_chosen, show_recipes, another_option, \
    RecipeStates
from token_data import HELP_MESSAGE

# Инициализация бота и диспетчера с хранилищем состояний
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


# при вводе команды /start выводится приветствие и приглашение выбрать тип блюда
@dp.message_handler(Command('start'))
async def start_command(message: types.Message, state: FSMContext):
    await message.answer('Добро пожаловать! Я Бот Рецептов!')
    await start_category_search(message, state)


# при вводе команды /start выводится инструкция по работе с ботом.
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.answer(HELP_MESSAGE)


# вызывается функция которая формирует и отправляет запрос на категорию блюда,
# принимается и обрабатывается ответ и передаётся фркус на следуюшую функцию.
@dp.callback_query_handler(state=RecipeStates.waiting_for_category)
async def category_chosen_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await category_chosen(callback_query, state)


# вызывается функция которая формирует и отправляет запрос на количество рецептов,
# принимается и обрабатывается ответ и передаётся фркус на следуюшую функцию.
@dp.callback_query_handler(state=RecipeStates.waiting_for_option)
async def option_chosen_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await option_chosen(callback_query, state)


# вызывается функция которая формирует и отправляет запрос на выбранные рецепты,
# принимается и обрабатывается ответ и передаётся фркус на следуюшую функцию.
@dp.callback_query_handler(lambda c: c.data == "show_recipe", state=RecipeStates.waiting_for_recipe)
async def show_recipe_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await show_recipes(callback_query, state)


# вызывается функция которая по сути начинает работу бота снова как будто введена команда /start
@dp.callback_query_handler(lambda c: c.data == "another_option", state=RecipeStates.waiting_for_details)
async def another_option_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await another_option(callback_query, state)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
