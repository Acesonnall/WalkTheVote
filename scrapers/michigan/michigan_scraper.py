import requests
from bs4 import BeautifulSoup as bs
import re
import json

BASE_URL = "https://mvic.sos.state.mi.us/Clerk"

# found via Network tab in developer tools
NEW_URL = "https://mvic.sos.state.mi.us/Voter/SearchByCounty"

r = requests.get(BASE_URL, verify=False)
soup = bs(r.content, 'html.parser')

countyNames = []

def getCountyNames():
    dropdown = soup.find(id='Counties')
    options = soup.find_all('option')
    for option in options:
        if 'County' in option.text:
            countyNames.append(option.text)

getCountyNames()

alcona = countyNames[0].replace(" ", "+")

data = {'CountyName':alcona, 'CountyID': 1}

s = requests.post(NEW_URL, data, verify=False)
newsoup = bs(s.content, 'html.parser')
data = newsoup.find(id='pnlClerk').find(class_ = 'card-body').text.encode('utf-8')

print(data.decode())
