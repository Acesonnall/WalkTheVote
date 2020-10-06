import asyncio
import os
import time
from asyncio import Task
from asyncio.futures import Future
<<<<<<< HEAD
from typing import List, Tuple
=======
from typing import List, Any, Tuple
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?

import cloudscraper
from bs4 import BeautifulSoup as bS
import re
import json
import usaddress
from aiocfscrape import CloudflareScraper
from string import printable

<<<<<<< HEAD
from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR, bcolors
from lib.errors.wtv_errors import WalkTheVoteError
=======
from ElectionSaver import electionsaver
from definitions import ROOT_DIR, bcolors
from errors.wtv_errors import WalkTheVoteError
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?

BASE_URL = "https://dos.elections.myflorida.com/supervisors/"

scraper = cloudscraper.create_scraper()


def get_county_codes_and_names(soup):
    url_elems = soup.find_all("li")
    res = []
    for url in url_elems:
        a = url.find("a")
        href = a["href"]
        if "county" in href:
            county_data = {"countyCode": href.split("=")[1], "countyName": a.text}
            res.append(county_data)
    return res


# function to decode hexadecimal email strings
# lifted this off some stackoverflow post lol
async def scrape_one_county(session, county_code, county_name):
    url = BASE_URL + "countyInfo.asp?county=" + county_code
    # s = scraper.get(url)
    async with session.get(url) as s:
        text = await s.read()
        soup = bS(text.decode("utf-8"), "html.parser")

    # relevant info is in a random <p> with no classes
    county_info = soup.find("p", attrs={"class": None}).text
    hex_email = soup.find("span", class_="__cf_email__")["data-cfemail"]

    # clean up \t \r \n tags from string
    example = {"\t": None, "\n": " ", "\r": None}
    table = county_info.maketrans(example)
    cleaned = county_info.translate(table)

    return cleaned, hex_email, county_code, county_name


def format_data_into_schema(cleaned_data, hex_email, county_name):
    office_supervisor = cleaned_data.split(", Supervisor")[0].strip()
    office_supervisor = re.sub("[^{}]+".format(printable), " ", office_supervisor)

    # extract address info which is always between supervisor and phone
    address = re.search("Supervisor(.*)Phone:", cleaned_data)
    address_result = "None" if address is None else address.group(1)
    physical_address = ""

    # similar setup for phone
    phone = re.search("Phone: (.*)Fax:", cleaned_data)
    phone_result = "None" if phone is None else phone.group(1).strip()

    # grab website
    website = re.search("Web Address: (.*)", cleaned_data)
    website_result = "None" if phone is None else website.group(1).strip()

    # extract and decode email
    email = electionsaver.decodeEmail(hex_email)

    schema = {
        "countyName": county_name,
        "phone": phone_result,
        "email": email,
        "officeSupervisor": office_supervisor,
        "website": website_result,
        "supervisorTitle": "Supervisor",
    }

    if address_result.count("FL") > 1:  # there are two addresses listed
        split_addresses = address_result.split("     ")
        mailing_address = " ".join(split_addresses[1:])
        schema["mailingAddress"] = format_address_data(mailing_address, county_name)
        physical_address = format_address_data(split_addresses[0], county_name)
    else:
        physical_address = format_address_data(address_result, county_name)

    schema["physicalAddress"] = physical_address

    return schema


def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping
    # parsed_data_dict = usaddress.tag(addressData, tag_mapping=mapping)[0]

    # edge cases

    # lol doctor and drive have the same abbreviation
    if county_name == "Collier":
        address_data = address_data.replace("Rev Dr", "Reverend Doctor")

    # this county only has a PO Box, and I happened to click on the website
    # and find out there's an actual physical location lol.. got lucky
    if county_name == "Citrus":
        address_data = "1500 N. Meadowcrest Blvd. Crystal River, FL 34429"

    parsed_data_dict = {}
    try:
        parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]
    except Exception as e:
        raise WalkTheVoteError(
            f"Error with data for {county_name} county, data is {parsed_data_dict}"
        ) from e

    final_address = {
        "city": parsed_data_dict["city"],
        "state": parsed_data_dict["state"],
        "zipCode": parsed_data_dict["zipCode"],
    }
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
<<<<<<< HEAD
    final_address["locationName"] = parsed_data_dict.get(
        "locationName", f"{county_name} County Election Office"
    )
=======
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    return final_address


async def get_election_offices():
<<<<<<< HEAD
    """Starting point of the scraper program. Scrapes BASE_URL for election office
=======
    """ Starting point of the scraper program. Scrapes BASE_URL for election office
>>>>>>> 5600ab1... removed lib in git ignore and putting scrapers in lib...?
    information and both dumps results to a .json file and returns the results as json.

    @return: list of scraped results as json.
    """
    # Define coroutine functions (context managers)
    async with CloudflareScraper() as session:
        async with session.get(BASE_URL) as s:
            # ClientResponse.read() is a coroutine function so it must be awaited
            text = await s.read()
        soup = bS(text.decode("utf-8"), "html.parser")

        test_county_data = get_county_codes_and_names(soup)
        county_data = sorted(test_county_data, key=lambda k: k["countyName"])
        num_scraped = 0
        master_list = []

        # Create list that will store asyncio tasks
        tasks: List[Task] = []
        for county in county_data:
            code = county["countyCode"]
            name = county["countyName"]
            # Create task for a future asynchronous operation and store it in task list
            tasks.append(asyncio.create_task(scrape_one_county(session, code, name)))

        # Run the coroutines and iterate over the yielded results as they complete
        # (out-of-order). Use asyncio.gather() with a couple code modifications to
        # preserve list order
        future: Future[Tuple[str, str, str, str]]
        for future in asyncio.as_completed(tasks):
            # Unpack awaited result of scrape_one_county()
            cleaned_string, protected_email, _, county_name = await future
            schema = format_data_into_schema(
                cleaned_string, protected_email, county_name
            )
            master_list.append(schema)
            num_scraped += 1
            print(
                f"[Florida] Scraped {county_name} county: "
                f"#{num_scraped} of {len(county_data)} .... "
                f"[{round((num_scraped / len(county_data)) * 100, 2)}%]"
            )

    with open(os.path.join(ROOT_DIR, r"scrapers\florida\florida.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{bcolors.OKBLUE}Completed in {end - start} seconds.{bcolors.ENDC}")
