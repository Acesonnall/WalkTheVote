import asyncio
import json
import os
import re
import time

import aiohttp
import usaddress
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://www.sos.state.mn.us/elections-voting/find-county-election-office/#"


# regex to find urls in strings
def find(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]


def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping

    if county_name == "Crow Wing":
        address = "Historic Courthouse 326 Laurel St Ste 22 Brainerd, MN 56401"
    if county_name == "Saint Louis":
        address = address.replace("St. Louis", "Saint Louis")
    if county_name == "Marshall":
        address = "208 E Colvin Ave, Ste 11 Warren, MN 56762"
    if county_name == "Anoka":
        address = "2100 3rd Ave, Suite W130 Anoka, MN 55303-5031"

    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    final_address = {
        "state": "Minnesota",
        "zipCode": parsed_data_dict["zipCode"],
    }
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
        if county_name == "Mower":
            final_address["streetNumberName"] = "500 4th Ave NE"
        if county_name == "Sherburne":
            final_address["streetNumberName"] = "13880 Business Center Drive NW"
        if county_name == "Watonwan":
            final_address["streetNumberName"] = "710 2nd Ave S"
    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"]
        if county_name == "Mower":
            final_address["city"] = "Austin"
        if county_name == "Watonwan":
            final_address["city"] = "Saint James"
    else:
        if county_name == "Lincoln":
            final_address["city"] = "Ivanhoe"
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
        if county_name == "Lincoln":
            final_address["poBox"] = "PO Box 29"
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
        if county_name == "Marshall":
            final_address["locationName"] = "Marshall County Election Office"
        if county_name == "Sherburne":
            final_address["locationName"] = "Sherburne County Government Center"
        if county_name == "Watonwan":
            final_address["locationName"] = "Watonwan County Courthouse"
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    return final_address


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html5lib")

    # putting all county names in a list
    county_names = soup.find_all("h2", class_="contentpage-h2")

    name = []
    for i in county_names:
        name.append(i.text.replace("County", "").strip())

    county_info = soup.find_all("div", class_="collapse")
    county_info_text = []
    for i in county_info:
        county_info_text.append(i.text)

    email_add = []
    off_name = []
    phone = []
    addies = []

    for i in county_info_text:
        elec_name = re.search("Election official: (.*)General phone", i)
        off_name.append(elec_name.group(1).strip("\xa0"))
        email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", i)
        email_add.append(email.group(0))
        if "General Phone" in i:
            phone_num = re.search("General phone: (.*) Fax", i)
        else:
            phone_num = re.search("Phone: (.*)Fax", i)
        if "\nStreet address" in i:
            address = re.search("\nStreet address\n(.*)\nMailing address", i)
        elif "\nAddress\n" in i:
            address = re.search("\nAddress\n(.*)\nAbsentee", i)
        else:
            address = re.search("\nMailing Address\n(.*)\n", i)
        if phone_num is None:
            phone.append("None")
        else:
            phone.append(phone_num.group(1).strip("\xa0").strip())
        if address is None:
            addies.append("None")
        else:
            addies.append(address.group(1))

    real_add = [
        "Olmsted County Elections 2122 Campus Dr SE Rochester, MN 55904",
        "Scott County Public Works 600 Country Trail E Jordan, MN 55352",
        "Stearns County Service Center 3301 County Road 138 Waite Park, MN 56387",
        "Winona County Auditor-Treasurer 202 W Third St Winona, MN 55987",
    ]

    counter = 0
    for pos, i in enumerate(addies):
        if i == "None":
            addies[pos] = real_add[counter]
            counter += 1

    loc_name = [i + " County Election Office" for i in name]

    websites = [find(i) for i in county_info_text]
    websites = [item for sublist in websites for item in sublist]

    master_list = []

    for i in range(len(name)):
        real_address = format_address_data(addies[i], name[i])
        if "locationName" not in real_address:
            real_address["locationName"] = loc_name[i]

        schema = {
            "countyName": name[i],
            "physicalAddress": real_address,
            "phone": phone[i],
            "email": email_add[i],
            "officeSupervisor": off_name[i],
            "website": websites[i],
        }
        master_list.append(schema)

    with open(
        os.path.join(ROOT_DIR, "scrapers", "minnesota", "minnesota.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
