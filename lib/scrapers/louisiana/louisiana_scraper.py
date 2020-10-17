import requests
import re
import usaddress
import os
import json
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR

URL = "https://voterportal.sos.la.gov/Registrar"

r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

baseList = []

for br in soup.find_all("br"):
    br.replace_with("\n")

for j in range(2,65,1):
    x = soup.find("div", {"data-parish-id":str(j)})
    baseList.append(x)

def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping
    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    if "city" not in parsed_data_dict:
        print(f'county_name {county_name} is the culprit')
        print(parsed_data_dict["poBox"])



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
    print()
    return addressSchema

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


masterList = []

for i in baseList:
    datapoints1 = i.find_all('span', class_="reg-data")
    datapoints2 = i.find('span', class_="office-title")
    clean = datapoints2.text.strip()
    remove = re.search("Registrar of Voters", clean)
    cleaner = clean[:remove.start()]+clean[remove.end():]
    remove1 = re.search("\\sP", cleaner)
    person = cleaner[remove.start():].replace(": ", "").strip()
    county = cleaner[:remove.start()].replace("Parish ", "").strip()
    phone = datapoints1[2].text.split(",")[0].split("x")[0].strip()
    p_address = datapoints1[0].get_text(separator="\n").replace("\nGet directions", "").replace("\n", " ").strip()
    remove2 = re.search("\\d", p_address)
    p_address = p_address[remove2.start():].strip()
    m_address = datapoints1[1].text.replace("'n", " ")
    if county == "Bienville":
        p_address = "100 COURTHOUSE DR STE 1400 ARCADIA, LA 71001-1001"
        m_address = "PO BOX 697 ARCADIA, LA 71001-0697"
    if county == "Catahoula":
        p_address = "301 BUSHLEY ST RM 103 HARRISONBURG, LA 71340"
        m_address = "PO BOX 215 HARRISONBURG, LA 71340-0215"
    if county == "St. Helena":
        p_address = "23 S. MAIN ST SUITE A GREENSBURG, LA 70441"
        m_address = "PO BOX 543 GREENSBURG, LA 70441-0543"
    aschema = format_address_data(p_address, county)
    bschema = format_address_data(m_address, county)
    schema = formatSchema(county, phone, person, aschema, bschema)
    masterList.append(schema)

print(masterList)


with open(os.path.join(ROOT_DIR, "scrapers", "louisiana", "louisiana.json"), 'w') as f:
    json.dump(masterList, f)

