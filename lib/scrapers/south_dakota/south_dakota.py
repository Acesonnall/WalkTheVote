import requests
import re
import usaddress
import os
import json
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
URL = "https://vip.sdsos.gov/CountyAuditors.aspx"

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
        addressSchema["locationName"] = (county_name + " County Courthouse").lower()

    if "aptNumber" in parsed_data_dict:
        addressSchema["aptNumber"] = parsed_data_dict["aptNumber"].lower()

    if "poBox" in parsed_data_dict:
        addressSchema["poBox"] = parsed_data_dict["poBox"].lower()

    if "streetNumberName" in parsed_data_dict:
        addressSchema["streetNumberName"] = parsed_data_dict["streetNumberName"].lower()
#    else:
#        print(f'county_name {county_name} is the culprit')
    return addressSchema

def formatSchema(county, phone, person, p_address, m_address):
    schema = {
        "countyName": county.title(),
        "phone": phone,
        "officeSupervisor": person,
        "website": URL,
        "physicalAddress": p_address,
    }
    if m_address != {}:
        schema["mailingAddress"] = m_address
    return schema

URL = "https://vip.sdsos.gov/CountyAuditors.aspx"

r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

baseList = []

for j in range(0, 66, 1):
    x = soup.find("tr", {"id":str("ctl00_MainContent_rdgCountyAuditors_ctl00"+"__"+str(j))})
    baseList.append(x)

masterList = []

for i in baseList:
    data_row = i.find_all("td")
    county = data_row[0].text
    # print(county)
    person = data_row[1].text + " " + data_row[2].text
    if county == "Aurora":
        p_address = "401 Main St, Plankinton, SD 57368"
    elif county == "Bennett":
        p_address = "205 State St, Martin, SD 57551"
    elif county == "Bon Homme":
        p_address = "300 W Cherry St, Tyndall, SD 57066"
    elif county == "Buffalo":
        p_address = "300 S. Courtland St., Ste. 111, Chamberlain, SD 57325"
    elif county == "Campbell":
        p_address = "111 2nd St, Mound City, SD 57646, USA"
    elif county == "Charles Mix":
        p_address = "400 E Main St, Lake Andes, SD 57356"
    elif county == "Clark":
        p_address = "200 N Commercial St, Clark, SD 57225"
    elif county == "Corson":
        p_address = "1st Ave E, McIntosh, SD 57641"
    elif county == "Deuel":
        p_address = "408 4th St W, Clear Lake, SD 57226"
    elif county == "Dewey":
        p_address = "700 C St, Timber Lake, SD 57656"
    elif county == "Douglas":
        p_address = "706 Braddock St, Armour, SD 57313"
    elif county == "Edmunds":
        p_address = "210 2nd Ave, Ipswich, SD 57451"
    elif county == "Faulk":
        p_address = "110 9th Ave. S. Faulkton SD, 57438"
    elif county == "Gregory":
        p_address = "221 E 8th St, Burke, SD 57523"
    elif county == "Haakon":
        p_address = "140 Howard Ave, Philip, SD 57567"
    elif county == "Hamlin":
        p_address = "300 4th St, Hayti, SD 57241"
    elif county == "Hanson":
        p_address = "300 4th St, Hayti, SD 57241"
    elif county == "Harding":
        p_address = "410 Ramsland St, Buffalo, SD 57720"
    elif county == "Jackson":
        p_address = "700 Main St, Kadoka, SD 57543"
    elif county == "Jerauld":
        p_address = "205 Wallace Ave S, Wessington Springs, SD 57382"
    elif county == "Jones":
        p_address = "310 Main St, Murdo, SD 57559"
    elif county == "Kingsbury":
        p_address = "202 2nd St SW, De Smet, SD 57231"
    elif county == "Lawrence":
        p_address = "78 Sherman St, Deadwood, SD 57732"
    elif county == "Lyman":
        p_address = "300 Main St, Kennebec, SD 57544"
    elif county == "Marshall":
        p_address = "911 Vander Horck St, Britton, SD 57430"
    elif county == "McCook":
        p_address = "130 W Essex Ave, Salem, SD 57058"
    elif county == "McPherson":
        p_address = "706 Main St. Leola, SD 57456"
    elif county == "Mellette":
        p_address = "1st St, White River, SD 57579"
    elif county == "Miner":
        p_address = "401 N Main St, Howard, SD 57349"
    elif county == "Pennington":
        p_address = "315 St Joseph St, Rapid City, SD 57701"
    elif county == "Perkins":
        p_address = "100 E Main St, Bison, SD 57620"
    elif county == "Sanborn":
        p_address = "604 W 6th St, Woonsocket, SD 57385"
    elif county == "Stanley":
        p_address = "8 E 2nd Ave, Fort Pierre, SD 57532"
    elif county == "Sully":
        p_address = "8 E 2nd Ave, Fort Pierre, SD 57532"
    elif county == "Turner":
        p_address = "400 S Main Ave, Parker, SD 57053"
    elif county == "Walworth":
        p_address = "4308 4th Ave, Selby, SD 57472"
    elif county == "Ziebach":
        p_address = "215 S D St, Dupree, SD 57623"
    else:
        p_address = data_row[3].text + ", " + data_row[4].text + ", SD, " + data_row[5].text
    # print(p_address)
    m_address = data_row[3].text + ", " + data_row[4].text + ", SD, " + data_row[5].text
    # print(m_address)
    aschema = format_address_data(address=p_address, county_name=county)
    try:
        bschema = format_address_data(address=m_address, county_name=county)
    except Exception:
        bschema = {}
    if m_address == p_address:
        #         print(f'Physical and mailing are the same for {county} county')
        bschema = {}
    phone = data_row[6].text
    email = i.find("a").get("href")
    schema = formatSchema(county=county, phone=phone, person=person, p_address=aschema, m_address=bschema)
    masterList.append(schema)

with open(os.path.join(ROOT_DIR, "scrapers", "south_dakota", "south_dakota.json"), 'w') as f:
    json.dump(masterList, f)
