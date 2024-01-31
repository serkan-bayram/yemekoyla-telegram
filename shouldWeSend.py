import os

def shouldWeSend(menuDate):
    if not os.path.exists("./lastSent.txt"):
        with open("lastSent.txt", "w") as f:
            print("lastSent is created.")

    with open("lastSent.txt", "r") as f:
        lastSent = f.read()

    if lastSent != menuDate:
        with open("lastSent.txt", "w") as f:
            f.write(menuDate)
        return True

    return False