import asyncio
import json
import os
import time

import pandas as pd
import usaddress

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

CSV = os.path.join(ROOT_DIR, "scrapers", "wyoming", "wyoming_clerk_offices.csv")
WEBSITE = "https://sos.wyo.gov/Elections/"


async def get_election_offices():
    wyoming_df = pd.read_csv(CSV)
    election_offices = []
    mapping = electionsaver.addressSchemaMapping
    for county, county_clerk, phone, email, p_address, m_address in zip(
        wyoming_df["County"].values,
        wyoming_df["County Clerk"].values,
        wyoming_df["Phone"].values,
        wyoming_df["Email"].values,
        wyoming_df["P_address"].values,
        wyoming_df["M_address"].values,
    ):
        p_address_dict, m_address_dict = (None,) * 2
        supervisor_title = f"{county} County Clerk"
        election_office = {}
        if not pd.isnull(p_address):
            election_office["physicalAddress"] = usaddress.tag(
                p_address, tag_mapping=mapping
            )[0]
            election_office["physicalAddress"]["locationName"] = supervisor_title
        if not pd.isnull(m_address):
            election_office["mailingAddress"] = usaddress.tag(
                m_address, tag_mapping=mapping
            )[0]
            election_office["mailingAddress"]["locationName"] = supervisor_title

        election_office["countyName"] = county
        election_office["phone"] = phone
        election_office["email"] = email
        election_office["officeSupervisor"] = county_clerk
        election_office["supervisorTitle"] = "County Clerk" if county_clerk else None
        election_office["website"] = WEBSITE

        election_offices.append(election_office)

    with open(os.path.join(ROOT_DIR, "scrapers", "wyoming", "wyoming.json"), "w") as f:
        json.dump(election_offices, f)
    return election_offices


if __name__ == "__main__":
    start = time.time()
    # Normally you'd start the event loop with asyncio.run() but there's a known issue
    # with aiohttp that causes the program to error at the end after completion
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
