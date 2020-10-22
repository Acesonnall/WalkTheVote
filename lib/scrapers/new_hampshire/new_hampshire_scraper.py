# import context
import asyncio
import os
import json
import usaddress
import pandas as pd

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
from lib.errors.wtv_errors import WalkTheVoteError

DIRECTORY = os.path.join(ROOT_DIR, "scrapers", "new_hampshire")

def clean_raw_file(csv_path):
    # Open raw file to clean up
    csv_file = open(os.path.join(csv_path), "r",)
    data = csv_file.read()
    csv_file.close()

    data = data.replace("ST, SUITE", "ST SUITE")
    data = data.replace("Perkins, Sr.", "Perkins Sr.")
    data = data.replace("ST., PO", "ST. PO")
    data = data.replace("STREET, PO", "STREET PO")

    csv_file = open(os.path.join(DIRECTORY, "NewHampshireInfo.csv"), "w")
    csv_file.write(data)
    csv_file.close()


def format_address_data(address_data, town_name):
    mapping = electionsaver.addressSchemaMapping

    # Edge cases
    if address_data == "20 PARK ST GORHAM":
        address_data = "20 PARK ST GORHAM 03581"

    parsed_data_dict = {}
    try:
        parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]
    except Exception as e:
        raise WalkTheVoteError(
            f"Error with data for {town_name} town, data is {parsed_data_dict}"
        ) from e

    final_address = {"state": "NH"}

    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"].title()
    if "zipCode" in parsed_data_dict:
        final_address["zipCode"] = parsed_data_dict["zipCode"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"].title()
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"].title()
    final_address["locationName"] = parsed_data_dict.get(
        "locationName", f"{town_name} City Election Office".title()
    )
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"].title()
    return final_address


def data_to_json_schema():
    info_df = pd.read_csv(os.path.join(DIRECTORY, "NewHampshireInfo.csv"), index_col=False)

    town_list = info_df["Town/City"].values
    clerk_list = info_df["Clerk"].values
    address_list = info_df["Address"].values
    phone_list = info_df["Phone (area code 603)"].values
    email_list = info_df["E-Mail"].values
    website_list = info_df["Town Website Address"].values

    phone_list = ["603-" + phone_num for phone_num in phone_list]

    address_list_formatted = []
    for i in range(len(address_list)):
        address_list_formatted.append(
            format_address_data(address_list[i], town_list[i])
        )

    master_list = []

    for i in range(len(town_list)):
        schema = {
            "cityName": town_list[i].title(),
            "phone": phone_list[i],
            "email": email_list[i],
            "officeSupervisor": clerk_list[i].title(),
            "website": website_list[i]
            if not str(website_list[i]) == "nan"
            else "https://app.sos.nh.gov/Public/Reports.aspx",
            "supervisorTitle": "Clerk",
        }

        if "poBox" in address_list_formatted[i]:
            schema["mailingAddress"] = address_list_formatted[i]
        else:
            schema["physicalAddress"] = address_list_formatted[i]

        master_list.append(schema)

    with open(os.path.join(DIRECTORY, "new_hampshire.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


async def get_election_offices():
    csv_path = os.path.join(DIRECTORY, "StateList-Clerks & PollingPlaces.csv")
    if not os.path.isfile(csv_path):
        raise WalkTheVoteError(
            f"Prerequisite CSV file needed to scrape New Hampshire. Please go to "
            f"https://app.sos.nh.gov/Public/Reports.aspx and download the CSV file to "
            f"{DIRECTORY}. Make sure the downloaded file is named "
            f'"StateList-Clerks & PollingPlaces.csv". Once downloaded, you\'ll need '
            f"to name the right-most column that is currently unnamed because new "
            f"hampshire SOS staff couldn't be asked to do it."
        )
    if not os.path.isfile(os.path.join(DIRECTORY, "NewHampshireInfo.csv")):
        clean_raw_file(csv_path)
    return data_to_json_schema()


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(get_election_offices())
    except WalkTheVoteError as e:
        print(e)
