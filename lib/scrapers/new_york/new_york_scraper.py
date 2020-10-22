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

BASE_URL = "https://www.elections.ny.gov/CountyBoards.html"

def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping

    # Edge cases

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
        "locationName", f"{county_name} County Board of Elections".title()
    )
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"].title()
    return final_address


def format_data_into_schema(
    address, county_website, phone_number, email_address, county_name
):
    schema = {
        "countyName": county_name.title(),
        "phone": phone_number,
        "email": email_address,
        "website": county_website,
    }

    address_formatted = format_address_data(address, county_name)

    if "poBox" in address_formatted:
            schema["mailingAddress"] = address_formatted
    else:
        schema["physicalAddress"] = address_formatted

    return schema


async def scrape_one_county(session, county_name, county_url):
    async with session.get(county_url) as s:
        text = await s.read()
        soup = bS(text, "html5lib")
    
    info_text = soup.prettify()
    
    address_start_ind = info_text.index('Board of Elections') + len('Board of Elections')
    address_end_ind = info_text.index('Phone')
    raw_address = info_text[address_start_ind:address_end_ind]
    address = raw_address.replace('<br/>', ' ').replace('\n', ' ').strip()

    phone_start_ind = info_text.index('Phone:') + len('Phone:')
    phone_end_ind = info_text.index('Fax')
    raw_phone = info_text[phone_start_ind:phone_end_ind]
    phone_number = raw_phone.replace('<br/>', ' ').replace('\n', ' ').strip()

    hrefs_list = soup.findAll('a')

    county_website = ''
    email_address = ''

    for site in hrefs_list:
        if 'Email' in site.text and 'Absentee' not in site.text:
            raw_email = site['href']
            email_address = raw_email.replace('mailto:', '').strip()
        if 'Visit' in site.text:
            county_website = site['href'].strip()

    return (
        address,
        county_website,
        phone_number,
        email_address,
        county_name,
    )


async def get_election_offices():
    """Starting point of the scraper program. Scrapes BASE_URL for election office
    information and both dumps results to a .json file and returns the results as json.

    @return: list of scraped results as json.
    """
    # Get list of county names from registrar to populate form
    # Define coroutine functions (context managers)
    async with CloudflareScraper() as session:
        async with session.get(BASE_URL) as s:
            # ClientResponse.read() is a coroutine function so it must be awaited
            text = await s.read()
        soup = bS(text, "html5lib")

        info_list = soup.findAll("area")
        counties = [info['alt'] for info in info_list]
        county_urls = [info['href'] for info in info_list]

        # Use list of counties and IDs to get county info for each county
        tasks: List[Task] = []
        num_scraped = 0
        master_list = []

        for i in range(len(counties)):
            # Create task for a future asynchronous operation and store it in task list
            tasks.append(
                asyncio.create_task(scrape_one_county(session, counties[i], county_urls[i]))
            )

        # Run the coroutines and iterate over the yielded results as they complete
        # (out-of-order). Use asyncio.gather() with a couple code modifications to
        # preserve list order
        future: Future[Tuple[str, str, str, str, str]]
        for future in asyncio.as_completed(tasks):
            # Unpack awaited result of scrape_one_county()
            (
                address,
                county_website,
                phone_number,
                email_address,
                county_name,
            ) = await future
            schema = format_data_into_schema(
                address,
                county_website,
                phone_number,
                email_address,
                county_name,
            )
            master_list.append(schema)
            num_scraped += 1
            print(
                f"[New York] Scraped {county_name} county: "
                f"#{num_scraped} of {len(counties)} .... "
                f"[{round((num_scraped / len(counties)) * 100, 2)}%]"
            )
    master_list = sorted(master_list, key=lambda county: county['countyName'])
    
    with open(os.path.join(ROOT_DIR, "scrapers", "new_york", "new_york.json"), "w") as f:
        json.dump(master_list, f)
    return master_list




if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")