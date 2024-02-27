from dotenv import load_dotenv
import requests
import os
import base64
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import io
from PIL import Image
from scipy.ndimage import gaussian_filter
import numpy
import pytesseract
from PIL import ImageFilter

LOGIN_URL = "https://unka.bilecik.edu.tr:82"


def checkUserBalance(school_id):
    print(f"\n--- Getting balance for {school_id} ---\n")

    # We try only N times for an user
    tried_count = 0

    while True:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--headless=new")

        driver = webdriver.Chrome(options=options)

        if tried_count == 5:
            print(f"--- Getting balance is failed for {school_id} ---\n")
            driver.quit()
            return None

        try:
            get_captcha_image(driver)

            edit_image()

            numbers = read_image()

            fill_inputs(school_id, numbers, driver)

            balance = get_user_balance(driver)

            driver.quit()
            return balance
        except Exception as e:
            tried_count += 1
            print(f"\n--- Error on Main, trying again: {e} ---\n")
            driver.quit()
            continue


def get_captcha_image(driver):
    driver.get(LOGIN_URL)

    # Close cookie popup
    # TODO: Send cookies with selenium
    try:
        element = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable(
                (By.XPATH, "/html/body/div[1]/div/div/div[2]/div/div/div[3]/button"))
        )

        element.click()

        print("Cookie popup is closed.")
    except:
        raise Exception("Cookie close button is not found.")

    # Save screenshot of Captcha
    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "img_captcha"))
        )

        while not element.is_displayed():
            time.sleep(1)
            continue

        time.sleep(1)

        print("Captcha image is found: ", element)

        image_binary = element.screenshot_as_png
        img = Image.open(io.BytesIO(image_binary))
        img.save("./captcha/screenshot_captcha.png")

        print("Screenshot is saved.")
    except:
        raise Exception("Captcha is not found.")


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

        print("Read numbers: ", read_numbers)

        return read_numbers
    except:
        raise Exception("GPT response isn't correct.")


def fill_inputs(tckimno, numbers, driver):
    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "TCKIMLIKNO"))
        )

        element.send_keys(tckimno)

        print("TCKimNo is filled.")
    except Exception as e:
        raise Exception("TCKimNo Input is not found: ", e)

    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "CAPTCHA"))
        )

        element.send_keys(numbers)

        print("Captcha is filled.")
    except Exception as e:
        raise Exception("Captcha Input is not found: ", e)

    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "btnLogin"))
        )

        element.click()

        print("Login button is clicked.")
    except Exception as e:
        raise Exception("Login button is not found: ", e)


def get_user_balance(driver):
    try:
        element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "CARD_BODY"))
        )

        td_elements = element.find_element(By.TAG_NAME,
                                           "table").find_elements(By.TAG_NAME, "td")

        user_balance = td_elements[1].get_attribute("innerText")

        print("User balance: ", user_balance)

        return user_balance
    except Exception as e:
        raise Exception("User balance is not found: ", e)
