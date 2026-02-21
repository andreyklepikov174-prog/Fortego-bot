"""
Бот Фортего — Колесо целостности
Телеграм бот для программы самопознания и заботы о себе
"""

import logging
import sqlite3
import json
from datetime import datetime, time
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ── Настройки ──────────────────────────────────────────────────────────────────
BOT_TOKEN = "8306551070:AAGx-AwWZ-tJXs2V3rAQrL0bBsy4hgNOeBs"
ADMIN_CHAT_ID = 270143690  # Admin Telegram ID

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Состояния диалога ──────────────────────────────────────────────────────────
(
    DIAGNOSIS_BODY_1, DIAGNOSIS_BODY_2, DIAGNOSIS_BODY_3,
    DIAGNOSIS_BODY_4, DIAGNOSIS_BODY_5, DIAGNOSIS_BODY_6,
    DIAGNOSIS_BODY_SCORE,
    DIAGNOSIS_MIND_1, DIAGNOSIS_MIND_2, DIAGNOSIS_MIND_3,
    DIAGNOSIS_MIND_4, DIAGNOSIS_MIND_5, DIAGNOSIS_MIND_6,
    DIAGNOSIS_MIND_SCORE,
    DIAGNOSIS_SPIRIT_1, DIAGNOSIS_SPIRIT_2, DIAGNOSIS_SPIRIT_3,
    DIAGNOSIS_SPIRIT_4, DIAGNOSIS_SPIRIT_5, DIAGNOSIS_SPIRIT_6,
    DIAGNOSIS_SPIRIT_SCORE,
    DIAGNOSIS_WORLD_1, DIAGNOSIS_WORLD_2, DIAGNOSIS_WORLD_3,
    DIAGNOSIS_WORLD_4, DIAGNOSIS_WORLD_5, DIAGNOSIS_WORLD_6,
    DIAGNOSIS_WORLD_SCORE,
    DIAGNOSIS_FINAL,
    WEEKLY_REFLECTION,
) = range(30)

# ── Вопросы диагностики ────────────────────────────────────────────────────────
DIAGNOSIS = {
    "body": {
        "title": "🏃 ТЕЛО",
        "subtitle": "Биомеханика и биохимия",
        "questions": [
            "Твоё тело двигается достаточно в течение дня — или больше находится в статике?",
            "Ты уделяешь движению хотя бы 1 час в день?",
            "Ты просыпаешься с ощущением что тело отдохнуло?",
            "Как ты питаешься? Еда даёт тебе энергию — или забирает её?",
            "Есть ли у тебя ощущение что тело «работает» — или что-то постоянно тянет, болит, не так?",
            "Когда ты последний раз чувствовал себя действительно физически хорошо?",
        ],
        "score_question": "Оцени свой аспект ТЕЛО от 1 до 10.\n\n1 — совсем не забочусь\n10 — полностью в порядке",
        "emoji": "🏃"
    },
    "mind": {
        "title": "🧠 РАЗУМ",
        "subtitle": "Психика, мышление, информация",
        "questions": [
            "О чём ты думаешь в течение дня? Какой характер у этих мыслей?",
            "Какую информацию ты потребляешь — позитивную, негативную, или полезную?",
            "В течение дня у тебя есть ощущение ясности — или голова перегружена и мысли размытые?",
            "Ты контролируешь какую информацию впускаешь в себя — или она течёт неуправляемо?",
            "После общения или потребления контента ты чаще чувствуешь себя наполненным или опустошённым?",
            "Твои мысли в основном служат тебе — или работают против тебя?",
        ],
        "score_question": "Оцени свой аспект РАЗУМ от 1 до 10.\n\n1 — полный хаос в голове\n10 — ясность и фокус",
        "emoji": "🧠"
    },
    "spirit": {
        "title": "✨ ДУХ",
        "subtitle": "Истинное Я, смысл, жизненная энергия",
        "questions": [
            "Есть ли в твоей жизни что-то что даёт ощущение смысла — не пользы, а именно смысла?",
            "Слышишь ли ты своё сердце? Когда ты последний раз к нему прислушивался?",
            "Помнишь ли ты кто ты на самом деле — за пределами ролей и обязанностей?",
            "Бывают ли моменты когда ты чувствуешь себя собой — полностью, без масок?",
            "Ты доверяешь своей интуиции — или чаще игнорируешь её?",
            "Есть ли в твоей жизни тишина — физическая или внутренняя?",
        ],
        "score_question": "Оцени свой аспект ДУХ от 1 до 10.\n\n1 — полная потеря себя\n10 — живу в полном контакте с собой",
        "emoji": "✨"
    },
    "world": {
        "title": "🌍 МИР",
        "subtitle": "Среда, люди, пространство, природа",
        "questions": [
            "Нравится ли тебе всё что тебя окружает — дома, на работе, в жизни?",
            "Кайфуешь ли ты от того что вокруг — или что-то постоянно раздражает?",
            "Пространство где ты живёшь и работаешь даёт тебе энергию или забирает?",
            "Люди вокруг тебя в основном наполняют тебя или истощают?",
            "Ты бываешь на природе, на свежем воздухе, на солнце — достаточно для себя?",
            "Есть ли в твоей жизни порядок во внешнем мире — или хаос снаружи создаёт хаос внутри?",
        ],
        "score_question": "Оцени свой аспект МИР от 1 до 10.\n\n1 — среда полностью истощает\n10 — окружение питает и вдохновляет",
        "emoji": "🌍"
    }
}

