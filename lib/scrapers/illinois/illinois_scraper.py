import requests
from bs4 import BeautifulSoup
import re
import json
import usaddress
from lib.ElectionSaver import electionsaver
from lib.definitions import bcolors, ROOT_DIR
import os

URL = "https://www.elections.il.gov/ElectionOperations/ElectionAuthoritiesPrint.aspx?T=637353549301694642"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

all_names = soup.findAll('td', attrs={"width":"15%"})
all_clerks = soup.findAll('td', attrs={"width":"10%"})
clerk_names = [i.text for i in all_clerks][:-32]
all_emails = soup.findAll('td', attrs={"width":"25%"})
all_add = soup.findAll('td', attrs={"width":"20%"})

county_names = [i.text.capitalize() for i in all_names][:-8]
loc_names = [i + ' County Election Office' for i in county_names]
emails = [i.text for i in all_emails][:-8]
addies = [str(i) for i in all_add][:-8]

clerk_positions = clerk_names[1::4]
clerks = clerk_names[::4]
phone_nums = clerk_names[2::4]

addies = [i.split('"20%">')[1].replace('<br/>', ' ').replace('</td>', '').replace(' &amp;', '-') for i in addies]

rem_ind = []
for pos, i in enumerate(clerk_positions):
    if i == 'ELECTION DIVISION':
        rem_ind.append(pos)

for i in reversed(rem_ind):
    del county_names[i]
    del emails[i]
    del addies[i]
    del phone_nums[i]
    del clerks[i]
    del clerk_positions[i]
    del loc_names[i]

websites = ["https://www.elections.il.gov/ElectionOperations/ElectionAuthoritiesPrint.aspx?T=637353549301694642"] * len(county_names)

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Illinois",
        "zipCode": parsedDataDict["zipCode"],
    }
    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"]
    else:
        if countyName == "Cumberland":
            finalAddress["streetNumberName"] = "140 COURTHOUSE SQUARE"
        if countyName == "Mason":
            finalAddress["streetNumberName"] = "100 NORTH BROADWAY"
    if "city" in parsedDataDict:
        finalAddress["city"] = parsedDataDict["city"]
        if countyName == "Mason":
            finalAddress["city"] = "HAVANA"
    if "poBox" in parsedDataDict:
        finalAddress["poBox"] = parsedDataDict["poBox"]
        if countyName == "Cumberland":
            finalAddress["poBox"] = 'PO BOX 146'
        if countyName == "Mason":
            finalAddress["poBox"] = "PO BOX 77"
    if "locationName" in parsedDataDict:
        finalAddress["locationName"] = parsedDataDict["locationName"]
    if "aptNumber" in parsedDataDict:
        finalAddress["aptNumber"] = parsedDataDict["aptNumber"]
    return finalAddress

masterList = []

for i in range(len(county_names)):
    real_address = formatAddressData(addies[i], county_names[i])
    if "locationName" not in real_address:
        real_address["locationName"] = loc_names[i]

    schema = {
        "countyName": county_names[i],
        "physicalAddress": real_address,
        "phone": phone_nums[i],
        "email": emails[i],
        "officeSupervisor": clerks[i],
        "supervisorTitle": clerk_positions[i],
        "website": websites[i],
    }
    masterList.append(schema)

with open(os.path.join(ROOT_DIR, "scrapers", "illinois", "illinois.json"), "w") as f:
    json.dump(masterList, f)