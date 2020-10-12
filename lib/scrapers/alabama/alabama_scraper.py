import requests
import usaddress
import os
import json
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR

URL = "https://www.sos.alabama.gov/city-county-lookup/absentee-election-manager"

r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

info = soup.find_all('div', class_="official-info")

def formatSchema(phone, county, person, p_address, m_address):
    schema = {
        "countyName": county,
        "phone": phone,
        "officeSupervisor": person,
        "physicalAddress": p_address,
    }
    if m_address != {}:
        schema["mailingAddress"] = m_address
    #print(schema)
    return schema

masterList = []

def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping

    if county_name == "Coffee":
        address = "1055 E McKinnon St New Brockton, Alabama 36351"

    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    addressSchema = {
        "city": parsed_data_dict["city"],
        "state": parsed_data_dict["state"],
        "zipCode": parsed_data_dict["zipCode"]
    }

    if "aptNumber" in parsed_data_dict:
        addressSchema["aptNumber"] = parsed_data_dict["aptNumber"]
    if "poBox" in parsed_data_dict:
        addressSchema["poBox"] = parsed_data_dict["poBox"]
    if "locationName" in parsed_data_dict:
        addressSchema["locationName"] = parsed_data_dict["locationName"]
    if "streetNumberName" in parsed_data_dict:
        addressSchema["streetNumberName"] = parsed_data_dict["streetNumberName"]
    #else:
        #print(f'county_name {county_name} is the culprit')

    return addressSchema


for i in info:
    phone = i.find('div', class_="phone-1")

    datapoints = i.find_all('div', class_="physical-address")

    m_s = i.find('div', class_="mailing-address")

    cleaned_phone = phone.text.replace("Phone Number:", "").strip()
    cleaned_phone = cleaned_phone.split(",")[0].split("x")[0].strip()

    county = datapoints[0].text.replace("County:", "").strip()
    person = datapoints[1].text.replace("Absentee Election Manager", "").strip()
    p_address = datapoints[2].text.replace("Physical Address:", "").strip()
    aschema = format_address_data(p_address, county)

    m_address = m_s.text.replace("Mailing Address:", "").strip()

    bschema = format_address_data(m_address, county)

    if m_address == p_address:
        print(f'Physical and mailing are the same for {county} county')
        bschema = {}

    schema = formatSchema(cleaned_phone, county, person, aschema, bschema)
    masterList.append(schema)

with open(os.path.join(ROOT_DIR, "scrapers", "alabama", "alabama.json"), 'w') as f:
    json.dump(masterList, f)
