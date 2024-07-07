from dotenv import load_dotenv
import requests
import os
import base64
from PIL import Image
from scipy.ndimage import gaussian_filter
import numpy
import pytesseract
from PIL import ImageFilter
from bs4 import BeautifulSoup
import traceback

LOGIN_URL = "https://unka.bilecik.edu.tr:82"
headers = {'User-Agent': 'Mozilla/5.0'}


def checkUserBalance(school_id):


    print(f"\n--- Getting balance for {school_id} ---\n")

    # We try only N times for an user
    tried_count = 0

    while True:
        if tried_count == 5:
            print(f"--- Getting balance is failed for {school_id} ---\n")
            return None

        try:
            # Using same session for everything is important
            session = requests.Session()

            cookies, rvt = get_initial_cookies(session)

            get_captcha_image(session, cookies)

            edit_image()

            numbers = read_image()

            status = fill_inputs(school_id, numbers, session, cookies, rvt)

            if status == 200:
                balance = get_user_balance(session, cookies)
                return balance

            raise Exception("Status is not 200: ", status)
        except Exception as e:
            tried_count += 1
            print(f"\n--- Error on Main, trying again: {e} ---\n")
            print(traceback.format_exc())
            continue


def get_initial_cookies(session):
    page = session.get(
        LOGIN_URL, headers=headers)

    # This might be not neccessary
    accept_cookies = {".AspNet.Consent": "yes"}

    session.cookies.update(accept_cookies)

    soup = BeautifulSoup(page.content, 'html.parser')

    # Get RequestVerificationToken from a hidden input
    rvt = soup.find("input", attrs={"name": "__RequestVerificationToken"})[
        'value']

    return session.cookies, rvt


def fill_inputs(school_id, numbers, session, cookies, rvt):
    payload = {'LOGIN_FIELD': 'TCKIMLIKNO',
               'TCKIMLIKNO': school_id, 'CAPTCHA': numbers, "__RequestVerificationToken": rvt}

    login_response = session.post(
        "https://unka.bilecik.edu.tr:82/User/LoginAsync",
        headers=headers, cookies=cookies, data=payload)

    return login_response.status_code


def get_captcha_image(session, cookies):
    # Save captcha
    try:
        captcha = session.get(
            "https://unka.bilecik.edu.tr:82/Captcha/CaptchaImage?I=1709228631770", headers=headers, cookies=cookies)

        open("./captcha/screenshot_captcha.png", "wb").write(captcha.content)
    except:
        raise Exception("An error happened while getting captcha image.")


# We edit captcha because GPT refuses to read numbers
# If it understands it's a captcha
# TODO: Too many unneccessary image is creating.
def edit_image():
    try:
        # thresold1 on the first stage
        th1 = 220
        th2 = 90  # threshold after blurring
        sig = 1.7  # the blurring sigma

        original = Image.open("./captcha/screenshot_captcha.png")

        # reading the image from the request
        original.save("./captcha/original.png")

        black_and_white = original.convert(
            "L")  # converting to black and white
        black_and_white.save("./captcha/black_and_white.png")
        first_threshold = black_and_white.point(lambda p: p > th1 and 255)
        first_threshold.save("./captcha/first_threshold.png")

        blur = numpy.array(first_threshold)  # create an image array
        blurred = gaussian_filter(blur, sigma=sig)
        blurred = Image.fromarray(blurred)
        blurred.save("./captcha/blurred.png")
        final = blurred.point(lambda p: p > th2 and 255)

        final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
        final = final.filter(ImageFilter.SHARPEN)
        final.save("./captcha/final.png")
        number = pytesseract.image_to_string(Image.open('./captcha/final.png'))
    except Exception as e:
        raise Exception("Error on edit_image: ", e)


def encode_image(image_path):
    # Function to encode the image
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def read_image():
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    # Path to your image
    image_path = "./captcha/final.png"

    # Getting the base64 string
    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a photo of 4 digit integer. Like: 1234, 3124, 8792. Read the numbers from this image. Only give numbers. Don't write anything else."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

        print("GPT Response: ", response.json())

        read_numbers = response.json()["choices"][0]["message"]["content"]

        return read_numbers
    except:
        raise Exception("GPT response isn't correct.")


def get_user_balance(session, cookies):
    try:
        personel = session.get(
            "https://unka.bilecik.edu.tr:82/Personel", headers=headers, cookies=cookies)

        soup = BeautifulSoup(personel.content, 'html.parser')

        balance = soup.select(
            "#CARD_BODY table tr:first-child td:last-child")[0].text

        return balance.strip()
    except Exception as e:
        raise Exception("User balance is not found: ", e)
