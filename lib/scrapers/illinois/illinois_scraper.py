import asyncio
import time

import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import usaddress
import os

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR, Bcolors

URL = "https://www.elections.il.gov/ElectionOperations/ElectionAuthoritiesPrint.aspx?T=637353549301694642"

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Illinois",
        "zipCode": parsedDataDict["zipCode"],
    }
    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"].title()
    else:
        if countyName == "Cumberland":
            finalAddress["streetNumberName"] = "140 COURTHOUSE SQUARE".title()
        if countyName == "Mason":
            finalAddress["streetNumberName"] = "100 NORTH BROADWAY".title()
    if "city" in parsedDataDict:
        finalAddress["city"] = parsedDataDict["city"].title()
        if countyName == "Mason":
            finalAddress["city"] = "HAVANA".title()
    if "poBox" in parsedDataDict:
        finalAddress["poBox"] = parsedDataDict["poBox"]
        if countyName == "Cumberland":
            finalAddress["poBox"] = 'PO BOX 146'.title()
        if countyName == "Mason":
            finalAddress["poBox"] = "PO BOX 77".title()
    if "locationName" in parsedDataDict:
        finalAddress["locationName"] = parsedDataDict["locationName"]
    if "aptNumber" in parsedDataDict:
        finalAddress["aptNumber"] = parsedDataDict["aptNumber"].title()
    return finalAddress


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html.parser")

    all_names = soup.findAll('td', attrs={"width": "15%"})
    all_clerks = soup.findAll('td', attrs={"width": "10%"})
    clerk_names = [i.text for i in all_clerks][:-32]
    all_emails = soup.findAll('td', attrs={"width": "25%"})
    all_add = soup.findAll('td', attrs={"width": "20%"})

    county_names = [i.text.capitalize() for i in all_names][:-8]
    loc_names = [i + ' County Election Office' for i in county_names]
    emails = [i.text for i in all_emails][:-8]
    addies = [str(i) for i in all_add][:-8]

    clerk_positions = clerk_names[1::4]
    clerks = clerk_names[::4]
    phone_nums = clerk_names[2::4]

    addies = [i.split('"20%">')[1].replace('<br/>', ' ').replace('</td>', '').replace(
        ' &amp;', '-') for i in addies]

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

    websites = [
                   "https://www.elections.il.gov/ElectionOperations/ElectionAuthoritiesPrint.aspx?T=637353549301694642"] * len(
        county_names)

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
            "officeSupervisor": clerks[i].title(),
            "supervisorTitle": clerk_positions[i].title(),
            "website": websites[i],
        }
        masterList.append(schema)

    with open(os.path.join(ROOT_DIR, "scrapers", "illinois", "illinois.json"),
              "w") as f:
        json.dump(masterList, f)
    return masterList


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
