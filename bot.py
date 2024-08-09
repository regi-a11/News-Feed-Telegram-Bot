import sqlite3
import feedparser
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
    ContextTypes,
    filters,
)
import os
from dotenv import load_dotenv
from queue import Queue

load_dotenv()

# Telegram bot token from environment variable
API_TOKEN = os.getenv("API_TOKEN")

# RSS feed URLs
RSS_FEEDS = {
    'venturebeat': 'https://venturebeat.com/feed/',
    'techcrunch_ai': 'https://techcrunch.com/category/artificial-intelligence/feed/'
}

my_queue = Queue()

# Conversation states
ASKING, TYPING_REPLY = range(2)

# Initialize the database
def init_db():
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS latest_news
                 (feed TEXT, title TEXT, link TEXT)''')
    conn.commit()
    conn.close()

# Function to get the latest news and update the database
def fetch_latest_news():
    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    new_articles = []

    for name, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        if feed.entries:
            entry = feed.entries[0]
            c.execute("SELECT * FROM latest_news WHERE feed=? AND link=?", (name, entry.link))
            if not c.fetchone():
                c.execute("INSERT INTO latest_news (feed, title, link) VALUES (?, ?, ?)",
                          (name, entry.title, entry.link))
                new_articles.append((name, entry.title, entry.link))

    conn.commit()
    conn.close()
    return new_articles

# Function to notify users about new articles
async def notify_users(context: ContextTypes.DEFAULT_TYPE):
    new_articles = fetch_latest_news()

    if new_articles:
        for article in new_articles:
            name, title, link = article
            keyboard = [
                [InlineKeyboardButton("Read More", url=link)],
                [InlineKeyboardButton("Share", switch_inline_query=title)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"New article from {name.upper()}:\n{title}"
            # Replace with your chat ID or a method to get user chat IDs
            chat_id = '1661385198'
            try:
                await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
            except Exception as e:
                print(f"Error sending notification: {e}")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Latest News", callback_data='latest')],
        [InlineKeyboardButton("Chat", callback_data='chat')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome! How can I assist you today?', reply_markup=reply_markup)

# Callback query handler
async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'latest':
        await latest(update, context)
    elif query.data == 'chat':
        await chat(update, context)
    elif query.data == 'help':
        await help_command(update, context)

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/latest - Get the latest news articles\n"
        "/chat - Chat with the bot\n"
        "/help - Show this help message"
    )
    if update.message:
        await update.message.reply_text(help_text)
    else:
        await update.callback_query.message.reply_text(help_text)

# Latest news command
async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    new_articles = fetch_latest_news()

    if new_articles:
        for article in new_articles:
            name, title, link = article
            keyboard = [
                [InlineKeyboardButton("Read More", url=link)],
                [InlineKeyboardButton("Share", switch_inline_query=title)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            message = f"Latest article from {name.upper()}:\n{title}"
            if update.message:
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.callback_query.message.reply_text(message, reply_markup=reply_markup)
    else:
        if update.message:
            await update.message.reply_text("No new articles at the moment.")
        else:
            await update.callback_query.message.reply_text("No new articles at the moment.")

# Chat command
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Hi! How can I help you today?")
    else:
        await update.callback_query.message.reply_text("Hi! How can I help you today?")
    return ASKING

# Echo user response
async def receive_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    response = f"You said: {user_message}. How can I assist you further?"
    keyboard = [
        [InlineKeyboardButton("Latest News", callback_data='latest')],
        [InlineKeyboardButton("Help", callback_data='help')],
        [InlineKeyboardButton("Cancel", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(response, reply_markup=reply_markup)
    return TYPING_REPLY

# Cancel the conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Conversation cancelled.")
    return ConversationHandler.END

def main():
    # Initialize the database
    init_db()

    # Set up the bot
    application = ApplicationBuilder().token(API_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("latest", latest))

    # Callback query handler
    application.add_handler(CallbackQueryHandler(callback_query_handler))

    # Conversation handler for chatting
    chat_handler = ConversationHandler(
        entry_points=[CommandHandler('chat', chat)],
        states={
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_response)],
            TYPING_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_response)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')]
    )

    application.add_handler(chat_handler)

    # Schedule the job to check for new articles every hour
    job_queue = application.job_queue
    job_queue.run_repeating(notify_users, interval=3600, first=0)

    # Start the bot
    print("Initializing the bot...")
    try:
        application.run_polling()
        print("Bot initialized successfully.")
    except Exception as e:
        print(f"Error initializing the bot: {e}")

if __name__ == '__main__':
    main()