# ── Практики по аспектам ───────────────────────────────────────────────────────
PRACTICES = {
    "body": [
        "Сегодня пройди пешком хотя бы 20 минут — без телефона, просто чувствуй как движется тело.",
        "Выпей сегодня 8 стаканов воды. Просто воды. Замечай как меняется самочувствие.",
        "Сделай 10 минут растяжки перед сном. Почувствуй каждую часть тела.",
        "Сегодня съешь один приём пищи очень осознанно — медленно, без экрана, наслаждаясь едой.",
        "Ляг спать на 1 час раньше обычного. Подари телу дополнительный отдых.",
    ],
    "mind": [
        "Сегодня 1 час без социальных сетей и новостей. Замечай что происходит внутри.",
        "Запиши 3 мысли которые чаще всего приходят к тебе. Они тебе помогают или мешают?",
        "Прочитай что-то что вдохновляет — 15 минут книги или статьи которая питает.",
        "Сделай список из 5 вещей за которые ты благодарен прямо сейчас.",
        "Проведи 10 минут в полной тишине — без музыки, без подкастов. Просто мысли.",
    ],
    "spirit": [
        "Найди сегодня 10 минут тишины. Просто сиди и ничего не делай. Замечай что приходит.",
        "Напиши ответ на вопрос: что для меня действительно важно в жизни? Без фильтров.",
        "Сделай сегодня что-то что давно хотел но откладывал — пусть маленькое.",
        "Вспомни момент когда ты чувствовал себя по-настоящему живым. Что это было?",
        "Прогуляйся в одиночестве и позволь мыслям течь свободно — без цели и маршрута.",
    ],
    "world": [
        "Приведи в порядок одно пространство вокруг тебя — стол, комнату, телефон. Замечай как меняется ощущение.",
        "Проведи хотя бы 20 минут на природе сегодня. Просто побудь в ней.",
        "Позвони или напиши человеку который тебя наполняет — просто так, без повода.",
        "Убери из окружения одну вещь которая раздражает или давит. Пусть маленькую.",
        "Сделай что-то приятное для своего пространства — цветок, свеча, уборка, перестановка.",
    ]
}

SCORE_KEYBOARD = ReplyKeyboardMarkup(
    [["1", "2", "3", "4", "5"], ["6", "7", "8", "9", "10"]],
    resize_keyboard=True, one_time_keyboard=True
)

