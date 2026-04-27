import os
from html import escape
from pathlib import Path

import httpx
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_CITY = "Tallinn"

CATEGORY_ICONS = {
    "concerts": "🎵",
    "sports": "⚽",
    "lectures-exhibitions": "🖼",
    "film": "🎬",
    "other": "✨",
}

TEXTS = {
    "ru": {
        "choose_lang": "🌐 <b>Выбери язык</b>",
        "lang_ru": "🇷🇺 Русский",
        "lang_et": "🇪🇪 Eesti",

        "home_title": "🎫 <b>Tallinn Events Bot</b>",
        "home_body": (
            "Найди, куда сходить в Таллинне:\n"
            "• концерты\n"
            "• спорт\n"
            "• выставки\n"
            "• кино\n"
            "• события рядом с тобой\n\n"
            "Выбери нужный раздел ниже."
        ),

        "about_title": "ℹ️ <b>О боте</b>",
        "about_body": (
            "Этот бот помогает находить мероприятия в Таллинне в удобном формате.\n\n"
            "<b>Что умеет:</b>\n"
            "• поиск событий рядом\n"
            "• просмотр категорий\n"
            "• просмотр событий по времени\n"
            "• карточка события с деталями\n\n"
            "<b>Источники:</b>\n"
            "• Ticketmaster\n"
            "• PredictHQ"
        ),

        "menu_nearby": "🔎 Найти рядом",
        "menu_categories": "📂 Категории",
        "menu_time": "🗓 По времени",
        "menu_about": "ℹ️ О боте",
        "menu_home": "🏠 Главное меню",
        "menu_language": "🌐 Язык",

        "time_today": "🗓 Сегодня",
        "time_week": "📅 Эта неделя",

        "menu_prompt": "Выбери действие:",
        "period_prompt": "🗓 <b>Выбор периода</b>\n\nВыбери, что показать:",
        "nearby_prompt": (
            "🔎 <b>Найти рядом</b>\n\n"
            f"📍 Локация: <b>{DEFAULT_CITY}</b>\n\n"
            "Нажми кнопку ниже и отправь геолокацию. Я покажу ближайшие события."
        ),
        "categories_title": f"📂 <b>Категории</b>\n\n📍 Локация: <b>{DEFAULT_CITY}</b>\n\nВыбери категорию:",
        "categories_empty": "Категории пока не найдены.",
        "categories_error": "Не удалось получить категории.",
        "nearby_error": "Не удалось получить события рядом.",
        "nearby_empty": "😕 Рядом пока ничего не найдено.",
        "period_error": "Не удалось получить события по периоду.",
        "period_empty": "😕 <b>На период «{period}» событий пока не найдено.</b>",
        "category_error": "Не удалось получить события по категории.",
        "category_empty": (
            "😕 <b>Ничего не найдено</b>\n\n"
            "📂 Категория: <b>{category}</b>\n"
            f"📍 Локация: <b>{DEFAULT_CITY}</b>\n\n"
            "Попробуй другую категорию."
        ),
        "event_error": "Не удалось получить детали мероприятия.",
        "use_buttons": "Используй кнопки снизу.",
        "nearby_title": "📍 <b>Ближайшие мероприятия</b>",
        "period_header": "🗓 <b>{period}</b>\n\n📍 Локация: <b>{city}</b>\n",
        "category_header": "🎫 <b>{category}</b>\n\n📍 Локация: <b>{city}</b>\n",
        "btn_send_location": "📍 Отправить геолокацию",
        "btn_back_categories": "⬅️ Назад к категориям",
        "btn_home": "🏠 Главное меню",
        "btn_categories": "📂 Категории",
        "btn_open_event": "🔗 Открыть событие",
        "btn_back_nearby": "⬅️ Назад к поиску рядом",
        "btn_back_today": "⬅️ Назад к периоду: Сегодня",
        "btn_back_week": "⬅️ Назад к периоду: Эта неделя",
        "btn_back_category": "⬅️ Назад к категории",
        "btn_time": "🗓 По времени",
        "btn_back_time": "🗓 Назад к выбору периода",
        "btn_nearby_again": "📍 Найти рядом ещё раз",
        "unknown_title": "Без названия",
        "unknown_date": "Дата не указана",
        "unknown_desc": "Описание отсутствует.",
        "details_category": "Категория",
        "details_place": "Место",
        "details_city": "Город",
        "details_address": "Адрес",
        "details_source": "Источник",
        "details_description": "Описание",
        "main_menu_label": "Меню:",
        "details_button_prefix": "Подробнее",
        "distance_km": "км",
    },
    "et": {
        "choose_lang": "🌐 <b>Vali keel</b>",
        "lang_ru": "🇷🇺 Русский",
        "lang_et": "🇪🇪 Eesti",

        "home_title": "🎫 <b>Tallinn Events Bot</b>",
        "home_body": (
            "Leia, kuhu minna Tallinnas:\n"
            "• kontserdid\n"
            "• sport\n"
            "• näitused\n"
            "• kino\n"
            "• sündmused sinu lähedal\n\n"
            "Vali sobiv jaotis allpool."
        ),

        "about_title": "ℹ️ <b>Botist</b>",
        "about_body": (
            "See bot aitab leida üritusi Tallinnas mugavas vormis.\n\n"
            "<b>Mida bot oskab:</b>\n"
            "• otsib sündmusi lähedalt\n"
            "• näitab kategooriaid\n"
            "• näitab sündmusi aja järgi\n"
            "• avab detailse sündmuse kaardi\n\n"
            "<b>Allikad:</b>\n"
            "• Ticketmaster\n"
            "• PredictHQ"
        ),

        "menu_nearby": "🔎 Otsi lähedalt",
        "menu_categories": "📂 Kategooriad",
        "menu_time": "🗓 Aja järgi",
        "menu_about": "ℹ️ Botist",
        "menu_home": "🏠 Peamenüü",
        "menu_language": "🌐 Keel",

        "time_today": "🗓 Täna",
        "time_week": "📅 See nädal",

        "menu_prompt": "Vali tegevus:",
        "period_prompt": "🗓 <b>Ajavahemiku valik</b>\n\nVali, mida näidata:",
        "nearby_prompt": (
            "🔎 <b>Otsi lähedalt</b>\n\n"
            f"📍 Asukoht: <b>{DEFAULT_CITY}</b>\n\n"
            "Vajuta allolevat nuppu ja saada geolokatsioon. Näitan lähimaid sündmusi."
        ),
        "categories_title": f"📂 <b>Kategooriad</b>\n\n📍 Asukoht: <b>{DEFAULT_CITY}</b>\n\nVali kategooria:",
        "categories_empty": "Kategooriaid ei leitud.",
        "categories_error": "Kategooriate laadimine ebaõnnestus.",
        "nearby_error": "Lähedal olevate sündmuste laadimine ebaõnnestus.",
        "nearby_empty": "😕 Läheduses ei leitud praegu midagi.",
        "period_error": "Selle ajavahemiku sündmuste laadimine ebaõnnestus.",
        "period_empty": "😕 <b>Ajaperioodil „{period}” sündmusi ei leitud.</b>",
        "category_error": "Kategooria sündmuste laadimine ebaõnnestus.",
        "category_empty": (
            "😕 <b>Midagi ei leitud</b>\n\n"
            "📂 Kategooria: <b>{category}</b>\n"
            f"📍 Asukoht: <b>{DEFAULT_CITY}</b>\n\n"
            "Proovi teist kategooriat."
        ),
        "event_error": "Sündmuse detailide laadimine ebaõnnestus.",
        "use_buttons": "Kasuta all olevaid nuppe.",
        "nearby_title": "📍 <b>Lähimad üritused</b>",
        "period_header": "🗓 <b>{period}</b>\n\n📍 Asukoht: <b>{city}</b>\n",
        "category_header": "🎫 <b>{category}</b>\n\n📍 Asukoht: <b>{city}</b>\n",
        "btn_send_location": "📍 Saada geolokatsioon",
        "btn_back_categories": "⬅️ Tagasi kategooriatesse",
        "btn_home": "🏠 Peamenüü",
        "btn_categories": "📂 Kategooriad",
        "btn_open_event": "🔗 Ava sündmus",
        "btn_back_nearby": "⬅️ Tagasi lähedal otsingusse",
        "btn_back_today": "⬅️ Tagasi perioodi juurde: Täna",
        "btn_back_week": "⬅️ Tagasi perioodi juurde: See nädal",
        "btn_back_category": "⬅️ Tagasi kategooriasse",
        "btn_time": "🗓 Aja järgi",
        "btn_back_time": "🗓 Tagasi ajavalikusse",
        "btn_nearby_again": "📍 Otsi lähedalt uuesti",
        "unknown_title": "Pealkiri puudub",
        "unknown_date": "Kuupäev puudub",
        "unknown_desc": "Kirjeldus puudub.",
        "details_category": "Kategooria",
        "details_place": "Koht",
        "details_city": "Linn",
        "details_address": "Aadress",
        "details_source": "Allikas",
        "details_description": "Kirjeldus",
        "main_menu_label": "Menüü:",
        "details_button_prefix": "Vaata",
        "distance_km": "km",
    },
}


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    return context.user_data.get("lang", "ru")


