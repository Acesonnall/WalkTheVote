import asyncio
import os
<<<<<<< HEAD
<<<<<<< HEAD
import time

import aiohttp
=======
=======
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
import sys
import time

import aiohttp
import requests
<<<<<<< HEAD
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
=======
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
from bs4 import BeautifulSoup
import json
import usaddress


<<<<<<< HEAD
<<<<<<< HEAD
from lib.ElectionSaver import electionsaver
from lib.definitions import bcolors, ROOT_DIR
=======
from ElectionSaver import electionsaver
from definitions import bcolors
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
=======
from ElectionSaver import electionsaver
from definitions import bcolors
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?


def formatAddressData(addressData, countyName):
    mapping = electionsaver.addressSchemaMapping
    if countyName == "MITCHELL":
        addressData = addressData.replace("108BAKERSVILLE", "108 BAKERSVILLE")
    if countyName == "BURKE":
        addressData = addressData.replace("100MORGANTON", "100 MORGANTON")
    if countyName == "JACKSON":
        addressData = addressData.replace("1SYLVA", "1 SYLVA")
    if countyName == "ROWAN":
        addressData = addressData.replace("D10SALISBURY", "D10 SALISBURY")
    if countyName == "SAMPSON":
        addressData = addressData.replace("110CLINTON", "110 CLINTON")
    if countyName == "YANCEY":
        addressData = addressData.replace("2BURNSVILLE", "2 BURNSVILLE")

    parsedDataDict = usaddress.tag(addressData, tag_mapping=mapping)[0]

    finalAddress = {
        "city": parsedDataDict["city"],
        "state": parsedDataDict["state"],
        "zipCode": parsedDataDict["zipCode"],
    }

    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"]
<<<<<<< HEAD

    finalAddress["locationName"] = parsedDataDict.get(
        "locationName", f"{countyName} County Election Office"
    )
=======
    if "locationName" in parsedDataDict:
        finalAddress["locationName"] = parsedDataDict["locationName"]
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
    if "aptNumber" in parsedDataDict:
        finalAddress["aptNumber"] = parsedDataDict["aptNumber"]
    if "poBox" in parsedDataDict:
        finalAddress["poBox"] = parsedDataDict["poBox"]
    return finalAddress


URL = "https://vt.ncsbe.gov/BOEInfo/PrintableVersion/"


def renameKey(src, dest, all_elems_js):
    for element in all_elems_js:
        element[dest] = element[src]
        element.pop(src)


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
<<<<<<< HEAD
<<<<<<< HEAD
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html.parser")
=======
=======
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
        soup = None
        async with session.get(URL) as r:
            # r = requests.get(BASE_URL, verify=False)
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html.parser")
    # r = requests.get(URL)
    # soup = BeautifulSoup(r.content, "html.parser")
<<<<<<< HEAD
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
=======
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
    all_elems = soup.find_all("script")
    test = str(all_elems[16]).split("var data = ")[1].split("// initialize")[0]
    json.loads(test)
    all_elems_js = json.loads(test)
    to_del = [
        "Coordinates",
        "CountyId",
        "MapLink",
        "OfficeName",
        "OfficePhoneNumExt",
        "MailingAddr1",
        "MailingAddr2",
        "MailingAddrCSZ",
    ]
    for element in all_elems_js:
        [element.pop(key) for key in to_del]
        newAddy = (
<<<<<<< HEAD
<<<<<<< HEAD
            element["PhysicalAddr1"]
            + " "
            + element["PhysicalAddr2"]
            + element["PhysicalAddrCSZ"]
=======
=======
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
                element["PhysicalAddr1"]
                + " "
                + element["PhysicalAddr2"]
                + element["PhysicalAddrCSZ"]
<<<<<<< HEAD
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
=======
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
        )
        cleanedData = formatAddressData(newAddy, element["Name"])
        element["newAddress"] = cleanedData
    renameKey("Name", "countyName", all_elems_js)
    renameKey("newAddress", "physicalAddress", all_elems_js)
    renameKey("OfficePhoneNum", "phone", all_elems_js)
    renameKey("Email", "email", all_elems_js)
    renameKey("OfficeHours", "officeHours", all_elems_js)
    renameKey("DirectorName", "officeSupervisor", all_elems_js)
    renameKey("WebsiteAddr", "website", all_elems_js)
    addr_del = ["PhysicalAddr1", "PhysicalAddr2", "PhysicalAddrCSZ", "FaxNum"]
    for element in all_elems_js:
        [element.pop(key) for key in addr_del]
<<<<<<< HEAD
<<<<<<< HEAD
    with open(
        os.path.join(ROOT_DIR, r"scrapers\north_carolina\north_carolina.json"), "w"
    ) as f:
=======
    with open("north_carolina.json", "w") as f:
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
=======
    with open("north_carolina.json", "w") as f:
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
        json.dump(all_elems_js, f)
    return all_elems_js


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{bcolors.OKBLUE}Completed in {end - start} seconds.{bcolors.ENDC}")
