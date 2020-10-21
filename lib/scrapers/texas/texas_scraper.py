import asyncio
import os
import time

import aiohttp
import pandas as pd
import json
import usaddress
from bs4 import BeautifulSoup as BSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

BASE_URL = "https://www.sos.state.tx.us/elections/forms/election-duties-1.xlsx"

EMAIL_URL = "https://www.sos.state.tx.us/elections/voter/county.shtml"

emails = []

async def get_email_addresses():
    async with aiohttp.ClientSession() as session:
        async with session.get(EMAIL_URL) as r:
            text = await r.read()
            soup = BSoup(text.decode("utf-8"), "html.parser")
        alinks = soup.findAll("a")
        for a in alinks:
            if "County Email Address" in a.text:
                href = a["href"]
                href = href.replace("mailto:", "")
                href = href.replace("maito:", "")  # bc ofc this is necessary
                href = href.split(";")[0].strip()
                emails.append(href)


def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping

    if county_name == "Knox":
        address = "100 W Cedar St, Benjamin, TX 79505"
    if county_name == "Live Oak":
        address = "301 E Houston St George West, TX 78022"
    if county_name == "Kleberg":
        address = address + " 78364"
    if county_name == "Parker":
        address = "1112 Santa Fe Drive Weatherford, TX 76086"
    if county_name == "Stephens":
        address = address.replace("Courthouse", "")
    if county_name == "Borden":
        address = "117 Wasson Rd, Gail, TX 79738"

    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    final_address = {"state": "Texas"}
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"]
    if "zipCode" in parsed_data_dict:
        final_address["zipCode"] = parsed_data_dict["zipCode"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    return final_address


async def get_election_offices():
    # Moved the below function call here since the db handler needs the everything to be
    # prepared by the time get_election_offices finishes.
    # TODO: Reconfigure to prevent get_email_address from being I/O blocking
    await get_email_addresses()
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as r:
            texas_boe = pd.read_excel(await r.read())

    texas_boe = texas_boe.drop(
        ["Mailing Address", "Secondary Email", "Fax", "Primary Email "], axis=1
    )

    county_names = texas_boe["County"].str.replace(" COUNTY", "").str.title()

    location_names = []
    for i in county_names:
        loc_n = i + " County Election Office"
        location_names.append(loc_n)

    websites = ["https://www.sos.state.tx.us/elections/voter/county.shtml"] * len(
        county_names
    )

    real_add = []
    tx_string = ["TX", "tx", "Tx", "Texas"]

    for i in texas_boe["Physical Address"]:
        if all(t not in i for t in tx_string):
            if i[-5] == "-":
                addy = i[:-11] + " TX " + i[-10:]
            else:
                addy = i[:-6] + " TX " + i[-5:]
        else:
            addy = i
        real_add.append(addy.replace("\n", " "))

    master_list = []

    for i in range(len(county_names)):
        real_address = format_address_data(real_add[i], county_names[i])
        if "locationName" not in real_address:
            real_address["locationName"] = location_names[i]
        # print(f'County Name: {county_names[i]} | Email: {emails[i]}')
        schema = {
            "countyName": county_names[i],
            "physicalAddress": real_address,
            "phone": texas_boe["Phone "][i],
            "email": emails[i],
            "officeSupervisor": texas_boe["Name"][i],
            "supervisorTitle": texas_boe["Postion"][i],
            "website": websites[i],
        }
        master_list.append(schema)

    with open(os.path.join(ROOT_DIR, "scrapers", "texas", "texas.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
