import asyncio
import json
import os
import shutil
import time

from bs4 import BeautifulSoup as bS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import usaddress

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://elect.ky.gov/About-Us/Pages/County-Clerks.aspx"
PATH_CHROMEDRIVER = shutil.which("chromedriver")


def format_address_data(address_data):
    mapping = electionsaver.addressSchemaMapping

    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    final_address = {}

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]

    return final_address

async def get_election_offices():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options, executable_path=PATH_CHROMEDRIVER)
    driver.get(URL)

    soup = bS(driver.page_source, "html.parser")
    counties = [option.text for option in soup.find_all('option')][2:]

    master_list = []
    soups = []

    for county in counties:
        dropdown = Select(driver.find_element_by_id("county"))
        button = driver.find_element_by_id("search-clerks")
        dropdown.select_by_visible_text(county)
        button.click()
        time.sleep(2)
        soup = bS(driver.page_source, "html.parser")

        supervisor = soup.find(class_="panel-heading").span.text

        # if we expand to branch offices in the future, swap to find_all
        # and iterate through list--main ofice always first

        email, website, po_box = None, None, None

        main_office = soup.find(class_="list-group")
        items = main_office.find_all(class_="list-group-content")

        for item in items:
            label = item.label.text
            if label == "Phone":
                phone = item.span.text
            elif label == "Email":
                email = item.span.text
            elif label == "Website":
                website = item.span.text
            elif label == "Physical Address":
                # this includes both physical and mailing addresses
                addresses = item.find_all("address")
                text = addresses[0].get_text("\n").split("\n")
                zip_code = text[-2].split()[-1][:5]
                city = text[-2].split(",")[0]
                if county == "Woodford":
                    address_data = "701 W. Ormsby Ave., Suite 301"
                else:
                    address_data = ", ".join(text[:-2])
                if len(addresses) > 1:
                    po_box = addresses[1].get_text("\n").split("\n")[0]


        subschema = format_address_data(address_data)

        schema = {
            "countyName": county,
            "physicalAddress": {
                "city": city,
                "state": "Kentucky",
                "zipCode": zip_code,
                "locationName": f"{county} County Election Office",
            },
            "phone": phone,
            "officeSupervisor": supervisor,
            "website": website if website else URL,
        }

        if email:
            schema["email"] = email
        if po_box:
            schema["physicalAddress"]["poBox"] = po_box
        if "aptNumber" in subschema:
            schema["physicalAddress"]["aptNumber"] = subschema["aptNumber"]
        if "streetNumberName" in subschema:
            schema["physicalAddress"]["streetNumberName"] = subschema["streetNumberName"]

        master_list.append(schema)
        print(county)

    driver.quit()

    with open(
        os.path.join(ROOT_DIR, "scrapers", "kentucky", "kentucky.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list

if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
