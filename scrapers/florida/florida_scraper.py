import asyncio
import os
import time

import cloudscraper
from bs4 import BeautifulSoup as bs
import re
import json
import usaddress
from aiocfscrape import CloudflareScraper
from string import printable

from ElectionSaver import electionsaver
from definitions import ROOT_DIR

BASE_URL = "https://dos.elections.myflorida.com/supervisors/"

scraper = cloudscraper.create_scraper()

def getCountyCodesAndNames(soup):
    urlElems = soup.find_all('li')
    res = []
    for url in urlElems:
        a = url.find('a')
        href = a['href']
        if ('county' in href):
            countyData = {
                "countyCode": href.split('=')[1],
                "countyName": a.text
            }
            res.append(countyData)
    return res

# function to decode hexadecimal email strings
# lifted this off some stackoverflow post lol
    
async def scrapeOneCounty(countyCode, countyName):
    URL = BASE_URL + "countyInfo.asp?county=" + countyCode
    # s = scraper.get(URL)
    async with CloudflareScraper() as session:
        async with session.get(URL) as s:
            text = await s.read()
            soup = bs(text.decode("utf-8"), 'html.parser')
    
    # relevant info is in a random <p> with no classes
    countyInfo = soup.find('p', attrs={'class': None}).text
    hexEmail = soup.find('span', class_="__cf_email__")['data-cfemail']

    # clean up \t \r \n tags from string
    example = {"\t": None, "\n": " ", "\r": None}
    table = countyInfo.maketrans(example)
    cleaned = countyInfo.translate(table)
    
    return cleaned, hexEmail

def formatDataIntoSchema(cleanedData, hexEmail, countyName):
    officeSupervisor = cleanedData.split(", Supervisor")[0].strip()
    officeSupervisor = re.sub("[^{}]+".format(printable), " ", officeSupervisor)

    # extract address info which is always between supervisor and phone
    address = re.search('Supervisor(.*)Phone:', cleanedData)
    addressResult = 'None' if address is None else address.group(1)
    physicalAddress = ""

    # similar setup for phone 
    phone = re.search('Phone: (.*)Fax:', cleanedData)
    phoneResult = 'None' if phone is None else phone.group(1).strip()

    # grab website
    website = re.search('Web Address: (.*)', cleanedData)
    websiteResult = 'None' if phone is None else website.group(1).strip()

    # extract and decode email
    email = electionsaver.decodeEmail(hexEmail)

    schema = {
        "countyName": countyName,
        "phone": phoneResult,
        "email": email,
        "officeSupervisor": officeSupervisor,
        "website": websiteResult,
        "supervisorTitle": "Supervisor"
    }
    
    if addressResult.count('FL') > 1: # there are two addresses listed
        splitAddresses = addressResult.split("     ")
        mailingAddress = " ".join(splitAddresses[1:])
        schema['mailingAddress'] = formatAddressData(mailingAddress, countyName)
        physicalAddress = formatAddressData(splitAddresses[0], countyName)
    else:
        physicalAddress = formatAddressData(addressResult, countyName)

    schema['physicalAddress'] = physicalAddress

    return schema
    
def formatAddressData(addressData, countyName):
    mapping = electionsaver.addressSchemaMapping
    # parsedDataDict = usaddress.tag(addressData, tag_mapping=mapping)[0]

    # edge cases

    # lol doctor and drive have the same abbreviation
    if countyName == "Collier":
        addressData = addressData.replace('Rev Dr', 'Reverend Doctor')
    
    # this county only has a PO Box, and I happened to click on the website
    # and find out there's an actual physical location lol.. got lucky
    if countyName == "Citrus":
        addressData = "1500 N. Meadowcrest Blvd. Crystal River, FL 34429"

    parsedDataDict = {}
    try:
        parsedDataDict = usaddress.tag(addressData, tag_mapping=mapping)[0]
    except:
        print(f'Error with data for {countyName} county, data is {parsedDataDict}')

    finalAddress = {
        "city": parsedDataDict['city'],
        "state": parsedDataDict['state'],
        "zipCode": parsedDataDict['zipCode'],
    }
    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    return finalAddress


async def get_election_offices():
    # s = scraper.get(BASE_URL)
    async with CloudflareScraper() as session:
        async with session.get(BASE_URL) as s:
            text = await s.read()
            soup = bs(text.decode("utf-8"), 'html.parser')

    testCountyData = getCountyCodesAndNames(soup)
    countyData = sorted(testCountyData, key=lambda k: k['countyName'])
    numScraped = 0
    masterList = []
    for county in countyData:
        code = county['countyCode']
        name = county['countyName']
        cleandStringAndEmail = await scrapeOneCounty(code, name)
        schema = formatDataIntoSchema(cleandStringAndEmail[0], cleandStringAndEmail[1],
                                      name)
        masterList.append(schema)
        numScraped += 1
        print(
            f'[Florida] Scraped {name} county: #{numScraped} of {len(countyData)} .... [{round((numScraped / len(countyData)) * 100, 2)}%]')

    with open(os.path.join(ROOT_DIR, r"scrapers\florida\florida.json"), 'w') as f:
        json.dump(masterList, f)


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(end - start)
