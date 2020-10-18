import asyncio
import os
import json
import usaddress
import pandas as pd

# Downlaod CSV file from https://www.sos.wa.gov/elections/viewauditors.aspx (click 
# Export to Excel) and place in same directory as this python file. 

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
from lib.errors.wtv_errors import WalkTheVoteError

def format_address_data(address_data, county_name, zip_code, city_name):
    mapping = electionsaver.addressSchemaMapping

    address_data = address_data.replace('<br />', ' ')
    print(county_name, address_data, city_name, zip_code)

    # Edge cases
    if county_name == "Benton":
        address_data = "620 Market St"
    if county_name == "Pacific":
        address_data = "300 Memorial Dr, South Bend, 98586"
    if county_name == "Yakima":
        address_data = "128 N. Second Street, Room 117 Yakima, WA 98901-2639"

    parsed_data_dict = {}
    try:
        parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]
    except Exception as e:
        raise WalkTheVoteError(
            f"Error with data for {county_name} town, data is {parsed_data_dict}"
        ) from e

    final_address = {"state": "WA"}

    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"].title()
    else:
        final_address["city"] = city_name.title()
    if "zipCode" in parsed_data_dict:
        final_address["zipCode"] = parsed_data_dict["zipCode"]
    else:
        final_address["zipCode"] = zip_code.title()
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"].title()
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"].title()
    final_address["locationName"] = parsed_data_dict.get(
        "locationName", f"{county_name} City Election Office".title()
    )
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"].title()
    return final_address

def data_to_json_schema():
    info_df = pd.read_csv(
        os.path.join(ROOT_DIR, "scrapers", "washington", "county-elections-departments.csv"),
        index_col=False,
    )

    county_list = info_df["County"].values
    website_list = info_df["Web"].values
    address_list = info_df["Address"].values
    city_list = info_df["City"]
    zip_list = info_df["Zip"]
    email_list = info_df["Email"].values
    phone_list = info_df["Phone"].values

    address_list_formatted = []
    for i in range(len(address_list)):
        address_list_formatted.append(
            format_address_data(address_list[i], county_list[i], zip_list[i], city_list[i])
        )

    master_list = []

    for i in range(len(county_list)):
        schema = {
            "countyName": county_list[i].title(),
            "phone": phone_list[i],
            "email": email_list[i],
            "website": website_list[i]
            if not str(website_list[i]) == "nan"
            else "https://www.sos.wa.gov/elections/viewauditors.aspx",
        }

        if "poBox" in address_list_formatted[i]:
            schema["mailingAddress"] = address_list_formatted[i]
        else:
            schema["physicalAddress"] = address_list_formatted[i]

        master_list.append(schema)

    master_list = sorted(master_list, key=lambda county: county['countyName'])

    with open(os.path.join(ROOT_DIR, "scrapers", "washington", "washington.json"), "w") as f:
        json.dump(master_list, f)
    return master_list

async def get_election_offices():
    if not os.path.isfile(
        os.path.join(ROOT_DIR, "scrapers", "washington", "county-elections-departments.csv")
    ):
        raise Exception("Washington county info csv file not found!")
    return data_to_json_schema()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(get_election_offices())