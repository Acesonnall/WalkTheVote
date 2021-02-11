import requests
import re
import usaddress
import os
import json
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR

def formatSchema(county, phone, person, p_address, m_address, website):
    schema = {
        "countyName": county.title(),
        "phone": phone,
        "officeSupervisor": person,
        "website": website,
        "physicalAddress": p_address,
    }
    if m_address != {}:
        schema["mailingAddress"] = m_address
    return schema

def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping
    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    # if "city" not in parsed_data_dict:
        # print(f'county_name {county_name} is the culprit')
        # print(parsed_data_dict["poBox"])

    addressSchema = {
        "city": parsed_data_dict["city"].title(),
        "state": parsed_data_dict["state"].lower(),
        "zipCode": parsed_data_dict["zipCode"]
    }

    if "locationName" in parsed_data_dict:
        addressSchema["locationName"] = parsed_data_dict["locationName"].lower()
    else:
        addressSchema["locationName"] = (county_name + " Parish Registrar of Voters").lower()
    if "aptNumber" in parsed_data_dict:
        addressSchema["aptNumber"] = parsed_data_dict["aptNumber"].lower()
    if "poBox" in parsed_data_dict:
        addressSchema["poBox"] = parsed_data_dict["poBox"]
    if "streetNumberName" in parsed_data_dict:
        addressSchema["streetNumberName"] = parsed_data_dict["streetNumberName"].lower()
    else:
        print(f'county_name {county_name} is the culprit')
    return addressSchema

URL = "https://tnsos.org/elections/election_commissions.php?Show=All"

r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')


info = soup.findAll("table", {"id":"data"})

masterList = []

for i in info:
    county = i.find("div", class_="title").text.strip()
    data = i.findAll("tr")
    person = data[1].text.split("\n")[2]
    # print(county)
    if re.match("(\\d){3}((\\.)|-)?(\\d){3}((\\.)|-)?(\\d){4}",data[3].text.split("\n")[2]):
        phone = data[3].text.split("\n")[2]
    elif re.match("(\\d){3}(\\.)?(\\d){3}(\\.)?(\\d){4}",data[4].text.split("\n")[2]):
        phone = data[4].text.split("\n")[2]
    # print(phone)
    if re.match("Address", data[2].text.replace("\n", "").strip()):
        p_address = data[2].text.replace("\n", "").strip()
    elif re.match("Address:", data[3].text.replace("\n", "").strip()):
        p_address = data[3].text.replace("\n", "").strip()
    # print(p_address)

    if re.match("Mailing Address:", data[2].text.replace("\n", "").strip()):
        m_address = data[2].text.replace("\n", "").strip()
    else:
        m_address = []
    try:
        m_address = m_address.replace("Mailing Address:", "")
    except Exception:
        m_address = []
    # Cleaning up both addresss
    p_address = p_address.replace("Address:", "")
    p_address = re.split("\\s{2,}", p_address)
    try:
        p_address[2] = p_address[2].replace(" Co ", " County ")
    except Exception:
        p_address = p_address
    try:
        p_address[1] = p_address[1].replace(" Co ", " County ")
    except Exception:
        p_address = p_address
    # print(county)
    # print(p_address)
    try:
        p_address = p_address[1] + ", " + p_address[0] + ", " + p_address[2] + ", TN, " + p_address[3]
    except Exception:
        p_address = p_address = p_address[0] + ", TN," + p_address[1]

    try:
        m_address = m_address.replace("Mailing Address:", "")
        m_address = re.split("\\s{2,}", m_address)
        m_address = m_address[0] + ", " + m_address[1] + ", " + m_address[2]
    except Exception:
        m_address = ""

    # print(m_address)
    if county == "Anderson":
        p_address = "Anderson County Courthouse, 100 North Main Street, Room 207, Clinton, LA, 37716-3683"
    elif county == "Bledsoe":
        p_address = "Bledsoe County Courthouse, 3150 Main Street, Suite 700, Pikeville, LA, 37367"
    elif county == "Bradley":
        p_address = "Courthouse Annex, 155 Broad Street N.W. Suite 102, Cleveland, TN, 37311-5000"
    elif county == "Carroll":
        p_address = "Carroll County Office Complex, 625 High Street,  Suite 113, Huntingdon, TN, 38344-1731"
    elif county == "Dyer":
        p_address = "113 W Market, Dyersburg, TN,38024-5009"
    elif county == "Gibson":
        p_address = "1 Court Square, Suite 101, Gibson County Courthouse, Trenton, 38382-1851"
    elif county == "Macon":
        p_address = "607 Hwy 52 Bypass E, Suite C, Lafayette, TN, 37083-1082"
    elif county == "Meigs":
        p_address = "17214 Highway 58 N, Meigs County Courthouse, TN, Decatur, 37322-7472"
    elif county == "Weakley":
        p_address = "135 South Poplar Street, Suite A, TN, Dresden, 38225-1479"

    # print(p_address)
    aschema = format_address_data(address=p_address, county_name=county)
    try:
        bschema = format_address_data(address=m_address, county_name=county)
    except Exception:
        bschema = {}
    try:
        if re.match("Web Site", data[8].text.replace("\n", "").strip()):
            website = data[8].text.replace("\n","").strip()
            website = website.replace("Web Site:", "")
        elif re.match("Web Site", data[7].text.replace("\n", "").strip()):
            website = data[7].text.replace("\n","").strip()
            website = website.replace("Web Site:", "")
    except Exception:
            website = ""
    # print(website)
    schema = formatSchema(county=county, person=person, p_address=aschema,
                          m_address=bschema, phone=phone, website=website)
    masterList.append(schema)

# print(masterList)

with open(os.path.join(ROOT_DIR, "scrapers", "tennessee", "tennessee.json"), 'w') as f:
    json.dump(masterList, f)
