import json
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)

# ===== 初始化日志 =====
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ===== 加载配置文件 =====
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]
WHITELIST = set(config["whitelist"])         # 可以私聊机器人的人（如你自己）
BLACKLIST = set(config["blacklist"])         # 黑名单 UID
ALLOWED_GROUPS = set(config["allowed_groups"])  # 允许响应的群组 ID


# ===== 私聊静默处理 =====
async def private_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITELIST:
        return  # 静默无响应
    await update.message.reply_text("✅ 你是授权用户，Bot 已准备好！")


# ===== 群聊黑名单自动删除 =====
async def group_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in ALLOWED_GROUPS:
        return  # 群不在允许列表中，静默
    if user_id in BLACKLIST:
        try:
            await update.message.delete()
            logging.info(f"已删除黑名单用户 {user_id} 在群 {chat_id} 的消息")
        except Exception as e:
            logging.warning(f"⚠️ 删除失败：{e}")


# ===== 初始化授权群组 =====
async def initgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in WHITELIST:
        return  # 只有白名单用户能初始化群

    if chat_id not in ALLOWED_GROUPS:
        ALLOWED_GROUPS.add(chat_id)
        await update.message.reply_text("✅ 本群已授权，Bot 功能启用。")
        logging.info(f"群组 {chat_id} 被 {user_id} 授权启用")
    else:
        await update.message.reply_text("✅ 本群已在授权列表中，无需重复操作。")


# ===== 主程序入口 =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # 私聊处理器
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, private_handler))

    # 群聊消息处理器（自动删除黑名单消息）
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, group_guard))

    # 初始化群授权指令（只允许白名单用户使用）
    app.add_handler(CommandHandler("initgroup", initgroup))

    logging.info("🤖 Bot 已启动，正在监听中...")
    app.run_polling()


if __name__ == "__main__":
    main()
