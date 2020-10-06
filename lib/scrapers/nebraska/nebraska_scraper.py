import re
from string import printable

import json
import requests
import sys
sys.path.append('../../ElectionSaver')

import electionsaver
import usaddress
from bs4 import BeautifulSoup as bS

# emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleanedData)

BASE_URL = "https://sos.nebraska.gov/elections/election-officials-contact-information"

r = requests.get(BASE_URL)
soup = bS(r.content, "html.parser")

elems = soup.find_all(class_="col-sm-6")

masterList = []

def formatAddressData(addressData, countyName):
    mapping = electionsaver.addressSchemaMapping
    
    locationName = f'{countyName} County Election Office'

    if countyName == "Banner":
        addressData = "204 State St, PO Box 67"
        locationName = "Banner County Courthouse"
    if countyName == "Box Butte":
        addressData = "515 Box Butte Avenue #203, PO Box 678"

    parsedDataDict = usaddress.tag(addressData, tag_mapping=mapping)[0]

    finalAddress = {
        "locationName": locationName
    }

    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']

    return finalAddress

for e in elems:
    cleanedData = re.sub("[^{}]+".format(printable), "", e.text)

    # (.*) matches EVERYTHING between "Name: " and "Party"
    # the space is important
    nameRegex = re.search("Name:(.*)Party Affiliation:", cleanedData)
    name = "None" if nameRegex is None else nameRegex[1]
    Names: str = name.strip()

    addyRegex = re.search("Address:(.*)City", cleanedData)
    Addy = "None" if addyRegex is None else addyRegex[1]
    streetNumberName: str = Addy.strip()

    cityRegex = re.search("City:(.*)Zip", cleanedData)
    cities = "None" if cityRegex is None else cityRegex[1]
    City: str = cities.strip()

    countyRegex = re.search("County:(.*)Name:", cleanedData)
    count = "None" if countyRegex is None else countyRegex[1]
    noParens = count.split("(")[0]
    County: str = noParens.strip()

    zipRegex = re.search("Code:(.*)Phone", cleanedData)
    z = "None" if zipRegex is None else zipRegex[1]
    zipCode: str = z.strip()

    phoRegex = re.search("Number:(.*)Fax", cleanedData)
    ph = "None" if phoRegex is None else phoRegex[1]
    Phone: str = ph.strip()

    emRegex = re.search("Email Address: (.*)", cleanedData)
    e = "None" if emRegex is None else emRegex[1]
    Email: str = e.strip()

    if County != 'None':
        subschema = formatAddressData(streetNumberName, County)
        schema = {
            "countyName": County,
            "physicalAddress": {
                "city": City,
                "state": "Nebraska",
                "zipCode": zipCode,
                "locationName": subschema['locationName']
            },
            "phone": Phone,
            "email": Email,
            "officeSupervisor": Names,
            "Link": "https://sos.nebraska.gov/elections/election-officials-contact"
            "-information",
        }

        if 'poBox' in subschema:
            schema['physicalAddress']['poBox'] = subschema['poBox']
        if 'aptNumber' in subschema:
            schema['physicalAddress']['aptNumber'] = subschema['aptNumber']
        if 'streetNumberName' in subschema:
            schema['physicalAddress']['streetNumberName'] = subschema['streetNumberName']

        masterList.append(schema)

with open("nebraska.json", "w") as f:
    json.dump(masterList, f)
