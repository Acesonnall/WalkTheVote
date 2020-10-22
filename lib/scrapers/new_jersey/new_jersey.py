import cloudscraper
import usaddress
import os
import json
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR

URL = "https://www.state.nj.us/state/elections/vote-county-election-officials.shtml"

scraper = cloudscraper.create_scraper()
r = scraper.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

info1 = soup.find_all("div", {"class":"card"})
# print(info1)

for br in info1:
    br.replace_with("\n")

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
        addressSchema["poBox"] = parsed_data_dict["poBox"].lower()
    if "streetNumberName" in parsed_data_dict:
        addressSchema["streetNumberName"] = parsed_data_dict["streetNumberName"].lower()
    # else:
        # print(f'county_name {county_name} is the culprit')
    return addressSchema

def formatSchema(county, phone, person, p_address, m_address, URLx):
    schema = {
        "countyName": county.title(),
        "phone": phone,
        "officeSupervisor": person,
        "website": URLx,
        "physicalAddress": p_address,
    }
    if m_address != {}:
        schema["mailingAddress"] = m_address
    return schema


masterlist = []

for i in info1:
    county = i.find("a", class_="card-link").text.replace(" County", "").strip()
    # print(county)
    datapoint1 = i.find_all("div", class_="col-sm-4")
    # print(datapoint1[1])

    # Midpoint for mailing address, person
    try:
        datapoint2 = datapoint1[1].text.split("\n")
    except Exception:
        pass
    # Midpoint for p_address, phone, website
    try:
        datapoint3 = datapoint1[2].text.split("\n")
    except Exception:
        pass


    # Got got
    person = datapoint2[2].strip()
    # print(person)

    # Getting P_address
    if county == "Camden":
        m_address = "P.O. Box 218, Blackwood, NJ 08012-0218"
    elif county == "Gloucester":
        m_address = "Court House, P.O. Box 129, 1 North Broad Street, Woodbury, NJ 08096-7129"
    else:
        m_address = datapoint2[3].strip().replace("Address: ", "")
    bschema = format_address_data(address=m_address,county_name=county)
    # print(m_address)
    # Fix this
    if county == "Camden":
        p_address = "Historic Court House Complex, 5903 Main Street, Mays Landing, NJ 08330"
    elif county == "Salem":
        p_address = "Fifth Street Complex, 110 Fifth St, Suite 1000, Salem, NJ 08079"
    else:
        p_address = datapoint3[2].strip().replace("Address: ", "")
    # print(p_address)
    aschema = format_address_data(address=p_address, county_name=county)
    # print(p_address)
    # getting phone
    if county == "Camden":
        phone = "856-225-7219"
    else:
        datas = datapoint1[2].find_all("strong")
        phone = datas[1].text
        # getting phone
    if county == "Atlantic":
        URL = "www.atlantic-county.org/board-of-elections/"
    elif county == "Camden":
        URL = "www.camdencounty.com/service/board-of-elections/"
    elif county == "Gloucester":
        URL = "www.co.gloucester.nj.us/depts/ e/eoff/boe/default.asp"
    elif county == "Hudson":
        URL = "www.hudsoncountyclerk.org"
    elif county == "Mercer":
        URL = "www.mercercounty.org/ boards-commissions/board-of-elections"
    elif county == "Morris":
        URL = "elections.morriscountynj.gov"
    elif county == "Passaic":
        URL = "www.passaiccountynj.org/government/boards_committees_and_commissions/board_of_elections/index.php"
    elif county == "Sussex":
        URL = "www.sussex.nj.us/cit-e-access/webpage.cfm?TID=7&TPID=1503"
    elif county == "Salem":
        URL = "elections.salemcountynj.gov"
    else:
        URL = datapoint3[4].strip().replace(" ", "").replace("Website:", "").strip()
    schema = formatSchema(county=county, phone=phone, person=person, p_address=aschema, m_address=bschema, URLx=URL)
    masterlist.append(schema)

# print(masterlist)

with open(os.path.join(ROOT_DIR, "scrapers", "new_jersey", "new_jersey.json"), 'w') as f:
    json.dump(masterlist, f)
