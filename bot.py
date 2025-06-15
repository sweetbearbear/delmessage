# bot.py
import os
import time
import threading
from telegram import Bot
from dotenv import load_dotenv
from check_live import is_streaming
from record import record_stream_and_send

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LIVE_UID = os.getenv("LIVE_UID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL"， 600))

bot = Bot(token=BOT_TOKEN)


def monitor():
    print("📡 直播检测任务已启动...")
    while True:
        try:
            if is_streaming(LIVE_UID):
                print("✅ 检测到直播开始，准备录制...")
                record_stream_and_send(uid=LIVE_UID, bot=bot, chat_id=CHAT_ID)
            else:
                print("❌ 当前未开播。")
        except Exception as e:
            print(f"⚠️ 检测时发生错误: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    thread = threading.Thread(target=monitor)
    thread.start()
