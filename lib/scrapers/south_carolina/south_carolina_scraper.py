import asyncio
import os
import time
from asyncio import Task
from asyncio.futures import Future
from typing import List, Tuple

from bs4 import BeautifulSoup as bS
import json
import usaddress
from aiocfscrape import CloudflareScraper

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR, Bcolors
from lib.errors.wtv_errors import WalkTheVoteError

INFO_URL = "https://www.scvotes.gov/how-register-absentee-voting"
BASE_URL = "https://www.scvotes.gov/"

def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping

    print(county_name, address_data)

    parsed_data_dict = {}
    try:
        parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]
    except Exception as e:
        raise WalkTheVoteError(
            f"Error with data for {county_name} town, data is {parsed_data_dict}"
        ) from e

    final_address = {"state": "NY"}

    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"].title()
    if "zipCode" in parsed_data_dict:
        final_address["zipCode"] = parsed_data_dict["zipCode"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"].title()
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"].title()
    final_address["locationName"] = parsed_data_dict.get(
        "locationName", f"{county_name} County Board of Voter Registration & Elections".title()
    )
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"].title()
    return final_address


def format_data_into_schema(
    address, county_website, phone_number, email_address, director_name, county_name
):
    schema = {
        "countyName": county_name.title(),
        "phone": phone_number,
        "email": email_address,
        "website": county_website,
    }

    if director_name != '':
        schema["officeSupervisor"] = director_name.title()
        schema["supervisorTitle"] = "Director"


    # Edge cases
    if county_name == 'Aiken':
        schema["mailingAddress"] = format_address_data('Aiken County Government Center, 1930 University Parkway, Aiken, SC 29801', county_name)
        schema["physicalAddress"] = format_address_data('Post Office Box 3127, Aiken, SC  29802', county_name)
        return schema
    if county_name == 'Colleton':
        schema["mailingAddress"] = format_address_data('2471 Jefferies Highway, Walterboro, SC  29488', county_name)
        schema["physicalAddress"] = format_address_data('Post Office Box 97, Walterboro, SC 29488', county_name)
        return schema
    if county_name == 'Marion':
        schema["mailingAddress"] = format_address_data('2523 E. Highway 76, Marion, S.C. 29571', county_name)
        schema["physicalAddress"] = format_address_data('P.O. Box 1898, Marion, S.C. 29571', county_name)
        return schema
    if county_name == 'Richland':
        schema["mailingAddress"] = format_address_data('2020 Hampton Street, Columbia, SC  29202', county_name)
        schema["physicalAddress"] = format_address_data('PO Box 5330, Columbia, SC  29250', county_name)
        return schema

    address_formatted = format_address_data(address, county_name)

    if "poBox" in address_formatted:
            schema["mailingAddress"] = address_formatted
    else:
        schema["physicalAddress"] = address_formatted

    return schema


async def scrape_one_county(session, county_name):
    county_url = BASE_URL + county_name.lower()
    async with session.get(county_url) as s:
        text = await s.read()
        soup = bS(text, "html5lib")
    
    p_tags = soup.findAll('p')

    address = ''
    county_website = county_url
    phone_number = ''
    email_address = ''
    director_name = ''

    # Basically need to make a state machine and parse line by line, initially
    # scraping address components, then phone number, director, email, etc. This website sucks.

    # Variable to determine whether we are still scraping address.
    scraping_address = True
    for line in p_tags[3:]:
        if phone_number == '' and '(' in line.text and ')' in line.text:
            raw_number = line.text
            phone_number = raw_number.replace('Phone', '').replace('Office', '').replace(':', '').strip()

            # No longer on an address line, so set to false.
            scraping_address = False

        if director_name == '' and 'Director' in line.text:
            end_index = line.text.index('Director')
            director_name = line.text[:end_index].replace('-', '').strip()
        
        if email_address == '' and '@' in line.text:
            email_address = line.text
        
        if 'Board of Voter Registration' in line.text:
            county_website = line.find('a')['href']

        if scraping_address:
            address = address + ' ' + line.text
        

    return (
        address,
        county_website,
        phone_number,
        email_address,
        director_name,
        county_name
    )


async def get_election_offices():
    """Starting point of the scraper program. Scrapes BASE_URL for election office
    information and both dumps results to a .json file and returns the results as json.

    @return: list of scraped results as json.
    """
    # Get list of county names from registrar to populate form
    # Define coroutine functions (context managers)
    async with CloudflareScraper() as session:
        async with session.get(INFO_URL) as s:
            # ClientResponse.read() is a coroutine function so it must be awaited
            text = await s.read()
        soup = bS(text, "html5lib")

        info_list = soup.find('div', {'class':'content'}).findAll('li')
        counties = [info.text for info in info_list]

        # Use list of counties and IDs to get county info for each county
        tasks: List[Task] = []
        num_scraped = 0
        master_list = []

        for i in range(len(counties)):
            # Create task for a future asynchronous operation and store it in task list
            tasks.append(
                asyncio.create_task(scrape_one_county(session, counties[i]))
            )

        # Run the coroutines and iterate over the yielded results as they complete
        # (out-of-order). Use asyncio.gather() with a couple code modifications to
        # preserve list order
        future: Future[Tuple[str, str, str, str, str, str]]
        for future in asyncio.as_completed(tasks):
            # Unpack awaited result of scrape_one_county()
            (
                address,
                county_website,
                phone_number,
                email_address,
                director_name,
                county_name
            ) = await future
            schema = format_data_into_schema(
                address,
                county_website,
                phone_number,
                email_address,
                director_name,
                county_name
            )
            master_list.append(schema)
            num_scraped += 1
            print(
                f"[South Carolina] Scraped {county_name} county: "
                f"#{num_scraped} of {len(counties)} .... "
                f"[{round((num_scraped / len(counties)) * 100, 2)}%]"
            )
    master_list = sorted(master_list, key=lambda county: county['countyName'])

    with open(os.path.join(ROOT_DIR, "scrapers", "south_carolina", "south_carolina.json"), "w") as f:
        json.dump(master_list, f)
    return master_list




if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")