import asyncio
import json
import os
import time

import pandas as pd
import usaddress

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://sos.wv.gov/elections/Pages/CountyClerkDirectory.aspx"


def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping

    location_name = f"{county_name} County Election Office"

    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    final_address = {"locationName": location_name}

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]

    return final_address

async def get_election_offices():
    df = pd.read_html(URL)[0]
    df.drop(35, inplace=True)

    df["zip"] = df.Address.apply(lambda x: x.split()[-1])
    df["street_number_name"] = df.Address.apply(lambda x: " ".join(x.split("  ")[:-1]))
    df["city"] = df.Address.apply(lambda x: x.split("  ")[-1].split(",")[0])
    df["subschema"] = df.apply(lambda x: format_address_data(x.street_number_name, x.County), axis=1)

    df.loc[53, "city"] = "Elizabeth"
    df.loc[9, "street_number_name"] = "100 Court Street Ste. 1 P.O. Box 569"

    master_list = []

    for _, row in df.iterrows():
        schema = {
            "countyName": row.County,
            "physicalAddress": {
                "city": row.city,
                "state": "West Virginia",
                "zipCode": row.zip,
                "locationName": row.subschema["locationName"],
            },
            "phone": row.Phone,
            "email": row.Email,
            "officeSupervisor": row.Clerk,
            "website": URL,
        }

        if "poBox" in row.subschema:
            schema["physicalAddress"]["poBox"] = row.subschema["poBox"]
        if "aptNumber" in row.subschema:
            schema["physicalAddress"]["aptNumber"] = row.subschema["aptNumber"]
        if "streetNumberName" in row.subschema:
            schema["physicalAddress"]["streetNumberName"] = row.subschema["streetNumberName"]

        master_list.append(schema)

    with open(
        os.path.join(ROOT_DIR, "scrapers", "west_virginia", "west_virginia.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
