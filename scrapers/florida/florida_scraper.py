import cloudscraper
from bs4 import BeautifulSoup as bs
import re
import json

BASE_URL = "https://dos.elections.myflorida.com/supervisors/"

scraper = cloudscraper.create_scraper()

r = scraper.get(BASE_URL)
soup = bs(r.content, 'html.parser')

urlElems = soup.find_all('li')

countyCodes = []
countyNames = []

for url in urlElems:
    a = url.find('a')
    href = a['href']
    if ('county' in href):
        countyCodes.append(href.split('=')[-1])
        countyNames.append(a.text)

#countyCodes.sort()
#countyNames.sort()

# Given a three-letter county code, scrape that specific county webpage's data.
# Returns a tuple of the format (address, phone)
def scrapeOneCounty(code):
    URL = BASE_URL + "countyInfo.asp?county=" + code
    t = scraper.get(URL)
    soup = bs(t.content, 'html.parser')
    
    # relevant info is in a random <p> with no classes
    countyInfo = soup.find('p', attrs={'class': None}).text

    # clean up \t \r \n tags from string
    example = {"\t": None, "\n": " ", "\r": None}
    table = countyInfo.maketrans(example)
    cleaned = countyInfo.translate(table)

    #extract address info which is always between supervisor and phone
    address = re.search('Supervisor(.*)Phone:', cleaned)
    phone = re.search('Phone: (.*)Fax:', cleaned)
    addressResult = 'None' if address is None else address.group(1)
    phoneResult = 'None' if phone is None else phone.group(1)
    return addressResult, phoneResult
    
masterList = []

for index, county in enumerate(countyNames):
    code = countyCodes[index]
    print(code, county)
    address, phone = scrapeOneCounty(code)
    result = {'address': address, 'phone': phone}
    masterResult = {'county': county, 'data': result}
    masterList.append(masterResult)

print(masterList)