# ── База данных ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT,
            diagnosis_done INTEGER DEFAULT 0,
            body_score INTEGER DEFAULT 0,
            mind_score INTEGER DEFAULT 0,
            spirit_score INTEGER DEFAULT 0,
            world_score INTEGER DEFAULT 0,
            weak_aspect TEXT DEFAULT '',
            week_number INTEGER DEFAULT 1
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            aspect TEXT,
            question TEXT,
            answer TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reflections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            week_number INTEGER,
            reflection TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user(user_id, username, first_name):
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, first_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_answer(user_id, aspect, question, answer):
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO answers (user_id, aspect, question, answer, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, aspect, question, answer, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_scores(user_id, body, mind, spirit, world):
    scores = {"body": body, "mind": mind, "spirit": spirit, "world": world}
    weak = min(scores, key=scores.get)
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("""
        UPDATE users SET
            body_score=?, mind_score=?, spirit_score=?, world_score=?,
            weak_aspect=?, diagnosis_done=1
        WHERE user_id=?
    """, (body, mind, spirit, world, weak, user_id))
    conn.commit()
    conn.close()
    return weak

def get_user(user_id):
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def get_all_users():
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, body_score, mind_score, spirit_score, world_score, weak_aspect, week_number FROM users WHERE diagnosis_done=1")
    rows = c.fetchall()
    conn.close()
    return rows

def save_reflection(user_id, week_number, text):
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO reflections (user_id, week_number, reflection, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, week_number, text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def increment_week(user_id):
    conn = sqlite3.connect("fortego.db")
    c = conn.cursor()
    c.execute("UPDATE users SET week_number = week_number + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

# ── Визуализация колеса ────────────────────────────────────────────────────────
def draw_wheel(body, mind, spirit, world):
    def bar(score):
        filled = int(score)
        return "█" * filled + "░" * (10 - filled)

    return (
        f"🎡 *Твоё Колесо Фортего*\n\n"
        f"🏃 Тело   {bar(body)} {body}/10\n"
        f"🧠 Разум  {bar(mind)} {mind}/10\n"
        f"✨ Дух    {bar(spirit)} {spirit}/10\n"
        f"🌍 Мир    {bar(world)} {world}/10\n"
    )

def get_weak_label(aspect):
    labels = {"body": "ТЕЛО 🏃", "mind": "РАЗУМ 🧠", "spirit": "ДУХ ✨", "world": "МИР 🌍"}
    return labels.get(aspect, aspect)

# ── Хендлеры ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username or "", user.first_name or "")

    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n\n"
        "Добро пожаловать в *Фортего* — пространство где ты учишься заботиться о себе целостно.\n\n"
        "Мы верим что хорошее самочувствие — это не случайность. Это результат внимания к четырём аспектам себя:\n\n"
        "🏃 *Тело* — движение и питание\n"
        "🧠 *Разум* — мысли и информация\n"
        "✨ *Дух* — смысл и истинное Я\n"
        "🌍 *Мир* — среда, люди, природа\n\n"
        "Когда все четыре в порядке — начинается синергия. Вещи налаживаются там где ты не ожидаешь.\n\n"
        "Начнём с диагностики — узнаем где ты сейчас. Это займёт около 10 минут.\n\n"
        "Готов?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["Да, начнём! 🚀"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return DIAGNOSIS_BODY_1

# ── ТЕЛО ──────────────────────────────────────────────────────────────────────
async def diag_body_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = DIAGNOSIS["body"]
    await update.message.reply_text(
        f"*{q['title']}*\n_{q['subtitle']}_\n\n"
        "Отвечай честно — здесь нет правильных ответов, только твоё наблюдение за собой.\n\n"
        f"1️⃣ {q['questions'][0]}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return DIAGNOSIS_BODY_2

async def diag_body_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "body", DIAGNOSIS["body"]["questions"][0], update.message.text)
    await update.message.reply_text(f"2️⃣ {DIAGNOSIS['body']['questions'][1]}")
    return DIAGNOSIS_BODY_3

async def diag_body_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "body", DIAGNOSIS["body"]["questions"][1], update.message.text)
    await update.message.reply_text(f"3️⃣ {DIAGNOSIS['body']['questions'][2]}")
    return DIAGNOSIS_BODY_4

async def diag_body_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "body", DIAGNOSIS["body"]["questions"][2], update.message.text)
    await update.message.reply_text(f"4️⃣ {DIAGNOSIS['body']['questions'][3]}")
    return DIAGNOSIS_BODY_5

async def diag_body_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "body", DIAGNOSIS["body"]["questions"][3], update.message.text)
    await update.message.reply_text(f"5️⃣ {DIAGNOSIS['body']['questions'][4]}")
    return DIAGNOSIS_BODY_6

