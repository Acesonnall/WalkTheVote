import asyncio
import os
import time

import aiohttp
from bs4 import BeautifulSoup
import json
import usaddress


from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR


def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping
    if county_name == "MITCHELL":
        address_data = address_data.replace("108BAKERSVILLE", "108 BAKERSVILLE")
    if county_name == "BURKE":
        address_data = address_data.replace("100MORGANTON", "100 MORGANTON")
    if county_name == "JACKSON":
        address_data = address_data.replace("1SYLVA", "1 SYLVA")
    if county_name == "ROWAN":
        address_data = address_data.replace("D10SALISBURY", "D10 SALISBURY")
    if county_name == "SAMPSON":
        address_data = address_data.replace("110CLINTON", "110 CLINTON")
    if county_name == "YANCEY":
        address_data = address_data.replace("2BURNSVILLE", "2 BURNSVILLE")

    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    final_address = {
        "city": parsed_data_dict["city"],
        "state": parsed_data_dict["state"],
        "zipCode": parsed_data_dict["zipCode"],
    }

    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]

    final_address["locationName"] = parsed_data_dict.get(
        "locationName", f"{county_name} County Election Office"
    )
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    return final_address


URL = "https://vt.ncsbe.gov/BOEInfo/PrintableVersion/"


def rename_key(src, dest, all_elems_js):
    for element in all_elems_js:
        element[dest] = element[src]
        element.pop(src)


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html.parser")
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
        new_addy = (
            element["PhysicalAddr1"]
            + " "
            + element["PhysicalAddr2"]
            + element["PhysicalAddrCSZ"]
        )
        cleaned_data = format_address_data(new_addy, element["Name"])
        element["newAddress"] = cleaned_data
    rename_key("Name", "countyName", all_elems_js)
    rename_key("newAddress", "physicalAddress", all_elems_js)
    rename_key("OfficePhoneNum", "phone", all_elems_js)
    rename_key("Email", "email", all_elems_js)
    rename_key("OfficeHours", "officeHours", all_elems_js)
    rename_key("DirectorName", "officeSupervisor", all_elems_js)
    rename_key("WebsiteAddr", "website", all_elems_js)
    addr_del = ["PhysicalAddr1", "PhysicalAddr2", "PhysicalAddrCSZ", "FaxNum"]
    for element in all_elems_js:
        [element.pop(key) for key in addr_del]
    with open(
        os.path.join(ROOT_DIR, "scrapers", "north_carolina", "north_carolina.json"), "w"
    ) as f:
        json.dump(all_elems_js, f)
    return all_elems_js


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
