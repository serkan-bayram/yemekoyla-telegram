from bs4 import BeautifulSoup 

def getSofraCardData(session):
    url = "https://sofra.bilecik.edu.tr/Aks/AkilliKartBilgi"

    response = session.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')

    expenses = soup.find_all("span", {"class": "badge badge-danger bold"})
    loads =  soup.find_all("span", {"class": "badge badge-primary bold"})
    
    allExpenses = expenses[1].text.split('₺')[1].replace('.', '').replace(',', '.')
    allLoads = loads[1].text.split('₺')[1].replace('.', '').replace(',', '.')

    currentBalance = float(allLoads) - float(allExpenses)

    currentBalance = round(currentBalance, 2)

    return currentBalance