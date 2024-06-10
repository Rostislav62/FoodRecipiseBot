# recipes_handler.py
# для корректной работы этого бота я загнузил эти пакеты
# pip install aiogram==2.21 aiohttp==3.8.1 googletrans==4.0.0-rc1

import aiohttp
import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from random import choices
from googletrans import Translator
from token_data import BASE_URL
# Объект для перевода текста с помощью библиотеки googletrans.
translator = Translator()

# Функция для получения данных из API themealdb.
async def fetch_data(endpoint):
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL + endpoint) as response:
            return await response.json()

# Перечисление состояний Finite State Machine (FSM) для обработки различных этапов взаимодействия с пользователем.
class RecipeStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_option = State()
    waiting_for_recipe = State()
    waiting_for_details = State()

# Запускает процесс выбора категории блюд. Начальная функция для получения списка категорий блюд.
async def start_category_search(message: types.Message, state: FSMContext):
    data = await fetch_data('list.php?c=list')
    categories = data.get('meals', [])

    # Генерируем кнопки категорий по 5 в ряд
    # InlineKeyboardMarkup : Разметка для кнопок, которая может быть использована в сообщениях с помощью Inline-режима отправки.
    categories_keyboard = InlineKeyboardMarkup(row_width=5)
    # buttons   InlineKeyboardButton: Кнопка для использования в Inline Keyboard Markup для обработки нажатий пользователей.
    buttons = [InlineKeyboardButton(category['strCategory'], callback_data=category['strCategory']) for category in
               categories]
    categories_keyboard.add(*buttons)

    await message.answer("Выберите категорию нажав на кнопку.", reply_markup=categories_keyboard)
    await RecipeStates.waiting_for_category.set()


# Обрабатывает выбранную пользователем категорию блюд и запускает процесс выбора количества вариантов рецептов.
async def category_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    category = callback_query.data
    await state.update_data(selected_category=category)
    # InlineKeyboardMarkup : Разметка для кнопок, которая может быть использована в сообщениях с помощью Inline-режима отправки.
    options_keyboard = InlineKeyboardMarkup(row_width=5)
    options_keyboard.add(
        InlineKeyboardButton("1 вариант", callback_data="option_1"),
        InlineKeyboardButton("2 варианта", callback_data="option_2"),
        InlineKeyboardButton("3 варианта", callback_data="option_3"),
        InlineKeyboardButton("4 варианта", callback_data="option_4"),
        InlineKeyboardButton("5 вариантов", callback_data="option_5")
    )

    await callback_query.message.answer("ВВыберите количество рецептов которые хотите увидеть.",
                                        reply_markup=options_keyboard)
    await RecipeStates.waiting_for_option.set()

# Обрабатывает выбранное количество вариантов рецептов и формирует список доступных рецептов.
async def option_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    option = int(callback_query.data.split('_')[1])
    await state.update_data(num_recipes=option)
    user_data = await state.get_data()
    category = user_data['selected_category']

    data = await fetch_data(f'filter.php?c={category}')
    meals = data.get('meals', [])
    selected_meals = choices(meals, k=option)
    meal_ids = [meal['idMeal'] for meal in selected_meals]
    await state.update_data(meal_ids=meal_ids)

    meal_names = [meal['strMeal'] for meal in selected_meals]
    translated_meal_names = [translator.translate(name, src='en', dest='ru').text for name in meal_names]
    meal_names_text = "\n".join(translated_meal_names)
    # markup Объект для создания и хранения различных клавиатур (кнопок) для отправки пользователю.
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Покажи рецепт", callback_data="show_recipe"))

    await callback_query.message.answer(
        f"Как вам такой вариант:\n{meal_names_text}\n\nНажмите кнопку ниже, чтобы получить рецепт.",
        reply_markup=markup)
    await RecipeStates.waiting_for_recipe.set()


# Показывает пользователю выбранный рецепт и предоставляет кнопку для просмотра подробной информации о рецепте.
async def show_recipes(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    user_data = await state.get_data()
    meal_ids = user_data['meal_ids']
    meal_details = await asyncio.gather(*[fetch_data(f'lookup.php?i={meal_id}') for meal_id in meal_ids])

    for meal_detail in meal_details:
        meal = meal_detail['meals'][0]
        meal_name = translator.translate(meal['strMeal'], src='en', dest='ru').text
        instructions = translator.translate(meal['strInstructions'], src='en', dest='ru').text

        ingredients = []
        for i in range(1, 21):
            ingredient = meal.get(f'strIngredient{i}')
            if ingredient:
                translated_ingredient = translator.translate(ingredient, src='en', dest='ru').text
                ingredients.append(translated_ingredient)
        ingredients_text = ", ".join(ingredients)

        await callback_query.message.answer(
            f"{meal_name}\n\nРецепт:\n{instructions}\n\nИнгредиенты: {ingredients_text}")
    await callback_query.message.answer("Выберите другой вариант или начните сначала.",
                                        reply_markup=InlineKeyboardMarkup().add(
                                            InlineKeyboardButton("Выберите другой вариант",
                                                                 callback_data="another_option")))
    await RecipeStates.waiting_for_details.set()

# Обрабатывает запрос на отображение других вариантов рецептов, повторно вызывает функцию option_chosen.
async def another_option(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await start_category_search(callback_query.message, state)
