import logging
import telegram
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from getMenuInfo import getMenuInfo
from downloadMenu import downloadMenu
from getMenuText import getMenuText
from errors import getMenuInfoError, downloadMenuError
from shouldWeSend import shouldWeSend

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

with open("bot_token", "r") as f:
    TOKEN = f.read()

bot = telegram.Bot(TOKEN)

with open("group_id", "r") as f:
    GROUP_ID = f.read()

async def getMenuByRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menuArray, menuURL, menuDate = getMenuInfo()
    except Exception as e:
        print(e)
        await getMenuInfoError(update, context)
        return

    try:
        filename = downloadMenu(menuDate, menuURL)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(f"./data/{filename}", "rb"))
        
        menuText = getMenuText(menuArray)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=menuText)
    except Exception as e:
        print(e)
        await downloadMenuError(update, context)
        return


async def sendMenuOfDay(context: ContextTypes.DEFAULT_TYPE):
    try:
        menuArray, menuURL, menuDate = getMenuInfo()
        
        if not shouldWeSend(menuDate):
            return
    except Exception as e:
        print(e)
        return
    
    try:
        filename = downloadMenu(menuDate, menuURL)
        await context.bot.send_photo(chat_id=GROUP_ID, photo=open(f"./data/{filename}", "rb"))
        
        menuText = getMenuText(menuArray)
        await context.bot.send_message(chat_id=GROUP_ID, text=menuText)
    except Exception as e:
        print(e)
        return  


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Merhaba {update.effective_user.full_name} ben YemekBot!\n\nAmacım günün yemeğini sana olabildiğince erken ulaştırmak, şimdiden afiyet olsun. ☺️"

    await context.bot.send_message(chat_id=update.effective_user.id, text=text)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Üzgünüm, girdiğiniz komutu anlayamadım.")


if __name__ == '__main__':
    print("Bot is alive.")

    application = ApplicationBuilder().token(TOKEN).build()
    
    getMenu_handler = CommandHandler('menu', getMenuByRequest)
    start_handler = CommandHandler(["basla", "yardim"], start)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.job_queue.run_repeating(callback=sendMenuOfDay, interval=1800, chat_id=GROUP_ID)
    
    application.add_handler(getMenu_handler)
    application.add_handler(start_handler)
    application.add_handler(unknown_handler) # This should be in last line

    application.run_polling()