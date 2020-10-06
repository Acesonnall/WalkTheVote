import asyncio
import os
import time

import aiohttp
import pandas as pd
import json
import usaddress

from lib.ElectionSaver import electionsaver
from lib.definitions import bcolors, ROOT_DIR

BASE_URL = "https://www.sos.state.tx.us/elections/forms/election-duties-1.xlsx"


def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    if countyName == 'Knox':
        address = '100 W Cedar St, Benjamin, TX 79505'
    if countyName == 'Live oak':
        address = '301 E Houston St George West, TX 78022'
    if countyName == 'Kleberg':
        address = address + ' 78364'
    if countyName == 'Stephens':
        address = address.replace('Courthouse', '')
    if countyName == 'Borden':
        address = '117 Wasson Rd, Gail, TX 79738'

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Texas",
        "is_mailing": False
    }
    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'city' in parsedDataDict:
        finalAddress['city'] = parsedDataDict['city']
    if 'zipCode' in parsedDataDict:
        finalAddress['zipCode'] = parsedDataDict['zipCode']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    return finalAddress


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as r:
            texas_boe = pd.read_excel(await r.read())

    texas_boe = texas_boe.drop(
        ['Mailing Address', 'Secondary Email', 'Fax', 'County Email Addresses',
         'Primary Email '], axis=1)

    county_names = []
    for i in texas_boe['County']:
        county_names.append(i.replace(' COUNTY', '').capitalize())

    location_names = []
    for i in county_names:
        loc_n = i + ' County Election Office'
        location_names.append(loc_n)

    websites = ['https://www.sos.state.tx.us/elections/voter/county.shtml'] * len(
        county_names)

    real_add = []
    tx_string = ['TX', 'tx', 'Tx', 'Texas']

    for i in texas_boe['Physical Address']:
        if all(t not in i for t in tx_string):
            if i[-5] == '-':
                addy = i[:-11] + ' TX ' + i[-10:]
            else:
                addy = i[:-6] + ' TX ' + i[-5:]
        else:
            addy = i
        real_add.append(addy.replace('\n', ' '))

    masterList = []

    for i in range(len(county_names)):
        real_address = formatAddressData(real_add[i], county_names[i])
        if 'locationName' not in real_address:
            real_address['locationName'] = location_names[i]
        schema = {
            "countyName": county_names[i],
            "physicalAddress": real_address,
            "phone": texas_boe['Phone '][i],
            "officeSupervisor": texas_boe['Name'][i],
            "supervisorTitle": texas_boe['Postion'][i],
            "website": websites[i]
        }
        masterList.append(schema)

    with open(os.path.join(ROOT_DIR, r"scrapers\texas\texas.json"), 'w') as f:
        json.dump(masterList, f)
    return masterList


if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{bcolors.OKBLUE}Completed in {end - start} seconds.{bcolors.ENDC}")
