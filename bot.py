import sqlite3
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8672258475:AAEYVNVkycE-jwdJCZ3Ut1gIxTZFCxw_Aio"
ADMIN_ID = 8512949204

conn = sqlite3.connect("movies.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    code TEXT PRIMARY KEY,
    photo TEXT,
    link TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    code TEXT
)
""")
conn.commit()

ADD_PHOTO, ADD_LINK = range(2)

def generate_code():
    return str(random.randint(1000, 9999))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Kod kiriting:")

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text
    user_id = update.message.from_user.id

    cursor.execute("SELECT * FROM movies WHERE code=?", (code,))
    result = cursor.fetchone()

    if result:
        cursor.execute("INSERT INTO users VALUES (?, ?)", (user_id, code))
        conn.commit()

        _, photo, link = result
        await update.message.reply_photo(photo=photo, caption=f"📥 {link}")
    else:
        await update.message.reply_text("❌ Kod topilmadi")

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    code = generate_code()
    context.user_data["code"] = code

    await update.message.reply_text(f"🎬 Kod: {code}\nRasm yuboring:")
    return ADD_PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["photo"] = update.message.photo[-1].file_id
    await update.message.reply_text("Link yuboring:")
    return ADD_LINK

async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = context.user_data["code"]
    photo = context.user_data["photo"]
    link = update.message.text

    cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (code, photo, link))
    conn.commit()

    await update.message.reply_text(f"✅ Saqlandi: {code}")
    return ConversationHandler.END

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    await update.message.reply_text(f"📊 Kirishlar: {total}")

app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler("add", add_start)],
    states={
        ADD_PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
        ADD_LINK: [MessageHandler(filters.TEXT, add_link)],
    },
    fallbacks=[]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT, handle_code))
app.add_handler(conv)

app.run_polling()
