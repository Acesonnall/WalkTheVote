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

URL = "https://www.sos.ca.gov/elections/voting-resources/county-elections-offices/"


def rem_dups(add, real_add):
    for i in add:
        if i not in real_add:
            real_add.append(i)


# regex to find urls
def find(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]


def format_address_data(address, county_name):
    final_address = {}
    mapping = electionsaver.addressSchemaMapping
    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    try:
        final_address = {
            "city": parsed_data_dict["city"],
            "state": "California",
            "zipCode": parsed_data_dict["zipCode"],
        }
    except KeyError:
        print(f"Error with data for {county_name} county, data is {parsed_data_dict}")

    return final_address


def format_street_number(street_number_name, county_name):
    mapping = electionsaver.addressSchemaMapping

    if county_name == "Glenn":
        street_number_name = street_number_name.replace(", 2nd Street", "")

    parsed_data_dict = usaddress.tag(street_number_name, tag_mapping=mapping)[0]

    final_address = {"locationName": f"{county_name} County Election Office"}

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]

    if county_name == "San Francisco":
        final_address = {
            "streetNumberName": "1 Dr. Carlton B Goodlett Place",
            "locationName": "City Hall",
            "aptNumber": "Room 48",
        }

    # print(f'Error with data for {countyName} county, data is {parsed_data_dict}')

    return final_address


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html5lib")

    all_names = soup.findAll("h2")
    county_names = [i.text.strip("\xa0") for i in all_names]
    county_names = county_names[:-4]

    all_info = soup.findAll("li")
    county_info = [i.text.strip("\xa0") for i in all_info]
    county_info = county_info

    no_emails = ["Alameda", "Sutter", "Ventura"]
    no_email_index = [county_names.index(i) for i in no_emails]
    emails = [
        i.strip("E-Mail:").replace("\xa0", "").strip() for i in county_info if "@" in i
    ]
    for i in no_email_index:
        emails.insert(i, "None")

    phone = [
        i.strip()
        for i in county_info
        if "(" in i
        and "Fax" not in i
        and "(800)" not in i
        and "(888)" not in i
        and "Library" not in i
        and "Hall" not in i
        and "(916) 375-6490" not in i
        and "(866)" not in i
    ]

    ind_la = county_names.index("Los Angeles")
    phone.insert(ind_la, "(800) 815-2666")

    phone_num = [i[:14] for i in phone]

    hours = [
        i.strip("Hours: ").strip("(707) 263-2742 FaxHours:").strip("\n\t")
        for i in county_info
        if "Hours: " in i
    ]

    add_id = [
        "Street",
        "Road",
        "Ave",
        "Court ",
        "lane",
        "Blvd",
        "Hwy",
        "Drive",
        "Place",
        "St.",
        "Real",
        "Square",
        "Memorial",
    ]

    addresses = []
    real_addresses = []
    for i in county_info:
        for j in add_id:
            if j in i and "CA" not in i:
                addresses.append(i)

    rem_dups(addresses, real_addresses)
    real_addresses.remove("Placer")

    add_index = []
    real_add_index = []
    for i in real_addresses:
        for j in county_info:
            if i == j:
                add_index.append(county_info.index(j))

    rem_dups(add_index, real_add_index)

    real_add_index_2 = [i + 1 for i in real_add_index]
    real_addresses_2 = [county_info[i] for i in real_add_index_2]
    replace_adds = [
        "Martinez, CA 94553",
        "San Francisco, CA 94102-4635",
        "Downieville, CA 95936-0398",
        "Ventura, CA 93009-1200",
    ]

    counter = 0
    for pos, i in enumerate(real_addresses_2):
        if "CA" not in i:
            real_addresses_2[pos] = replace_adds[counter]
            counter += 1

    clerks = [
        i.replace("\xa0", "")
        for i in county_info
        if "," in i
        and "CA" not in i
        and "Room" not in i
        and "Suite" not in i
        and "Street" not in i
        and "Hours" not in i
        and "Floor" not in i
        and "Drive" not in i
        and "Avenue" not in i
        and "option" not in i
        and "Hall" not in i
    ]

    clerk_name = [i.split(",")[0] for i in clerks]
    clerk_position = [i.split(",")[1].strip() for i in clerks]

    websites = [find(i) for i in county_info]
    websites = [item for sublist in websites for item in sublist]

    ind_orange = county_names.index("Orange")
    ind_placer = county_names.index("Placer")

    websites.insert(ind_orange, "https://www.ocvote.com/")
    websites.insert(ind_placer, "https://www.placerelections.com/")

    master_list = []

    for i in range(len(county_names)):
        address_schema = format_address_data(real_addresses_2[i], county_names[i])
        strestreet_sub_schemat_sub_schema = format_street_number(
            real_addresses[i], county_names[i]
        )
        if "streetNumberName" in strestreet_sub_schemat_sub_schema:
            address_schema["streetNumberName"] = strestreet_sub_schemat_sub_schema[
                "streetNumberName"
            ]
        if "aptNumber" in strestreet_sub_schemat_sub_schema:
            address_schema["aptNumber"] = strestreet_sub_schemat_sub_schema["aptNumber"]
        if "locationName" in strestreet_sub_schemat_sub_schema:
            address_schema["locationName"] = strestreet_sub_schemat_sub_schema[
                "locationName"
            ]
        schema = {
            "countyName": county_names[i],
            "physicalAddress": address_schema,
            "phone": phone_num[i],
            "officeSupervisor": clerk_name[i],
            "supervisorTitle": clerk_position[i],
            "email": emails[i],
            "website": websites[i],
        }

        no_emails_local = ["Merced", "Alameda", "Ventura", "Sutter"]
        if county_names[i] in no_emails_local:
            schema.pop("email")

        master_list.append(schema)

    # print(masterList)

    with open(
        os.path.join(ROOT_DIR, "scrapers", "california", "california.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
