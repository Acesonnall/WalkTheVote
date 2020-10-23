import requests
from bs4 import BeautifulSoup
import re
import json
import usaddress
from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
import os

URL = "https://elections.maryland.gov/about/county_boards.html"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

all_info = soup.findAll('p')
all_info_text = [str(i).replace('<p><strong>', '').replace('</strong>', '') for i in all_info][:24]
county_names = [i.split('<br/>')[0] for i in all_info_text]
for n, i in enumerate(county_names):
    if i == "Baltimore County":
        county_names[n] = "Baltimore"

addies = [i.split('MD ')[0] for i in all_info_text]
addies = [i.split('<br/>', 1)[1].replace('\r\n', ' ').replace('<br/>', ' ').replace('Street Address: ', '').replace('<br>', '').replace('Mailing Address: P.O. Box 353 - Easton', '').strip() for i in addies]
zipcodes = [i.split('MD ')[1] for i in all_info_text]
zipcodes = [i.split('<br/>')[0] for i in zipcodes]
full_addies = [i + ', MD ' + j for i, j in zip(addies, zipcodes)]

for n, i in enumerate(full_addies):
    if i == "215 Bay Street, Easton MD, 21601, MD 21601-0353":
        full_addies[n] = "215 Bay Street, Easton MD, 21601"

emails = []

for i in all_info_text:
    email = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', i)
    emails.append(email.group(0))

test = [i.split('<br/>') for i in all_info_text]
test_flat = [item for sublist in test for item in sublist]

fax_ind = [i for i, s in enumerate(test_flat) if '(Fax)' in s or '(fax)' in s]
phone_ind = [i - 1 for i in fax_ind]
phone_nums = [test_flat[i].replace('\r\n', '').strip()[:12] for i in phone_ind]

officers = [i.replace('\r\n', '').strip() for i in test_flat if 'Election Director' in i]
officer_names = [i.split(',')[0] for i in officers]
officer_positions = [i.split(',')[1] for i in officers]


def Find(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]

websites = [Find(i) for i in all_info_text]
websites = [item for sublist in websites for item in sublist]
websites = [i for i in websites if 'google' not in i][::2]
websites.remove('http://boe.baltimorecity.gov')
websites.remove('http://www.harfordcountymd.gov/elections/')
loc_names = [i + ' County Election Office' for i in county_names]

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Maryland",
        "zipCode": parsedDataDict["zipCode"],
    }
    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"]
    if "city" in parsedDataDict:
        finalAddress["city"] = parsedDataDict["city"]
    if "poBox" in parsedDataDict:
        finalAddress["poBox"] = parsedDataDict["poBox"]
    if "locationName" in parsedDataDict:
        finalAddress["locationName"] = parsedDataDict["locationName"]
    if "aptNumber" in parsedDataDict:
        finalAddress["aptNumber"] = parsedDataDict["aptNumber"]
    return finalAddress

masterList = []

for i in range(len(county_names)):
    real_address = formatAddressData(full_addies[i], county_names[i])
    if "locationName" not in real_address:
        real_address["locationName"] = loc_names[i]

    schema = {
        "countyName": county_names[i],
        "physicalAddress": real_address,
        "phone": phone_nums[i],
        "email": emails[i],
        "officeSupervisor": officer_names[i],
        "supervisorTitle": officer_positions[i],
        "website": websites[i],
    }
    masterList.append(schema)

with open(os.path.join(ROOT_DIR, "scrapers", "maryland", "maryland.json"), "w") as f:
    json.dump(masterList, f)