async def diag_body_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "body", DIAGNOSIS["body"]["questions"][4], update.message.text)
    await update.message.reply_text(f"6️⃣ {DIAGNOSIS['body']['questions'][5]}")
    return DIAGNOSIS_BODY_SCORE

async def diag_body_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "body", DIAGNOSIS["body"]["questions"][5], update.message.text)
    await update.message.reply_text(
        f"Хорошо. Теперь — итоговая оценка.\n\n{DIAGNOSIS['body']['score_question']}",
        reply_markup=SCORE_KEYBOARD
    )
    return DIAGNOSIS_MIND_1

# ── РАЗУМ ─────────────────────────────────────────────────────────────────────
async def diag_mind_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = int(update.message.text)
        context.user_data["body_score"] = score
    except ValueError:
        await update.message.reply_text("Пожалуйста, выбери число от 1 до 10", reply_markup=SCORE_KEYBOARD)
        return DIAGNOSIS_MIND_1

    q = DIAGNOSIS["mind"]
    await update.message.reply_text(
        f"Тело — записано ✓\n\n*{q['title']}*\n_{q['subtitle']}_\n\n"
        f"1️⃣ {q['questions'][0]}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return DIAGNOSIS_MIND_2

async def diag_mind_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "mind", DIAGNOSIS["mind"]["questions"][0], update.message.text)
    await update.message.reply_text(f"2️⃣ {DIAGNOSIS['mind']['questions'][1]}")
    return DIAGNOSIS_MIND_3

async def diag_mind_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "mind", DIAGNOSIS["mind"]["questions"][1], update.message.text)
    await update.message.reply_text(f"3️⃣ {DIAGNOSIS['mind']['questions'][2]}")
    return DIAGNOSIS_MIND_4

async def diag_mind_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "mind", DIAGNOSIS["mind"]["questions"][2], update.message.text)
    await update.message.reply_text(f"4️⃣ {DIAGNOSIS['mind']['questions'][3]}")
    return DIAGNOSIS_MIND_5

async def diag_mind_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "mind", DIAGNOSIS["mind"]["questions"][3], update.message.text)
    await update.message.reply_text(f"5️⃣ {DIAGNOSIS['mind']['questions'][4]}")
    return DIAGNOSIS_MIND_6

async def diag_mind_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "mind", DIAGNOSIS["mind"]["questions"][4], update.message.text)
    await update.message.reply_text(f"6️⃣ {DIAGNOSIS['mind']['questions'][5]}")
    return DIAGNOSIS_MIND_SCORE

async def diag_mind_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "mind", DIAGNOSIS["mind"]["questions"][5], update.message.text)
    await update.message.reply_text(
        f"Хорошо.\n\n{DIAGNOSIS['mind']['score_question']}",
        reply_markup=SCORE_KEYBOARD
    )
    return DIAGNOSIS_SPIRIT_1

