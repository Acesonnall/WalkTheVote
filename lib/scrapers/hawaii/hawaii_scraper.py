import requests
import usaddress
import os
import json
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR

URL = "https://elections.hawaii.gov/resources/county-election-divisions/"

r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

classList = ["row-2 even", "row-3 odd", "row-4 even", "row-5 odd"]

baseList = []

for br in soup.find_all("br"):
    br.replace_with("\n")

for j in classList:
    x = soup.find("tr", class_=j)
    baseList.append(x)

def formatSchema(county, phone, person, p_address, m_address):
    schema = {
        "countyName": county,
        "phone": phone,
        "officeSupervisor": person,
        "physicalAddress": p_address,
    }
    if m_address != {}:
        schema["mailingAddress"] = m_address
    # print(schema)
    return schema

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
    else:
        print(f'county_name {county_name} is the culprit')

    return addressSchema

masterList = []

for i in baseList:
    datapoints1 = i.find('td', class_="column-1").text.split("\n")
    datapoints2 = i.find('td', class_="column-2").text.split("\n")
    datapoints3 = i.find('td', class_="column-3").text.split("\n")
    phone = datapoints3[0].replace("Phone: ", "").strip()
    p_address = datapoints2[0] + " " + datapoints2[2] + " " + datapoints2[4]
    m_address = datapoints2[0] + " " + datapoints2[2] + " " + datapoints2[4]
    county = datapoints1[0].replace("County of ", "").strip()
    person = datapoints1[4].strip()
    aschema = format_address_data(p_address, county)
    bschema = format_address_data(m_address, county)
    if m_address == p_address:
        print(f'Physical and mailing are the same for {county} county')
        bschema = {}
    schema = formatSchema(county=county, phone=phone, person=person, p_address=aschema, m_address=bschema)
    masterList.append(schema)
print(masterList)

with open(os.path.join(ROOT_DIR, "scrapers", "hawaii", "hawaii.json"), 'w') as f:
    json.dump(masterList, f)