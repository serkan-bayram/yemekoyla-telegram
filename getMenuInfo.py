import requests
import ast

def getMenuInfo():
    menu = requests.get("http://localhost:3000/api/getMenu")
    
    menuArray = ast.literal_eval(menu.json()["menu"]["menu"])
    menuURL = menu.json()["menu"]["url"]
    menuDate = menu.json()["menu"]["date"]

    return menuArray, menuURL, menuDate