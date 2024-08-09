import sqlite3
import feedparser
from telegram import Bot
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram bot token from environment variable
API_TOKEN = os.getenv("API_TOKEN")
CHAT_ID = '1661385198'  # Replace with your chat ID or manage user chat IDs

# RSS feed URLs
RSS_FEEDS = {
    'venturebeat': 'https://venturebeat.com/feed/',
    'techcrunch_ai': 'https://techcrunch.com/category/artificial-intelligence/feed/'
}

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
def notify_users():
    bot = Bot(token=API_TOKEN)
    new_articles = fetch_latest_news()

    if new_articles:
        for article in new_articles:
            name, title, link = article
            message = f"New article from {name.upper()}:\n{title}\n{link}"
            bot.send_message(chat_id=CHAT_ID, text=message)

if __name__ == '__main__':
    init_db()
    notify_users()
