import json
import re
from string import printable
from typing import Dict

import requests
import usaddress
from bs4 import BeautifulSoup as bS

requests.packages.urllib3.disable_warnings()

BASE_URL = "https://mvic.sos.state.mi.us/Clerk"

# found via Network tab in developer tools
NEW_URL = "https://mvic.sos.state.mi.us/Voter/SearchByCounty"

r = requests.get(BASE_URL, verify=False)
soup = bS(r.content, "html.parser")

countyData = []


def get_county_names():
    options = soup.find_all("option")
    for option in options:
        if "County" in option.text or "COUNTY" in option.text:
            this_county_name = option.text.replace(" ", "+")
            if "IRON" in option.text:
                this_county_name = "Iron"
            this_county_id = option["value"]
            countyData.append(
                {"CountyName": this_county_name, "CountyID": this_county_id}
            )


get_county_names()


def request_data_for_one_county(county_data):
    req = requests.post(NEW_URL, county_data, verify=False)
    _soup = bS(req.content, "html.parser")

    office_data = _soup.find(id="pnlClerk").find(class_="card-body").text
    example = {"\t": None, "\n": " ", "\r": None}
    table = office_data.maketrans(example)
    cleaned = office_data.translate(table)

    res = format_data_into_schema(county_data["CountyName"], cleaned)
    return res


def format_data_into_schema(county_name, post_response_data):
    """

    @param county_name:
    @param post_response_data: a string that that lists county clerk name, address,
    phone, fax, email, and business hours in that order
    @return:
    """
    cleaned_data = re.sub("[^{}]+".format(printable), "", post_response_data)
    cleaned_county_name = county_name.replace("+", " ").replace(" County", "")

    # print(cleanedData)

    phone_regex = re.search("Phone:(.*) {2}Fax:", cleaned_data)
    phone = "None" if phone_regex is None else phone_regex[1]

    email_regex = re.search(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", cleaned_data
    )
    email = "None" if email_regex is None else email_regex[0]

    # janky as fuck, but search stops after first match
    # and our code cleaned it up in such a way that address is always
    # 3 spaces after the end of the clerk name
    clerk_regex = re.search(".+?(?= {3})", cleaned_data)
    clerk_data = "None" if clerk_regex is None else clerk_regex[0]

    tmpcd = clerk_data.split(",")
    first_last = tmpcd[0].strip()
    clerk_title = "N/A" if len(tmpcd) == 1 else tmpcd[1].strip()

    address_data = cleaned_data.replace(clerk_data, "").split("Phone:")[0]

    # dealing with stupid edge cases
    if cleaned_county_name == "Keweenaw":
        address_data = address_data.replace("5095 4th", "5095 4th St")

    if cleaned_county_name == "Oakland":
        address_data = address_data.replace("Building 12 East", "Building 12")

    if cleaned_county_name == "Wayne":
        address_data = address_data.replace("Bldg", "Building")

    if cleaned_county_name == "Kent":
        address_data = address_data.replace("T Grand", "Grand")

    if cleaned_county_name == "Missaukee":
        address_data = address_data.replace("111 S Canal St", "")

    split_addresses = address_data.split("Mailing address:")

    physical_address = format_address_data(split_addresses[0], cleaned_county_name)

    schema = {
        "countyName": cleaned_county_name,
        "physicalAddress": physical_address,
        "phone": phone,
        "email": email,
        "officeSupervisor": first_last,
        "supervisorTitle": clerk_title,
    }

    if len(split_addresses) > 1:  # there is a mailing address as well
        mailing = split_addresses[1]

        # another edge case
        if cleaned_county_name == "Iosco":
            mailing = mailing.replace(
                "422 W. Lake Street, County Building",
                "County Building 422 W. Lake Street",
            )

        mailing_address = format_address_data(mailing, cleaned_county_name)
        schema["mailingAddress"] = mailing_address

    # print(schema)
    return schema


def format_address_data(address_data, county_name):
    address_schema_mapping = {
        "BuildingName": "locationName",
        "CornerOf": "locationName",
        "IntersectionSeparator": "locationName",
        "LandmarkName": "locationName",
        "NotAddress": "locationName",
        "SubaddressType": "aptNumber",
        "SubaddressIdentifier": "aptNumber",
        "AddressNumber": "streetNumberName",
        "StreetName": "streetNumberName",
        "StreetNamePreDirectional": "streetNumberName",
        "StreetNamePreModifier": "streetNumberName",
        "StreetNamePreType": "streetNumberName",
        "StreetNamePostDirectional": "streetNumberName",
        "StreetNamePostModifier": "streetNumberName",
        "StreetNamePostType": "streetNumberName",
        "OccupancyType": "aptNumber",
        "OccupancyIdentifier": "aptNumber",
        "Recipient": "locationName",
        "PlaceName": "city",
        "USPSBoxGroupID": "poBox",
        "USPSBoxGroupType": "poBox",
        "USPSBoxID": "poBox",
        "USPSBoxType": "poBox",
        "StateName": "state",
        "ZipCode": "zipCode",
    }
    parsed_data_dict: Dict = usaddress.tag(
        address_data, tag_mapping=address_schema_mapping
    )[0]

    final_address = {
        "city": parsed_data_dict.get("city"),
        "state": parsed_data_dict.get("state"),
        "zipCode": parsed_data_dict.get("zipCode"),
    }
    if not (
        final_address["city"] or final_address["state"] or final_address["zipCode"]
    ):
        raise KeyError(f"Error with data: {parsed_data_dict}")

    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
        if county_name == "Montmorency":
            final_address["streetNumberName"] = (
                final_address["streetNumberName"] + " M-32"
            )
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
        if county_name == "Oakland":
            final_address["aptNumber"] = final_address["aptNumber"] + " East"
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    return final_address


masterList = []
# do stuff to all counties
numScraped = 0
for county in countyData:
    data = request_data_for_one_county(county)
    masterList.append(data)
    numScraped += 1
    print(
        f'[Michigan] Scraped {data["countyName"]} county: #{numScraped} of '
        f"{len(countyData)} .... [{round((numScraped / len(countyData)) * 100, 2)}%]"
    )

# output to JSON
with open("michigan.json", "w") as f:
    json.dump(masterList, f)
