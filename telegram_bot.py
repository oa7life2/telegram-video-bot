import os
import logging
import requests
from pytube import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from threading import Thread
import uvicorn
from fastapi import FastAPI

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use environment variable for the token
TOKEN = os.environ.get("BOT_TOKEN", "7573230533:AAGiwZ06Oes7w8ZyX7Ahlv15Vaqn5mgA2P0")

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! أرسل لي رابط فيديو من يوتيوب أو تيك توك.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("فقط أرسل لي رابط فيديو من يوتيوب أو تيك توك!")

# YouTube video handler
async def handle_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    try:
        await update.message.reply_text("جارٍ تحميل فيديو يوتيوب...")
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        stream.download(filename="youtube_video.mp4")

        with open("youtube_video.mp4", "rb") as f:
            await update.message.reply_video(f, caption="إليك فيديو اليوتيوب!")

        os.remove("youtube_video.mp4")
    except Exception as e:
        logger.error(f"YouTube download failed: {e}")
        await update.message.reply_text("فشل تحميل فيديو اليوتيوب.")

# TikTok video handler
async def handle_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    try:
        await update.message.reply_text("جارٍ تحميل فيديو تيك توك...")
        api = f"https://tikwm.com/api/?url={url}"
        r = requests.get(api).json()

        video_url = r["data"]["play"] if r["data"] else None
        if not video_url:
            raise Exception("TikTok video URL not found.")

        video_data = requests.get(video_url).content
        with open("tiktok_video.mp4", "wb") as f:
            f.write(video_data)

        with open("tiktok_video.mp4", "rb") as f:
            await update.message.reply_video(f, caption="إليك فيديو التيك توك!")

        os.remove("tiktok_video.mp4")
    except Exception as e:
        logger.error(f"TikTok download failed: {e}")
        await update.message.reply_text("فشل تحميل فيديو التيك توك.")

# Invalid link handler
async def handle_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("الرجاء إرسال رابط من يوتيوب أو تيك توك.")

# Main function for bot logic
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.Regex("youtube.com|youtu.be"), handle_youtube))
    app.add_handler(MessageHandler(filters.Regex("tiktok.com"), handle_tiktok))
    app.add_handler(MessageHandler(filters.TEXT, handle_invalid))

    # Start the bot
    logger.info("Bot is running...")
    app.run_polling()

# Create a FastAPI app to keep the service running
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Bot is running!"}

def run_bot():
    main()

if __name__ == "__main__":
    # Start the bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # Start a small web server to keep the app alive
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
