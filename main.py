import logging
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
from bindTelegram import bindTelegram
from getUserBalances import getUserBalances
from checkUserBalance import checkUserBalance
from datetime import datetime, timezone, timedelta

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     level=logging.INFO
# )

with open("bot_token", "r") as f:
    TOKEN = f.read()

bot = telegram.Bot(TOKEN)

with open("group_id", "r") as f:
    GROUP_ID = f.read()

tz = timezone(timedelta(hours=3))

API_URL = "https://yemekhane-puanla.vercel.app/api"
# API_URL = "http://localhost:3000/api"
FOOD_COST = 20


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


async def checkUserBalances(context: ContextTypes.DEFAULT_TYPE):
    print("Checking user balances...")

    users = getUserBalances(TOKEN, API_URL)

    for user in users:
        school_id = user["school_id"]

        telegram_id = user["telegram_id"]

        currentBalance = checkUserBalance(school_id)

        if currentBalance == None:
            continue

        currentBalance = float(currentBalance.replace(',', '.').split(" ")[0])

        print(f"{school_id} balance is {currentBalance}")

        if currentBalance < float(FOOD_COST):
            await context.bot.send_message(chat_id=telegram_id, text=f"Dikkat! Bakiyenizde kalan miktar: {currentBalance}₺")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"Merhaba {update.effective_user.full_name} ben YemekBot!\n\nAmacım günün yemeğini sana olabildiğince erken ulaştırmak, şimdiden afiyet olsun. ☺️\n\n/bagla komutuyla Telegram hesabınızı Yemekoyla ile bağlayabilir, yemekhane yemeklerimizi iyileştirme yolunda sizinde katkınız olabilir. 😊"

    await context.bot.send_message(chat_id=update.effective_user.id, text=text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Üzgünüm, girdiğiniz komutu anlayamadım.\n/yardim yazarak daha fazla bilgi alabilirsiniz.")


async def post_init(application: Application):
    return


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

    print("New poll created: ", message.poll.id)

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


async def pollByRequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != GROUP_ID:
        return

    questions = ["Çok kötü", "Kötü", "Ortalama", "Güzel", "Çok güzel"]

    message = await context.bot.send_poll(
        GROUP_ID,
        "Yemek nasıldı?",
        questions,
        is_anonymous=False,
        allows_multiple_answers=False,
    )

    print("New poll created: ", message.poll.id)

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

    response = saveRating(pollId, votedBy, isVoted,
                          votedOption, API_URL, TOKEN)

    await context.bot.send_message(chat_id=answer.user.id, text=response)


def oyla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("")


async def bagla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_user.id, text="Geçersiz komut.\nKullanım şekli: /bagla {kullanıcı-adın}")
        return

    response = bindTelegram(update.effective_user.id,
                            context.args[0], API_URL, TOKEN)

    await context.bot.send_message(chat_id=update.effective_user.id, text=response)


if __name__ == '__main__':
    print("Bot is alive.")

    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    getMenu_handler = CommandHandler('menu', getMenuByRequest)
    pollByRequest_handler = CommandHandler("poll", pollByRequest)
    receivePollAnswer_handler = PollAnswerHandler(receivePollAnswer)
    start_handler = CommandHandler(["basla", "yardim", "start"], start)
    bagla_handler = CommandHandler("bagla", bagla)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.job_queue.run_repeating(
        callback=sendMenuOfDay, interval=1800, chat_id=GROUP_ID)

    application.job_queue.run_daily(
        callback=checkUserBalances, days=(1, 2, 3, 4, 5), time=datetime(1, 1, 1, 11, 00, tzinfo=tz))

    application.add_handler(getMenu_handler)
    application.add_handler(start_handler)
    application.add_handler(pollByRequest_handler)
    application.add_handler(bagla_handler)
    application.add_handler(receivePollAnswer_handler)
    application.add_handler(unknown_handler)  # This should be in last line

    application.run_polling()