# ── ДУХ ───────────────────────────────────────────────────────────────────────
async def diag_spirit_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = int(update.message.text)
        context.user_data["mind_score"] = score
    except ValueError:
        await update.message.reply_text("Пожалуйста, выбери число от 1 до 10", reply_markup=SCORE_KEYBOARD)
        return DIAGNOSIS_SPIRIT_1

    q = DIAGNOSIS["spirit"]
    await update.message.reply_text(
        f"Разум — записан ✓\n\n*{q['title']}*\n_{q['subtitle']}_\n\n"
        f"Это самый глубокий аспект. Отвечай медленно.\n\n"
        f"1️⃣ {q['questions'][0]}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return DIAGNOSIS_SPIRIT_2

async def diag_spirit_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "spirit", DIAGNOSIS["spirit"]["questions"][0], update.message.text)
    await update.message.reply_text(f"2️⃣ {DIAGNOSIS['spirit']['questions'][1]}")
    return DIAGNOSIS_SPIRIT_3

async def diag_spirit_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "spirit", DIAGNOSIS["spirit"]["questions"][1], update.message.text)
    await update.message.reply_text(f"3️⃣ {DIAGNOSIS['spirit']['questions'][2]}")
    return DIAGNOSIS_SPIRIT_4

async def diag_spirit_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "spirit", DIAGNOSIS["spirit"]["questions"][2], update.message.text)
    await update.message.reply_text(f"4️⃣ {DIAGNOSIS['spirit']['questions'][3]}")
    return DIAGNOSIS_SPIRIT_5

async def diag_spirit_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "spirit", DIAGNOSIS["spirit"]["questions"][3], update.message.text)
    await update.message.reply_text(f"5️⃣ {DIAGNOSIS['spirit']['questions'][4]}")
    return DIAGNOSIS_SPIRIT_6

async def diag_spirit_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "spirit", DIAGNOSIS["spirit"]["questions"][4], update.message.text)
    await update.message.reply_text(f"6️⃣ {DIAGNOSIS['spirit']['questions'][5]}")
    return DIAGNOSIS_SPIRIT_SCORE

async def diag_spirit_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "spirit", DIAGNOSIS["spirit"]["questions"][5], update.message.text)
    await update.message.reply_text(
        f"Хорошо.\n\n{DIAGNOSIS['spirit']['score_question']}",
        reply_markup=SCORE_KEYBOARD
    )
    return DIAGNOSIS_WORLD_1

# ── МИР ───────────────────────────────────────────────────────────────────────
async def diag_world_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        score = int(update.message.text)
        context.user_data["spirit_score"] = score
    except ValueError:
        await update.message.reply_text("Пожалуйста, выбери число от 1 до 10", reply_markup=SCORE_KEYBOARD)
        return DIAGNOSIS_WORLD_1

    q = DIAGNOSIS["world"]
    await update.message.reply_text(
        f"Дух — записан ✓\n\n*{q['title']}*\n_{q['subtitle']}_\n\n"
        f"1️⃣ {q['questions'][0]}",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return DIAGNOSIS_WORLD_2

async def diag_world_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "world", DIAGNOSIS["world"]["questions"][0], update.message.text)
    await update.message.reply_text(f"2️⃣ {DIAGNOSIS['world']['questions'][1]}")
    return DIAGNOSIS_WORLD_3

async def diag_world_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "world", DIAGNOSIS["world"]["questions"][1], update.message.text)
    await update.message.reply_text(f"3️⃣ {DIAGNOSIS['world']['questions'][2]}")
    return DIAGNOSIS_WORLD_4

async def diag_world_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "world", DIAGNOSIS["world"]["questions"][2], update.message.text)
    await update.message.reply_text(f"4️⃣ {DIAGNOSIS['world']['questions'][3]}")
    return DIAGNOSIS_WORLD_5

async def diag_world_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "world", DIAGNOSIS["world"]["questions"][3], update.message.text)
    await update.message.reply_text(f"5️⃣ {DIAGNOSIS['world']['questions'][4]}")
    return DIAGNOSIS_WORLD_6

async def diag_world_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "world", DIAGNOSIS["world"]["questions"][4], update.message.text)
    await update.message.reply_text(f"6️⃣ {DIAGNOSIS['world']['questions'][5]}")
    return DIAGNOSIS_WORLD_SCORE

