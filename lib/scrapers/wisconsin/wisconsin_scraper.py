import asyncio
import json
import os
import re
import time
from pprint import pprint

import aiohttp
import requests
import usaddress
from pdfreader import SimplePDFViewer, PDFDocument

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR, bcolors

URL = (
    "https://elections.wi.gov/sites/elections.wi.gov/files/2020-08/WI%20County"
    "%20Clerks%20Updated%208-7-20.pdf"
)


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()

    # Prep helper vars
    phone, office_supervisor, website, location_name, county_name = ("",) * 5

    doc = PDFDocument(text)
    viewer = SimplePDFViewer(text)
    physical_address, mailing_address = ({},) * 2
    election_offices = []
    for i, page in enumerate(doc.pages(), 1):
        viewer.navigate(i)
        viewer.render()
        # This is parsed in the order at which pdf elements are read by the viewer.
        for j, s in enumerate(viewer.canvas.strings):
            if not county_name:
                m = re.search(r"\D+(?=\s-)", s)
                if m:
                    county_name = m.group(0).split(maxsplit=1)[0].capitalize()
                    location_name = f"{county_name} Election Office"

            mapping = electionsaver.addressSchemaMapping

            if not physical_address:
                m = re.search(r"(?<=MUNICIPAL ADDRESS :).*", s)
                if m:
                    physical_address = usaddress.tag(
                        f"{m.group(0)} {viewer.canvas.strings[j + 1]}".title(),
                        tag_mapping=mapping,
                    )[0]
                    physical_address["state"].upper()
                    physical_address["locationName"] = location_name
            if not mailing_address:
                m = re.search(r"(?<=MAILING ADDRESS :).*", s)
                if m:
                    mailing_address = usaddress.tag(
                        f"{m.group(0)} {viewer.canvas.strings[j + 1]}".title(),
                        tag_mapping=mapping,
                    )[0]
                    mailing_address["state"].upper()
                    mailing_address["locationName"] = location_name
            if not phone:
                m = re.search(r"(?<=Phone 1: ).*", s)
                if m:
                    phone = m.group(0)
                    election_offices.append(
                        {
                            "countyName": county_name,
                            "physicalAddress": physical_address,
                            "mailingAddress": mailing_address,
                            "phone": phone,
                            "officeSupervisor": office_supervisor,
                            "supervisorTitle": "County Clerk",
                            "website": website,
                        }
                    )
                    # reset for next round
                    phone, office_supervisor, website, location_name, county_name = (
                        "",
                    ) * 5
            if not office_supervisor:
                m = re.search(r"(?<=COUNTY CLERK: ).*", s)
                if m:
                    office_supervisor = m.group(0).title()
            if not website:
                m = re.search(r"http.*", s)
                if m:
                    website = m.group(0)

    with open(
        os.path.join(ROOT_DIR, "scrapers", "wisconsin", "wisconsin.json"), "w"
    ) as f:
        json.dump(election_offices, f)
    return election_offices


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{bcolors.OKBLUE}Completed in {end - start} seconds.{bcolors.ENDC}")
