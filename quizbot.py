import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

# Bot token
TOKEN = "7658286578:AAF9hJ3mL-zvbYOjKCASsldRpuvZ0nl6gf4"

# Initialize bot and dispatcher
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# States for creating a quiz
class QuizStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_options = State()
    waiting_for_correct_option = State()

# Temporary storage for quiz creation
quiz_data = {}

@dp.message_handler(commands="start")
async def start_handler(message: types.Message):
    await message.reply("Assalomu alaykum! Ushbu bot orqali testlar yaratishingiz va tarqatishingiz mumkin. Test yaratishni boshlash uchun /create_quiz komandasini yuboring.")

@dp.message_handler(commands="create_quiz")
async def create_quiz_handler(message: types.Message):
    quiz_data[message.chat.id] = {"questions": []}
    await message.reply("Test uchun savollarni kiritishni boshlang. Avval birinchi savolni yuboring.")
    await QuizStates.waiting_for_question.set()

@dp.message_handler(state=QuizStates.waiting_for_question)
async def question_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["current_question"] = message.text
    await message.reply("Variantlarni kiritishni boshlang. Har bir variantni alohida yuboring. Variantlarni tugatgach, /done deb yozing.")
    await QuizStates.waiting_for_options.set()

@dp.message_handler(state=QuizStates.waiting_for_options, commands="done")
async def done_options_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if "options" not in data or len(data["options"]) < 2:
            await message.reply("Iltimos, kamida 2 ta variant kiriting.")
            return

        quiz_data[message.chat.id]["questions"].append({
            "question": data["current_question"],
            "options": data["options"],
        })
        await message.reply("To‘g‘ri javob bo‘lgan variantning raqamini yuboring (1, 2, 3...).")
        await QuizStates.waiting_for_correct_option.set()

@dp.message_handler(state=QuizStates.waiting_for_options)
async def options_handler(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if "options" not in data:
            data["options"] = []
        data["options"].append(message.text)
    await message.reply(f"Variant qo‘shildi: {message.text}")

@dp.message_handler(state=QuizStates.waiting_for_correct_option)
async def correct_option_handler(message: types.Message, state: FSMContext):
    try:
        correct_option = int(message.text) - 1
        async with state.proxy() as data:
            if correct_option < 0 or correct_option >= len(data["options"]):
                raise ValueError("Invalid option number.")

            quiz_data[message.chat.id]["questions"][-1]["correct_option"] = correct_option
        
        await message.reply("Savol saqlandi. Yangi savolni kiriting yoki testni yakunlash uchun /finish komandasini yuboring.")
        await QuizStates.waiting_for_question.set()
    except ValueError:
        await message.reply("Iltimos, to‘g‘ri raqamni kiriting.")

@dp.message_handler(commands="finish", state=QuizStates.waiting_for_question)
async def finish_handler(message: types.Message, state: FSMContext):
    questions = quiz_data.get(message.chat.id, {}).get("questions", [])
    if not questions:
        await message.reply("Hech qanday savol kiritilmagan.")
        return

    await message.reply("Test yaratildi! Endi foydalanuvchilar testni /take_quiz orqali yechishlari mumkin.")
    await state.finish()

@dp.message_handler(commands="take_quiz")
async def take_quiz_handler(message: types.Message):
    questions = quiz_data.get(message.chat.id, {}).get("questions", [])
    if not questions:
        await message.reply("Hozircha hech qanday test mavjud emas.")
        return

    for question in questions:
        options_markup = InlineKeyboardMarkup()
        for idx, option in enumerate(question["options"]):
            options_markup.add(InlineKeyboardButton(text=option, callback_data=f"quiz_{idx}"))

        await message.reply(question["question"], reply_markup=options_markup)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
