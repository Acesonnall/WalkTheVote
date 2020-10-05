import asyncio
import os
import time
from asyncio import Task
from asyncio.futures import Future
from typing import List, Any, Tuple

import cloudscraper
from bs4 import BeautifulSoup as bS
import re
import json
import usaddress
from aiocfscrape import CloudflareScraper
from string import printable

import context
from definitions import ROOT_DIR, bcolors
from ElectionSaver import electionsaver
from errors.wtv_errors import WalkTheVoteError

REGISTRAR_URL = "https://elections.sos.ga.gov/Elections/countyregistrars.do"
INFO_URL = "https://elections.sos.ga.gov/Elections/contactinfo.do"


def format_address_data(address_data, county_name, is_physical, mailing_addr={}):
    mapping = electionsaver.addressSchemaMapping
    
    parsed_data_dict = {}
    try:
        parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]
    except Exception as e:
        raise WalkTheVoteError(
            f"Error with data for {county_name} county, data is {parsed_data_dict}"
        ) from e

    final_address = {}

    # Sometimes info is only in mailing address, if data is missing in physical, add the info from mailing
    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"]
    elif is_physical and "city" in mailing_addr:
        final_address["city"] = mailing_addr["city"]
    
    if "state" in parsed_data_dict:
        final_address["state"] = parsed_data_dict["state"]
    elif is_physical and "state" in mailing_addr:
        final_address["state"] = mailing_addr["state"]

    if "zipCode" in parsed_data_dict:
        final_address["zipCode"] = parsed_data_dict["zipCode"]
    elif is_physical and "zipCode" in mailing_addr:
        final_address["zipCode"] = mailing_addr["zipCode"]

    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    elif is_physical and "streetNumberName" in mailing_addr:
        final_address["streetNumberName"] = mailing_addr["streetNumberName"]

    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    elif is_physical and "locationName" in mailing_addr:
        final_address["locationName"] = mailing_addr["locationName"]

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    elif is_physical and "aptNumber" in mailing_addr:
        final_address["aptNumber"] = mailing_addr["aptNumber"]

    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    return final_address


def format_address_html(info_str):
    info_str = info_str.replace("\n<br/>", " ")
    info_str = info_str.replace("<br/>\n", " ")
    info_str = info_str.replace("<br/>", " ")

    start_ind = info_str.index("</h4>") + 5
    end_ind = info_str.index("</td>")

    address = info_str[start_ind:end_ind].strip()
    address = address.replace("\n", ", ")
    address = address.replace("  ", " ")

    return address


def get_phone_number(info_str):
    phone_num_index = info_str.index("Telephone: ") + len("Telephone: ")

    phone_num = []
    for c in info_str[phone_num_index:]:
        if str.isdigit(c):
            phone_num.append(c)
        elif c in ["(", ")", "-", " "]:
            phone_num.append(c)
        else:
            break

    return "".join(phone_num)


def get_county_registrar(info_str):
    registrar_index = info_str.index("County Chief Registrar") + len("County Chief Registrar")
    registrar_name = []

    for c in info_str[registrar_index:]:
        if c == "\n":
            break
        else:
            registrar_name.append(c)
        
        return "".join(registrar_name).strip()


# function to decode hexadecimal email strings
# lifted this off some stackoverflow post lol
async def scrape_one_county(session, county_id, county_name):
    data = {"idTown": county_id, "SubmitCounty": "Submit", "contactType": "R"}
    async with session.post(INFO_URL, data=data) as s:
        text = await s.read()
        soup = bS(text, "html5lib")

    table = soup.find("table", {"id": "Table1"})
    rows = table.find_all("tr")

    # Get county registsrar name
    registrar_name = ""
    if "County Chief Registrar" in rows[0].getText():
        registrar_name = get_county_registrar(rows[0].getText())

    # Get mailing and physical addresses
    phys_address, mail_address = "", ""

    if ("Physical Address:" in rows[0].getText() and "SAME AS ABOVE" not in rows[0].getText()):
        phys_info_str = str(rows[0])
        phys_address = format_address_html(phys_info_str)

    mail_info_str = str(rows[1])
    mail_address = format_address_html(mail_info_str)

    # Get phone number
    phone_number = ""
    if "Telephone: " in rows[2].getText():
        contact_info_str = rows[2].getText()
        phone_number = get_phone_number(contact_info_str)
    
    # Get Email
    email_address = ""
    email = soup.find("span", class_="__cf_email__")
    if email is not None:
        hex_email = email["data-cfemail"]
        email_address = electionsaver.decodeEmail(hex_email)
    
    return registrar_name, phys_address, mail_address, phone_number, email_address, county_name


def format_data_into_schema(registrar_name, phys_address, mail_address, phone_number, email_address, county_name):
    schema = {
        "countyName": county_name,
        "phone": phone_number,
        "email": email_address,
        "officeSupervisor": registrar_name,
        "website": INFO_URL,
        "supervisorTitle": "County Chief Registrar"
    }

    mailing_address_formatted = {}
    if mail_address != "":
        mailing_address_formatted = format_address_data(mail_address, county_name, False)
        schema["mailingAddress"] = mailing_address_formatted
        
    if phys_address != "":
        schema["physicalAddress"] = format_address_data(phys_address, county_name, True, mailing_address_formatted)

    return schema


async def get_georgia_election_offices():
    """ Starting point of the scraper program. Scrapes BASE_URL for election office
    information and both dumps results to a .json file and returns the results as json.

    @return: list of scraped results as json.
    """
    # Get list of county names from registrar to populate form
    # Define coroutine functions (context managers)
    async with CloudflareScraper() as session:
        async with session.get(REGISTRAR_URL) as s:
            # ClientResponse.read() is a coroutine function so it must be awaited
            text = await s.read()
        soup = bS(text, "html5lib")

        county_option_list = soup.findAll(attrs={"name": "idTown"})[0].findAll("option")

        id_list = [county_option["value"] for county_option in county_option_list]
        county_list = [county_option.string for county_option in county_option_list]

        # Use list of counties and IDs to get county info for each county
        tasks: List[Task] = []
        num_scraped = 0
        master_list = []

        for i in range(len(id_list)):
            county_id = id_list[i]
            county_name = county_list[i]

            # Create task for a future asynchronous operation and store it in task list
            tasks.append(asyncio.create_task(scrape_one_county(session, county_id, county_name)))
        
        # Run the coroutines and iterate over the yielded results as they complete
        # (out-of-order). Use asyncio.gather() with a couple code modifications to
        # preserve list order
        future: Future[Tuple[str, str, str, str, str, str]]
        for future in asyncio.as_completed(tasks):
            # Unpack awaited result of scrape_one_county()
            registrar_name, phys_address, mail_address, phone_number, email_address, county_name = await future
            schema = format_data_into_schema(
                registrar_name, phys_address, mail_address, phone_number, email_address, county_name
            )
            master_list.append(schema)
            num_scraped += 1
            print(
                f"[Georgia] Scraped {county_name} county: "
                f"#{num_scraped} of {len(county_list)} .... "
                f"[{round((num_scraped / len(county_list)) * 100, 2)}%]"
            )

    with open(os.path.join(ROOT_DIR, r"scrapers\georgia\georgia.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_georgia_election_offices())
    end = time.time()
    print(f"{bcolors.OKBLUE}Completed in {end - start} seconds.{bcolors.ENDC}")
