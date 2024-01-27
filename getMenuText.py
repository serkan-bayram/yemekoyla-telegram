def getMenuText(menuArray):
    menuText = "Günün Menüsü: \n\n"

    for food in menuArray:
        menuText += food + "\n"

    menuText += "\nAfiyet olsun."

    return menuText