async def diag_world_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_answer(update.effective_user.id, "world", DIAGNOSIS["world"]["questions"][5], update.message.text)
    await update.message.reply_text(
        f"Почти готово.\n\n{DIAGNOSIS['world']['score_question']}",
        reply_markup=SCORE_KEYBOARD
    )
    return DIAGNOSIS_FINAL

# ── ИТОГ ДИАГНОСТИКИ ──────────────────────────────────────────────────────────
async def diag_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        world_score = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, выбери число от 1 до 10", reply_markup=SCORE_KEYBOARD)
        return DIAGNOSIS_FINAL

    user_id = update.effective_user.id
    body = context.user_data.get("body_score", 5)
    mind = context.user_data.get("mind_score", 5)
    spirit = context.user_data.get("spirit_score", 5)
    world = world_score

    weak = save_scores(user_id, body, mind, spirit, world)
    wheel = draw_wheel(body, mind, spirit, world)
    weak_label = get_weak_label(weak)

    await update.message.reply_text(
        f"Диагностика завершена ✓\n\n{wheel}\n\n"
        f"Твой наименее развитый аспект сейчас — *{weak_label}*\n\n"
        f"Это не проблема. Это просто точка куда стоит направить внимание в первую очередь.\n\n"
        f"И последний вопрос на сегодня — самый важный:\n\n"
        f"*Какой аспект ты дольше всего оставлял без внимания — и что ты чувствуешь когда смотришь на это честно?*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return WEEKLY_REFLECTION

async def save_final_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_reflection(user_id, 0, update.message.text)

    user = get_user(user_id)
    weak = user[10] if user else ""
    weak_label = get_weak_label(weak)

    import random
    practice = random.choice(PRACTICES.get(weak, PRACTICES["body"]))

    await update.message.reply_text(
        f"Спасибо за честность. Это и есть начало.\n\n"
        f"На этой неделе твоё задание — одно маленькое действие для аспекта *{weak_label}*:\n\n"
        f"_{practice}_\n\n"
        f"Не нужно менять всё сразу. Просто сделай это одно.\n\n"
        f"В конце недели я спрошу тебя — что заметил. Договорились?\n\n"
        f"Команды:\n"
        f"/wheel — посмотреть своё колесо\n"
        f"/practice — получить практику на сегодня\n"
        f"/reflect — поделиться наблюдением",
        parse_mode="Markdown"
    )

    # Уведомить администратора
    if ADMIN_CHAT_ID:
        try:
            user_info = update.effective_user
            await context.bot.send_message(
                ADMIN_CHAT_ID,
                f"🆕 Новый участник завершил диагностику!\n"
                f"Имя: {user_info.first_name}\n"
                f"Username: @{user_info.username or 'нет'}\n"
                f"Слабый аспект: {weak_label}"
            )
        except Exception:
            pass

    return ConversationHandler.END

# ── КОМАНДЫ ───────────────────────────────────────────────────────────────────
async def show_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user or not user[7]:  # diagnosis_done
        await update.message.reply_text(
            "Ты ещё не прошёл диагностику. Напиши /start чтобы начать."
        )
        return

    wheel = draw_wheel(user[8], user[9], user[10], user[11])  # scores
    await update.message.reply_text(wheel, parse_mode="Markdown")

async def get_practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    if not user or not user[7]:
        await update.message.reply_text("Сначала пройди диагностику: /start")
        return

    weak = user[12]  # weak_aspect
    import random
    practice = random.choice(PRACTICES.get(weak, PRACTICES["body"]))
    weak_label = get_weak_label(weak)

    await update.message.reply_text(
        f"Твоя практика на сегодня — для аспекта *{weak_label}*:\n\n_{practice}_\n\n"
        f"Сделай — и поделись наблюдением через /reflect 🙏",
        parse_mode="Markdown"
    )

async def reflect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Поделись своим наблюдением за эту неделю.\n\n"
        "Что заметил? Что изменилось — даже чуть-чуть? Где почувствовал неожиданный эффект?\n\n"
        "Просто напиши — я слушаю.",
        reply_markup=ReplyKeyboardRemove()
    )
    return WEEKLY_REFLECTION