def t(key: str, lang: str) -> str:
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)


def get_user_meta(update: Update):
    user = update.effective_user
    if not user:
        return None, None
    return str(user.id), user.username


def category_label(item: dict) -> str:
    icon = CATEGORY_ICONS.get(item.get("slug"), "🎫")
    return f"{icon} {item.get('name', 'Категория')}"


def short_event_title(title: str, max_len: int = 28) -> str:
    title = title.strip()
    return title[:max_len] + "…" if len(title) > max_len else title


def build_language_reply() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇪🇪 Eesti")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери язык / Vali keel...",
    )


def build_main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("menu_categories", lang)), KeyboardButton(t("menu_nearby", lang))],
            [KeyboardButton(t("menu_time", lang)), KeyboardButton(t("menu_about", lang))],
            [KeyboardButton(t("menu_language", lang)), KeyboardButton(t("menu_home", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t("menu_prompt", lang),
    )


def build_time_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("time_today", lang)), KeyboardButton(t("time_week", lang))],
            [KeyboardButton(t("menu_home", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t("menu_prompt", lang),
    )


def build_location_reply(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("btn_send_location", lang), request_location=True)],
            [KeyboardButton(t("menu_categories", lang)), KeyboardButton(t("menu_home", lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def home_text(lang: str) -> str:
    return f"{t('home_title', lang)}\n\n{t('home_body', lang)}"


def about_text(lang: str) -> str:
    return f"{t('about_title', lang)}\n\n{t('about_body', lang)}"


def build_categories_keyboard(categories: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    pair = []

    for item in categories:
        pair.append(
            InlineKeyboardButton(
                category_label(item),
                callback_data=f"cat:{item['slug']}",
            )
        )
        if len(pair) == 2:
            rows.append(pair)
            pair = []

    if pair:
        rows.append(pair)

    rows.append([InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def build_category_results_keyboard(events: list[dict], slug: str, lang: str) -> InlineKeyboardMarkup:
    rows = []

    for event in events[:5]:
        title = event.get("title", t("unknown_title", lang))
        rows.append(
            [
                InlineKeyboardButton(
                    f"{t('details_button_prefix', lang)}: {short_event_title(title)}",
                    callback_data=f"ev:{slug}:{event['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton(t("btn_back_categories", lang), callback_data="back:categories")])
    rows.append([InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def build_nearby_results_keyboard(events: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []

    for event in events[:5]:
        title = event.get("title", t("unknown_title", lang))
        rows.append(
            [
                InlineKeyboardButton(
                    f"{t('details_button_prefix', lang)}: {short_event_title(title)}",
                    callback_data=f"ev:nearby:{event['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton(t("btn_nearby_again", lang), callback_data="menu:nearby")])
    rows.append([InlineKeyboardButton(t("btn_categories", lang), callback_data="back:categories")])
    rows.append([InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def build_period_results_keyboard(events: list[dict], period_slug: str, lang: str) -> InlineKeyboardMarkup:
    rows = []

    for event in events[:5]:
        title = event.get("title", t("unknown_title", lang))
        rows.append(
            [
                InlineKeyboardButton(
                    f"{t('details_button_prefix', lang)}: {short_event_title(title)}",
                    callback_data=f"evperiod:{period_slug}:{event['id']}",
                )
            ]
        )

    rows.append([InlineKeyboardButton(t("btn_back_time", lang), callback_data="menu:time")])
    rows.append([InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def build_event_details_keyboard(back_slug: str | None, event_url: str | None, lang: str) -> InlineKeyboardMarkup:
    rows = []

    if event_url:
        rows.append([InlineKeyboardButton(t("btn_open_event", lang), url=event_url)])

    if back_slug == "nearby":
        rows.append([InlineKeyboardButton(t("btn_back_nearby", lang), callback_data="menu:nearby")])
    elif back_slug == "today":
        rows.append([InlineKeyboardButton(t("btn_back_today", lang), callback_data="period:today")])
    elif back_slug == "week":
        rows.append([InlineKeyboardButton(t("btn_back_week", lang), callback_data="period:week")])
    elif back_slug:
        rows.append([InlineKeyboardButton(t("btn_back_category", lang), callback_data=f"cat:{back_slug}")])

    rows.append(
        [
            InlineKeyboardButton(t("btn_categories", lang), callback_data="back:categories"),
            InlineKeyboardButton(t("btn_time", lang), callback_data="menu:time"),
        ]
    )
    rows.append([InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")])
    return InlineKeyboardMarkup(rows)


def format_dt(value: str | None, lang: str) -> str:
    if not value:
        return t("unknown_date", lang)
    return value[:16].replace("T", " ")


def format_distance(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):.2f}"
    except Exception:
        return str(value)


async def backend_get(path: str, params: dict | None = None):
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.get(f"{BACKEND_BASE_URL}{path}", params=params)
        response.raise_for_status()
        return response.json()


async def backend_post(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(f"{BACKEND_BASE_URL}{path}", json=payload)
        response.raise_for_status()
        return response.json()


async def persist_user_from_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id, username = get_user_meta(update)
    if not telegram_id:
        return

    try:
        await backend_post(
            "/users/upsert",
            {
                "telegram_id": telegram_id,
                "username": username,
                "language": get_lang(context),
            },
        )
    except Exception:
        pass


async def log_user_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str, value: str | None = None):
    telegram_id, username = get_user_meta(update)
    if not telegram_id:
        return

    try:
        await backend_post(
            "/history/search",
            {
                "telegram_id": telegram_id,
                "username": username,
                "language": get_lang(context),
                "action": action,
                "value": value,
            },
        )
    except Exception:
        pass


async def send_language_choice(message):
    await message.reply_text(
        t("choose_lang", "ru") + "\n\n" + t("choose_lang", "et"),
        reply_markup=build_language_reply(),
        parse_mode="HTML",
    )


async def send_home(message, lang: str):
    await message.reply_text(
        home_text(lang),
        reply_markup=build_main_menu(lang),
        parse_mode="HTML",
    )


async def send_about(message, lang: str):
    await message.reply_text(
        about_text(lang),
        reply_markup=build_main_menu(lang),
        parse_mode="HTML",
    )


async def send_categories(message, lang: str):
    try:
        data = await backend_get("/categories")
    except Exception:
        await message.reply_text(
            t("categories_error", lang),
            reply_markup=build_main_menu(lang),
        )
        return

    if not data:
        await message.reply_text(
            t("categories_empty", lang),
            reply_markup=build_main_menu(lang),
        )
        return

    await message.reply_text(
        t("categories_title", lang),
        reply_markup=build_categories_keyboard(data, lang),
        parse_mode="HTML",
    )


async def send_time_menu(message, lang: str):
    await message.reply_text(
        t("period_prompt", lang),
        reply_markup=build_time_menu(lang),
        parse_mode="HTML",
    )


async def send_nearby_request(message, lang: str):
    await message.reply_text(
        t("nearby_prompt", lang),
        reply_markup=build_location_reply(lang),
        parse_mode="HTML",
    )


async def send_period_events(message, period_slug: str, period_title: str, lang: str):
    try:
        payload = await backend_get(f"/events/period/{period_slug}")
    except Exception:
        await message.reply_text(
            t("period_error", lang),
            reply_markup=build_main_menu(lang),
        )
        return

    events = payload.get("events", [])

    if not events:
        await message.reply_text(
            t("period_empty", lang).format(period=period_title),
            reply_markup=build_time_menu(lang),
            parse_mode="HTML",
        )
        return

    lines = [
        t("period_header", lang).format(period=period_title, city=DEFAULT_CITY),
        "",
    ]

    for index, event in enumerate(events[:5], start=1):
        title = escape(event.get("title", t("unknown_title", lang)))
        date = escape(format_dt(event.get("event_date"), lang))
        venue = escape(event.get("venue_name") or "—")
        source = escape(event.get("source") or "—")

        lines.append(
            f"<b>{index}. {title}</b>\n"
            f"📅 {date}\n"
            f"📍 {venue}\n"
            f"🌐 {source}\n"
        )

    await message.reply_text(
        "\n".join(lines),
        reply_markup=build_period_results_keyboard(events, period_slug, lang),
        parse_mode="HTML",
    )


async def send_period_events_to_query(query, period_slug: str, period_title: str, lang: str):
    try:
        payload = await backend_get(f"/events/period/{period_slug}")
    except Exception:
        await query.message.edit_text(t("period_error", lang))
        return

    events = payload.get("events", [])

    if not events:
        await query.message.edit_text(
            t("period_empty", lang).format(period=period_title),
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(t("btn_back_time", lang), callback_data="menu:time")],
                    [InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")],
                ]
            ),
            parse_mode="HTML",
        )
        return

    lines = [
        t("period_header", lang).format(period=period_title, city=DEFAULT_CITY),
        "",
    ]

    for index, event in enumerate(events[:5], start=1):
        title = escape(event.get("title", t("unknown_title", lang)))
        date = escape(format_dt(event.get("event_date"), lang))
        venue = escape(event.get("venue_name") or "—")
        source = escape(event.get("source") or "—")

        lines.append(
            f"<b>{index}. {title}</b>\n"
            f"📅 {date}\n"
            f"📍 {venue}\n"
            f"🌐 {source}\n"
        )

    await query.message.edit_text(
        "\n".join(lines),
        reply_markup=build_period_results_keyboard(events, period_slug, lang),
        parse_mode="HTML",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    telegram_id, _ = get_user_meta(update)
    if telegram_id:
        try:
            user = await backend_get(f"/users/{telegram_id}")
            saved_lang = user.get("language")
            if saved_lang in ("ru", "et"):
                context.user_data["lang"] = saved_lang
                await send_home(update.message, saved_lang)
                await persist_user_from_update(update, context)
                return
        except Exception:
            pass

    await send_language_choice(update.message)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    if text == "🇷🇺 Русский":
        context.user_data["lang"] = "ru"
        await persist_user_from_update(update, context)
        await log_user_action(update, context, "language_change", "ru")
        await send_home(update.message, "ru")
        return

    if text == "🇪🇪 Eesti":
        context.user_data["lang"] = "et"
        await persist_user_from_update(update, context)
        await log_user_action(update, context, "language_change", "et")
        await send_home(update.message, "et")
        return

    lang = get_lang(context)

    if text == t("menu_home", lang):
        await log_user_action(update, context, "open_menu", "home")
        await send_home(update.message, lang)
        return

    if text == t("menu_categories", lang):
        await log_user_action(update, context, "open_categories", None)
        await send_categories(update.message, lang)
        return

    if text == t("menu_about", lang):
        await log_user_action(update, context, "open_about", None)
        await send_about(update.message, lang)
        return

    if text == t("menu_nearby", lang):
        await log_user_action(update, context, "open_nearby", None)
        await send_nearby_request(update.message, lang)
        return

    if text == t("menu_time", lang):
        await log_user_action(update, context, "open_time", None)
        await send_time_menu(update.message, lang)
        return

    if text == t("time_today", lang):
        await log_user_action(update, context, "period", "today")
        await send_period_events(update.message, "today", t("time_today", lang), lang)
        return

    if text == t("time_week", lang):
        await log_user_action(update, context, "period", "week")
        await send_period_events(update.message, "week", t("time_week", lang), lang)
        return

    if text == t("menu_language", lang):
        await send_language_choice(update.message)
        return

    await update.message.reply_text(
        t("use_buttons", lang),
        reply_markup=build_main_menu(lang),
    )


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.location:
        return

    lang = get_lang(context)

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    await log_user_action(update, context, "nearby_location", f"{lat},{lon}")

    try:
        data = await backend_get(
            "/events/nearby",
            params={"lat": lat, "lon": lon, "radius_km": 10},
        )
    except Exception:
        await update.message.reply_text(
            t("nearby_error", lang),
            reply_markup=build_main_menu(lang),
        )
        return

    events = data.get("events", [])

    if not events:
        await update.message.reply_text(
            t("nearby_empty", lang),
            reply_markup=build_main_menu(lang),
        )
        return

    lines = [
        t("nearby_title", lang),
        "",
    ]

    for index, event in enumerate(events[:5], start=1):
        title = escape(event.get("title", t("unknown_title", lang)))
        date = escape(format_dt(event.get("event_date"), lang))
        venue = escape(event.get("venue_name") or "—")
        source = escape(event.get("source") or "—")
        distance = format_distance(event.get("distance_km"))

        lines.append(
            f"<b>{index}. {title}</b>\n"
            f"📅 {date}\n"
            f"📍 {venue}\n"
            f"🌐 {source}\n"
            f"📏 {distance} {t('distance_km', lang)}\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=build_nearby_results_keyboard(events, lang),
        parse_mode="HTML",
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = get_lang(context)
    data = query.data or ""

    if data == "menu:home":
        await query.message.edit_text(
            home_text(lang),
            parse_mode="HTML",
        )
        await query.message.reply_text(
            t("main_menu_label", lang),
            reply_markup=build_main_menu(lang),
        )
        return

    if data == "menu:nearby":
        await query.message.reply_text(
            t("nearby_prompt", lang),
            reply_markup=build_location_reply(lang),
            parse_mode="HTML",
        )
        return

    if data == "menu:time":
        await query.message.reply_text(
            t("period_prompt", lang),
            reply_markup=build_time_menu(lang),
            parse_mode="HTML",
        )
        return

    if data == "back:categories":
        try:
            categories = await backend_get("/categories")
        except Exception:
            await query.message.edit_text(t("categories_error", lang))
            return

        if not categories:
            await query.message.edit_text(t("categories_empty", lang))
            return

        await query.message.edit_text(
            t("categories_title", lang),
            reply_markup=build_categories_keyboard(categories, lang),
            parse_mode="HTML",
        )
        return

    if data == "period:today":
        await send_period_events_to_query(query, "today", t("time_today", lang), lang)
        return

    if data == "period:week":
        await send_period_events_to_query(query, "week", t("time_week", lang), lang)
        return

    if data.startswith("cat:"):
        slug = data.split(":", 1)[1]

        try:
            payload = await backend_get(f"/events/category/{slug}")
        except Exception:
            await query.message.edit_text(t("category_error", lang))
            return

        events = payload.get("events", [])
        category = payload.get("category", {})
        category_name = escape(category.get("name", "Категория"))

        if not events:
            await query.message.edit_text(
                t("category_empty", lang).format(category=category_name),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton(t("btn_back_categories", lang), callback_data="back:categories")],
                        [InlineKeyboardButton(t("btn_home", lang), callback_data="menu:home")],
                    ]
                ),
                parse_mode="HTML",
            )
            return

        lines = [
            t("category_header", lang).format(category=category_name, city=DEFAULT_CITY),
            "",
        ]

        for index, event in enumerate(events[:5], start=1):
            title = escape(event.get("title", t("unknown_title", lang)))
            date = escape(format_dt(event.get("event_date"), lang))
            venue = escape(event.get("venue_name") or "—")
            source = escape(event.get("source") or "—")

            lines.append(
                f"<b>{index}. {title}</b>\n"
                f"📅 {date}\n"
                f"📍 {venue}\n"
                f"🌐 {source}\n"
            )

        await query.message.edit_text(
            "\n".join(lines),
            reply_markup=build_category_results_keyboard(events, slug, lang),
            parse_mode="HTML",
        )
        return

    if data.startswith("evperiod:"):
        parts = data.split(":")
        if len(parts) != 3:
            return

        back_slug = parts[1]
        event_id = parts[2]

        try:
            event = await backend_get(f"/events/{event_id}")
        except Exception:
            await query.message.edit_text(t("event_error", lang))
            return

        title = escape(event.get("title", t("unknown_title", lang)))
        description = escape(event.get("description") or t("unknown_desc", lang))
        event_date = escape(format_dt(event.get("event_date"), lang))
        category_name = escape(event.get("category") or "—")
        venue_name = escape(event.get("venue_name") or "—")
        address = escape(event.get("address") or "—")
        city = escape(event.get("city") or "—")
        source = escape(event.get("source") or "—")
        event_url = event.get("url") or None

        text = (
            f"🎫 <b>{title}</b>\n\n"
            f"📅 {event_date}\n"
            f"📂 <b>{t('details_category', lang)}:</b> {category_name}\n"
            f"📍 <b>{t('details_place', lang)}:</b> {venue_name}\n"
            f"🏙️ <b>{t('details_city', lang)}:</b> {city}\n"
            f"📌 <b>{t('details_address', lang)}:</b> {address}\n"
            f"🌐 <b>{t('details_source', lang)}:</b> {source}\n\n"
            f"📝 <b>{t('details_description', lang)}:</b>\n{description}"
        )

        await query.message.edit_text(
            text,
            reply_markup=build_event_details_keyboard(back_slug, event_url, lang),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return

    if data.startswith("ev:"):
        parts = data.split(":")
        if len(parts) != 3:
            return

        back_slug = parts[1]
        event_id = parts[2]

        try:
            event = await backend_get(f"/events/{event_id}")
        except Exception:
            await query.message.edit_text(t("event_error", lang))
            return

        title = escape(event.get("title", t("unknown_title", lang)))
        description = escape(event.get("description") or t("unknown_desc", lang))
        event_date = escape(format_dt(event.get("event_date"), lang))
        category_name = escape(event.get("category") or "—")
        venue_name = escape(event.get("venue_name") or "—")
        address = escape(event.get("address") or "—")
        city = escape(event.get("city") or "—")
        source = escape(event.get("source") or "—")
        event_url = event.get("url") or None

        text = (
            f"🎫 <b>{title}</b>\n\n"
            f"📅 {event_date}\n"
            f"📂 <b>{t('details_category', lang)}:</b> {category_name}\n"
            f"📍 <b>{t('details_place', lang)}:</b> {venue_name}\n"
            f"🏙️ <b>{t('details_city', lang)}:</b> {city}\n"
            f"📌 <b>{t('details_address', lang)}:</b> {address}\n"
            f"🌐 <b>{t('details_source', lang)}:</b> {source}\n\n"
            f"📝 <b>{t('details_description', lang)}:</b>\n{description}"
        )

        await query.message.edit_text(
            text,
            reply_markup=build_event_details_keyboard(back_slug, event_url, lang),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        return


async def cmd_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await log_user_action(update, context, "command", "/categories")
    await send_categories(update.message, get_lang(context))


async def cmd_nearby(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await log_user_action(update, context, "command", "/nearby")
    await send_nearby_request(update.message, get_lang(context))


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    lang = get_lang(context)
    await log_user_action(update, context, "command", "/today")
    await send_period_events(update.message, "today", t("time_today", lang), lang)


async def cmd_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    lang = get_lang(context)
    await log_user_action(update, context, "command", "/week")
    await send_period_events(update.message, "week", t("time_week", lang), lang)


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await log_user_action(update, context, "command", "/about")
    await send_about(update.message, get_lang(context))


def main():
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("categories", cmd_categories))
    app.add_handler(CommandHandler("nearby", cmd_nearby))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("week", cmd_week))
    app.add_handler(CommandHandler("about", cmd_about))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Telegram bot started")
    app.run_polling()


if __name__ == "__main__":
    main()