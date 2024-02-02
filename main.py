import logging
import asyncio
import telegram
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, PollAnswerHandler, ContextTypes, CommandHandler, MessageHandler, Application
from getMenuInfo import getMenuInfo
from downloadMenu import downloadMenu
from getMenuText import getMenuText
from errors import getMenuInfoError, downloadMenuError
from shouldWeSend import shouldWeSend
from saveRating import saveRating
from bindMenuWithPoll import bindMenuWithPoll

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

with open("bot_token", "r") as f:
    TOKEN = f.read()

bot = telegram.Bot(TOKEN)

with open("group_id", "r") as f:
    GROUP_ID = f.read()

API_URL = "https://yemekhane-puanla.vercel.app/api"

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
    
        # SET INTERVAL TO TWO HOURS LATER
        context.job_queue.run_once(poll, 9000, chat_id=GROUP_ID)
    except Exception as e:
        print(e)
        return  
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Merhaba {update.effective_user.full_name} ben YemekBot!\n\nAmacım günün yemeğini sana olabildiğince erken ulaştırmak, şimdiden afiyet olsun. ☺️"

    await context.bot.send_message(chat_id=update.effective_user.id, text=text)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Üzgünüm, girdiğiniz komutu anlayamadım.")

async def post_init(application: Application):
    print("the bot is initiliazed")

# sent polls id should attach to last shared menu on db
async def poll(context: ContextTypes.DEFAULT_TYPE):
    questions = ["Çok kötü", "Kötü", "Ortalama", "Güzel", "Çok güzel"]
    
    message = await context.bot.send_poll(
        GROUP_ID,
        "Yemek nasıldı?",
        questions,
        is_anonymous=False,
        allows_multiple_answers=False,
    )
    
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "questions": questions,
            "message_id": message.message_id,
            "chat_id": GROUP_ID,
            "answers": 0,
        }
    }
    
    context.bot_data.update(payload)

    bindMenuWithPoll(message.poll.id, TOKEN, API_URL)

async def receivePollAnswer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer

    pollId = answer.poll_id
    votedBy = answer.user.id
    isVoted = False
    votedOption = None

    if len(answer.option_ids) > 0:
        # A user is voted something.
        isVoted = True
        votedOption = answer.option_ids[0]
    else:
        # A user is retracted its vote.
        isVoted = False

    saveRating(pollId, votedBy, isVoted, votedOption, API_URL, TOKEN)


if __name__ == '__main__':
    print("Bot is alive.")

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()


    getMenu_handler = CommandHandler('menu', getMenuByRequest)
    poll_handler = CommandHandler("oyla", poll)
    receivePollAnswer_handler = PollAnswerHandler(receivePollAnswer)
    start_handler = CommandHandler(["basla", "yardim"], start)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    # SET INTERVAL TO 1800
    application.job_queue.run_repeating(callback=sendMenuOfDay, interval=1800, chat_id=GROUP_ID)
    
    application.add_handler(getMenu_handler)
    application.add_handler(start_handler)
    application.add_handler(poll_handler)
    application.add_handler(receivePollAnswer_handler)
    application.add_handler(unknown_handler) # This should be in last line

    application.run_polling()