async def save_weekly_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    week = user[13] if user else 1  # week_number
    save_reflection(user_id, week, update.message.text)
    increment_week(user_id)

    await update.message.reply_text(
        "Записал. Спасибо за честность.\n\n"
        "Каждое такое наблюдение — это шаг к целостности. Продолжай замечать.\n\n"
        "Новая практика придёт в начале следующей недели. До встречи! 🙏"
    )
    return ConversationHandler.END

# ── ADMIN ─────────────────────────────────────────────────────────────────────
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    users = get_all_users()
    if not users:
        await update.message.reply_text("Участников пока нет.")
        return

    text = f"📊 *Статистика Фортего*\nУчастников: {len(users)}\n\n"
    for u in users:
        name, b, m, s, w, weak, week = u[1], u[2], u[3], u[4], u[5], u[6], u[7]
        text += f"👤 {name} | Т:{b} Р:{m} Д:{s} М:{w} | Слабый: {get_weak_label(weak)} | Неделя {week}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Хорошо, остановились. Когда будешь готов — напиши /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    diagnosis_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            DIAGNOSIS_BODY_1:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_body_intro)],
            DIAGNOSIS_BODY_2:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_body_2)],
            DIAGNOSIS_BODY_3:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_body_3)],
            DIAGNOSIS_BODY_4:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_body_4)],
            DIAGNOSIS_BODY_5:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_body_5)],
            DIAGNOSIS_BODY_6:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_body_6)],
            DIAGNOSIS_BODY_SCORE:[MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_intro)],
            DIAGNOSIS_MIND_1:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_intro)],
            DIAGNOSIS_MIND_2:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_2)],
            DIAGNOSIS_MIND_3:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_3)],
            DIAGNOSIS_MIND_4:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_4)],
            DIAGNOSIS_MIND_5:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_5)],
            DIAGNOSIS_MIND_6:    [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_mind_6)],
            DIAGNOSIS_MIND_SCORE:[MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_intro)],
            DIAGNOSIS_SPIRIT_1:  [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_intro)],
            DIAGNOSIS_SPIRIT_2:  [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_2)],
            DIAGNOSIS_SPIRIT_3:  [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_3)],
            DIAGNOSIS_SPIRIT_4:  [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_4)],
            DIAGNOSIS_SPIRIT_5:  [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_5)],
            DIAGNOSIS_SPIRIT_6:  [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_spirit_6)],
            DIAGNOSIS_SPIRIT_SCORE:[MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_intro)],
            DIAGNOSIS_WORLD_1:   [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_intro)],
            DIAGNOSIS_WORLD_2:   [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_2)],
            DIAGNOSIS_WORLD_3:   [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_3)],
            DIAGNOSIS_WORLD_4:   [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_4)],
            DIAGNOSIS_WORLD_5:   [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_5)],
            DIAGNOSIS_WORLD_6:   [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_world_6)],
            DIAGNOSIS_WORLD_SCORE:[MessageHandler(filters.TEXT & ~filters.COMMAND, diag_final)],
            DIAGNOSIS_FINAL:     [MessageHandler(filters.TEXT & ~filters.COMMAND, diag_final)],
            WEEKLY_REFLECTION:   [MessageHandler(filters.TEXT & ~filters.COMMAND, save_final_reflection)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    reflect_handler = ConversationHandler(
        entry_points=[CommandHandler("reflect", reflect)],
        states={
            WEEKLY_REFLECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_weekly_reflection)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(diagnosis_handler)
    app.add_handler(reflect_handler)
    app.add_handler(CommandHandler("wheel", show_wheel))
    app.add_handler(CommandHandler("practice", get_practice))
    app.add_handler(CommandHandler("stats", admin_stats))

    logger.info("Бот Фортего запущен 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
