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
        "countyName": county.title(),
        "phone": phone,
        "officeSupervisor": person,
        "website": URL,
        "physicalAddress": p_address,
    }
    if m_address != {}:
        schema["mailingAddress"] = m_address
    #print(schema)
    return schema

masterList = []

def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping

    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    addressSchema = {
        "city": parsed_data_dict["city"].title(),
        "state": parsed_data_dict["state"].lower(),
        "zipCode": parsed_data_dict["zipCode"]
    }
    if "locationName" in parsed_data_dict:
        addressSchema["locationName"] = parsed_data_dict["locationName"].title()
    else:
        addressSchema["locationName"] = (county_name.title() + " county registrar of voters").lower()
    if "aptNumber" in parsed_data_dict:
        addressSchema["aptNumber"] = parsed_data_dict["aptNumber"]
    if "poBox" in parsed_data_dict:
        addressSchema["poBox"] = parsed_data_dict["poBox"]
    if "streetNumberName" in parsed_data_dict:
        addressSchema["streetNumberName"] = parsed_data_dict["streetNumberName"].title()
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
    if county == "Coffee":
        p_address = "1055 E McKinnon St New Brockton, Alabama 36351"
    person = datapoints[1].text.replace("Absentee Election Manager", "").strip()
    p_address = datapoints[2].text.replace("Physical Address:", "").strip()
    aschema = format_address_data(address=p_address, county_name=county)
    for j in aschema:
        j = j.upper()
    m_address = m_s.text.replace("Mailing Address:", "")
    m_address = m_address.replace("\n", " ")
    bschema = format_address_data(address=m_address, county_name=county)

    if m_address == p_address:
        print(f'Physical and mailing are the same for {county} county')
        bschema = {}

    schema = formatSchema(cleaned_phone, county, person, aschema, bschema)
    masterList.append(schema)



with open(os.path.join(ROOT_DIR, "scrapers", "alabama", "alabama.json"), 'w') as f:
    json.dump(masterList, f)
