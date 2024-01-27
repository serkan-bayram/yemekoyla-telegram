import wget
import os

def downloadMenu(date, url):
    if not os.path.isdir("./data"):
        os.mkdir("./data")

    filenames = os.listdir("./data")

    for filename in filenames:
        filedate = filename.split(".jpeg")[0]
        if date == filedate:
            return filename

    wget.download(url, out="./data")

    return f"{date}.jpeg"

