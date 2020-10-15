import asyncio
import os
import time

import aiohttp
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import usaddress

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://www.maine.gov/sos/cec/elec/munic.html"
T_FILE = (
    "https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text"
)

def format_address_data(address_data, county_name):
    if county_name == "Swans Island":
        address_data = address_data.replace("Swan'S", "Swans")
    if county_name == "Jackson":
        address_data = "730 Moosehead Trail Hwy PO Box 393 Jackson, ME 04921"

    final_address = {}
    mapping = electionsaver.addressSchemaMapping
    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    try:
        final_address = {
            "city": parsed_data_dict["city"],
            "state": "Maine",
            "zipCode": parsed_data_dict["zipCode"],
        }
    except KeyError:
        print(f"Error with data {parsed_data_dict}")

    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    return final_address


def is_mailing_address(address_schema):
    if "poBox" in address_schema and "streetNumberName" not in address_schema:
        return True
    else:
        return False


async def get_election_offices():
    url_data = pd.read_table(T_FILE, sep="|")
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html5lib")

    all_names = soup.findAll("h2")
    county_names = [i.text for i in all_names]
    county_names = county_names[2:]
    county_names.remove("Lincoln Plt")
    county_names.remove("Magalloway Plt")

    all_info = soup.findAll("dd")
    county_info = [i.text.strip("\n") for i in all_info]
    county_info = county_info

    phone_nums = []
    for i in county_info:
        phone = re.search("Phone: (.*)\nFax", i)
        if phone is None:
            phone_nums.append("None")
        else:
            phone_nums.append(phone.group(1))

    phone_num_real = [x for x in phone_nums if x != "None" and x != " NH  03579"]

    for pos, i in enumerate(phone_num_real):
        if i == "Deblois, ME  04622":
            phone_num_real[pos] = "None"

    county_info_t = pd.DataFrame(url_data)
    county_info_t = county_info_t[
        county_info_t["133 Main Road"] != "226 Wilsons Mills Road"
    ]
    init_info = county_info_t.columns.tolist()
    new_init_info = []

    for string in init_info:
        new_string = string.replace("<plaintext>Abbot", "Abbot")
        new_init_info.append(new_string)

    add1 = county_info_t["133 Main Road"].tolist()
    add2 = county_info_t["Abbot, ME  04406"].tolist()
    add1.insert(0, "133 Main Road")
    add2.insert(0, "Abbot, ME 04406")
    address = [i + " " + j for i, j in zip(add1, add2)]

    for pos, i in enumerate(address):
        if i == " Luckings Gay Route 193":
            address[pos] = "8 Lane Road, Deblois, ME 04622"

    clerk_names = county_info_t["Lorna Flint Marshall"].tolist()
    clerk_names.insert(0, "Lorna Flint Marshall")
    clerk_positions = ["Municipal Clerk"] * len(county_names)
    location_names = [i + " Municipality Election Office" for i in county_names]
    websites = ["https://www.maine.gov/sos/cec/elec/munic.html"] * len(county_names)

    master_list = []

    tmp = 0
    for i in range(len(county_names)):
        real_address = format_address_data(address[i], county_names[i])
        if "locationName" not in real_address:
            real_address["locationName"] = location_names[i]

        schema = {
            "physicalAddress": real_address,
            "phone": phone_num_real[i],
            "officeSupervisor": clerk_names[i],
            "supervisorTitle": clerk_positions[i],
            "website": websites[i],
        }

        p = percent_similarity(county_names[i], real_address["city"])
        if county_names[i] != real_address["city"]:
            if p < 40.0:
                print(
                    f'Non-abbreviated mismatch detected: {county_names[i]} and '
                    f'{real_address["city"]} | adding {county_names[i]}'
                )
                schema["cityName"] = county_names[i]
                tmp += 1

        ismailing = is_mailing_address(real_address)

        if ismailing:
            schema["mailingAddress"] = schema["physicalAddress"]
            schema.pop("physicalAddress")
        if county_names[i] == "Jackson":
            mailing = format_address_data(
                "Town of Jackson PO Box 393 Brooks, ME 04921", "Jackson Mailing"
            )
            schema["mailingAddress"] = mailing
            schema["cityName"] = "Jackson"
        master_list.append(schema)

    print(f"Replaced {tmp} discrepancies out of {len(county_names)}")

    with open(os.path.join(ROOT_DIR, "scrapers", "maine", "maine.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


def percent_similarity(str1, str2):
    if str1 == str2:
        return 100
    str1 = str1.replace("Saint", "St.")
    is_str1_longer = len(str1) <= len(str2)
    str_to_check = str1 if is_str1_longer else str2
    other_string = str2 if is_str1_longer else str1
    similarity_index = 0
    for i in range(len(str_to_check)):
        if str_to_check[i] == other_string[i]:
            similarity_index += 1
    return 100 * (similarity_index / len(other_string))

def percentSimilarity(str1, str2):
    if str1 == str2:
        return 100
    str1 = str1.replace('Saint', 'St.')
    isStr1Longer = len(str1) <= len(str2)
    strToCheck = str1 if isStr1Longer else str2
    otherString = str2 if isStr1Longer else str1
    similarityIndex = 0
    for i in range(len(strToCheck)):
        if strToCheck[i] == otherString[i]:
            similarityIndex +=1
    return 100 * (similarityIndex/len(otherString))

if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
