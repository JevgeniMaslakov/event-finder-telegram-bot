import json
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = ""

processed_updates = set()


def is_duplicate(update: Update) -> bool:
    update_id = update.update_id

    if update_id in processed_updates:
        return True

    processed_updates.add(update_id)

    # чтобы set не рос бесконечно
    if len(processed_updates) > 1000:
        processed_updates.clear()

    return False


def load_events():
    data = Path("events.json").read_text(encoding="utf-8")
    return json.loads(data)


MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📍 Найти рядом со мной"],
        ["🗂️ Выбрать категорию"],
    ],
    resize_keyboard=True,
)

CATEGORIES_MENU = ReplyKeyboardMarkup(
    [
        ["🎵 Концерты", "🎓 Лекции"],
        ["⚽ Спорт", "🛠️ Мастер-классы"],
        ["⬅️ Назад"],
    ],
    resize_keyboard=True,
)

BACK_MENU = ReplyKeyboardMarkup(
    [["🏠 Главное меню"]],
    resize_keyboard=True,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_duplicate(update):
        return

    await update.message.reply_text(
        "Добро пожаловать в Бот Местных Событий!\nВыберите, как вы хотите искать мероприятия.",
        reply_markup=MAIN_MENU,
    )


def format_events_list(events):
    lines = []
    for e in events:
        lines.append(
            f"{e['title']}\n"
            f"📍 {e['distance_km']} км   🗓️ {e['date']}\n"
            f"📌 {e['place']}\n"
            f"ℹ️ {e['description']}\n"
            f"ID: {e['id']}\n"
            "-------------------------"
        )
    return "\n\n".join(lines)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_duplicate(update):
        return

    text = (update.message.text or "").strip()

    if text == "📍 Найти рядом со мной":
        events = load_events()
        msg = "Вот мероприятия рядом с вами:\n\n" + format_events_list(events)
        await update.message.reply_text(msg, reply_markup=BACK_MENU)
        return

    if text == "🗂️ Выбрать категорию":
        await update.message.reply_text(
            "Выберите категорию мероприятия:",
            reply_markup=CATEGORIES_MENU,
        )
        return

    if text == "⬅️ Назад" or text == "🏠 Главное меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=MAIN_MENU,
        )
        return

    categories_map = {
        "🎵 Концерты": "Концерты",
        "🎓 Лекции": "Лекции",
        "⚽ Спорт": "Спорт",
        "🛠️ Мастер-классы": "Мастер-классы",
    }

    if text in categories_map:
        category = categories_map[text]
        events = [e for e in load_events() if e["category"] == category]

        if not events:
            await update.message.reply_text(
                "Пока нет событий в этой категории.",
                reply_markup=BACK_MENU,
            )
            return

        msg = "Вот мероприятия по выбранной категории:\n\n" + format_events_list(events)
        await update.message.reply_text(msg, reply_markup=BACK_MENU)
        return

    await update.message.reply_text(
        "Я не понял команду. Выберите вариант из меню.",
        reply_markup=MAIN_MENU,
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()