import context
import os
import json
import usaddress
import pandas as pd
from definitions import ROOT_DIR, bcolors
from ElectionSaver import electionsaver
from errors.wtv_errors import WalkTheVoteError

# Downlaod CSV file from https://app.sos.nh.gov/Public/Reports.aspx and place in same directory as this python file

def clean_raw_file():
    # Open raw file to clean up
    csv_file = open("./StateList-Clerks & PollingPlaces.csv", "r")
    data = csv_file.read()
    csv_file.close()

    data = data.replace("ST, SUITE", "ST SUITE")
    data = data.replace("Perkins, Sr.", "Perkins Sr.")
    data = data.replace("ST., PO", "ST. PO")
    data = data.replace("STREET, PO", "STREET PO")

    csv_file = open("./NewHampshireInfo.csv", "w")
    csv_file.write(data)
    csv_file.close()

def format_address_data(address_data, town_name):
    mapping = electionsaver.addressSchemaMapping

    parsed_data_dict = {}
    try:
        parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]
    except Exception as e:
        raise WalkTheVoteError(
            f"Error with data for {town_name} town, data is {parsed_data_dict}"
        ) from e

    final_address = {
        
        "state": "NH"
    }

    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"]
    if "zipCode" in parsed_data_dict:
        final_address["zipCode"] = parsed_data_dict["zipCode"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    return final_address


def data_to_json_schema():
    info_df = pd.read_csv('./NewHampshireInfo.csv', index_col=False)

    town_list = info_df['Town/City'].values
    clerk_list = info_df['Clerk'].values
    address_list = info_df['Address'].values
    phone_list = info_df['Phone (area code 603)'].values
    email_list = info_df['E-Mail'].values
    website_list = info_df['Town Website Address'].values

    phone_list = ['603-' + phone_num  for phone_num in phone_list]
    
    address_list_formatted = []
    for i in range(len(address_list)):
        address_list_formatted.append(format_address_data(address_list[i], town_list[i]))
    
    master_list = []

    for i in range(len(town_list)):
        schema = {
            "cityName": town_list[i],
            "phone": phone_list[i],
            "email": email_list[i],
            "officeSupervisor": clerk_list[i],
            "website": website_list[i],
            "supervisorTitle": "Clerk"
        }

        if "poBox" in address_list_formatted[i]:
            schema["mailingAddress"] = address_list_formatted[i]
        else:
            schema["physicalAddress"] = address_list_formatted[i]

        master_list.append(schema)

    with open(os.path.join(ROOT_DIR, r"scrapers\new_hampshire\new_hampshire.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    if not os.path.isfile('./NewHampshireInfo.csv'):
        clean_raw_file()
    data_to_json_schema()