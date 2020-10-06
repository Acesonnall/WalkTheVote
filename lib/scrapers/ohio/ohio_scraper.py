from typing import List

import requests
from bs4 import BeautifulSoup
import re
import json

URL = (
    "https://www.sos.state.oh.us/elections/elections-officials/county-boards-of"
    "-elections-directory/ "
)
r = requests.get(URL)
soup = BeautifulSoup(r.content, "html5lib")
office_elems = soup.find_all("div", class_="wysiwyg-content")

# scraping for county names in Ohio
name_elems = soup.find_all("div", class_="list-item-blocks-grid__title")
county_names = []

for i in name_elems:
    c_name = i.text
    county_names.append(c_name)

all_elems = []
for i in office_elems:
    if "Telephone" in i.text:
        all_elems.append(i.text)

phone = []
addies = []
ohours: List[str] = []
zipcode = []

for i in all_elems:
    office_hours = re.search("Office Hours: (.*) Telephone", i)
    phone_num = re.search("Telephone: (.*) Fax", i)
    address = re.search("\nGet Directions {2}(.*) Office", i)
    zip = re.search("OH (.*) Office", i)
    if office_hours is None:
        ohours.append("None")
    else:
        ohours.append(office_hours.group(1))
    if phone_num is None:
        phone.append("None")
    else:
        phone.append(phone_num.group(1))
    if address is None:
        addies.append("None")
    else:
        addies.append(address.group(1))
    if zip is None:
        zipcode.append("None")
    else:
        zipcode.append(zip.group(1))

schema = {
    "countyName": county_names,
    "physicalAddress": {
        "streetNumberName": addies,
        "state": "Ohio",
        "county": county_names,
        "Zip Code": zipcode,
    },
    "phone": phone,
    "OfficeHours": ohours,
    "Link": "https://www.sos.state.oh.us/elections/elections-officials/county-boards"
    "-of-elections-directory/",
}
print(schema)