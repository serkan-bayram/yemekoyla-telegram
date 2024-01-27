from telegram import Update
from telegram.ext import ContextTypes

async def getMenuInfoError(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Üzgünüm, bu işlemi şu an da gerçekleştiremiyorum.")

async def downloadMenuError(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Üzgünüm, bu işlemi şu an da gerçekleştiremiyorum.")

