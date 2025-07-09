import asyncio 
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

# ===== 加载配置 =====
CONFIG_PATH = "config.json"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config_data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    logging.info("✅ 配置已保存到 config.json")

config = load_config()

TOKEN = config["token"]
WHITELIST = set(config["whitelist"])
BLACKLIST = set(config["blacklist"])
ALLOWED_GROUPS = set(config["allowed_groups"])


# ===== 私聊处理（身份判断 + 指令响应） =====
async def private_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITELIST:
        return  # 静默处理
    await update.message.reply_text("✅ 你是授权用户，可以使用控制命令。")


async def group_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    if chat_id in ALLOWED_GROUPS and user_id in BLACKLIST:
        asyncio.create_task(
            context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        )

# ===== 群授权命令（只能你用） =====
async def initgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if user_id not in WHITELIST:
        return

    if chat_id not in ALLOWED_GROUPS:
        ALLOWED_GROUPS.add(chat_id)
        config["allowed_groups"] = list(ALLOWED_GROUPS)
        save_config(config)
        await update.message.reply_text("✅ 本群已授权，Bot 功能启用。")
    else:
        await update.message.reply_text("✅ 本群已经启用，无需重复操作。")


# ===== 私聊命令：添加黑名单 =====
async def banuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITELIST:
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ 格式错误：请使用 /banuid <uid>")
        return

    target_uid = int(context.args[0])
    if target_uid in BLACKLIST:
        await update.message.reply_text(f"⚠️ UID {target_uid} 已在黑名单中。")
        return

    BLACKLIST.add(target_uid)
    config["blacklist"] = list(BLACKLIST)
    save_config(config)
    await update.message.reply_text(f"✅ 已添加 UID {target_uid} 到黑名单。")


# ===== 私聊命令：移除黑名单 =====
async def unbanuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITELIST:
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("❌ 格式错误：请使用 /unbanuid <uid>")
        return

    target_uid = int(context.args[0])
    if target_uid not in BLACKLIST:
        await update.message.reply_text(f"⚠️ UID {target_uid} 不在黑名单中。")
        return

    BLACKLIST.remove(target_uid)
    config["blacklist"] = list(BLACKLIST)
    save_config(config)
    await update.message.reply_text(f"✅ 已从黑名单中移除 UID {target_uid}。")


# ===== 主程序入口 =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("initgroup", initgroup))
    app.add_handler(CommandHandler("banuid", banuid))
    app.add_handler(CommandHandler("unbanuid", unbanuid))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, private_handler))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, group_guard))

    logging.info("🤖 Bot 启动成功，开始监听。")
    app.run_polling()


if __name__ == "__main__":
    main()
