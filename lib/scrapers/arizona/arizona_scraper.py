import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import usaddress
sys.path.append('../../ElectionSaver')

import electionsaver

URL = "https://azsos.gov/county-election-info"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')

all_elems = soup.find_all('div', class_ = 'nobs_body')

county_names = []
for i in soup.find_all('h2', class_ = 'display-hide'):
    county_names.append(i.text.replace('County', ''))

county_info_text = []

for i in all_elems:
    county_info_text.append(i.text)

county_info_text = county_info_text[:15]

actual_info = []
for i in county_info_text:
    actual_info.append(i.split("\n\n\t\t\t")[4])

clerk_name = [i.split('\n\t\t\t\t')[0] for i in actual_info]
building_name = [i.split('\n\t\t\t\t')[1] for i in actual_info]
address_1 = [i.split('\n\t\t\t\t')[2].replace("Physical: ", "") for i in actual_info]
address_1 = [i.split(' (')[0] for i in address_1]
address_2 = []
for i in actual_info:
    if 'Physical:' in i:
        addy = [i.split('\n\t\t\t\t')[4]]
    else:
        addy = [i.split('\n\t\t\t\t')[3]]
    address_2.append(addy)

phone_num = []
for i in county_info_text:
    phone = re.search('Phone - (.*)\n', i)
    phone_num.append(phone.group(1).split(" or")[0])

flatten = lambda l: [item for sublist in l for item in sublist]

address_2 = flatten(address_2)

for n, i in enumerate(address_2):
    if i == 'Phone - 520-724-4330':
        address_2[n] = ''
    if i == 'Suite 101':
        address_2[n] = 'Suite 101, Nogales, Arizona 85621'

full_address = [a + ', ' + b for a, b in zip(address_1, address_2)]

def Find(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]

websites = [Find(i) for i in county_info_text]
websites = [item for sublist in websites for item in sublist][::3]
websites.remove('http://recorder.maricopa.gov/elections/')

masterList = []

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Arizona",
        "zipCode": parsedDataDict['zipCode'],
    }
    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'city' in parsedDataDict:
        finalAddress['city'] = parsedDataDict['city']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    return finalAddress

for i in range(len(county_names)):
    addressSchema = formatAddressData(full_address[i], county_names[i])
    schema = {
        "countyName": county_names[i].strip(),
        "physicalAddress": addressSchema,
        "phone": phone_num[i],
        "officeSupervisor": clerk_name[i],
        "supervisorTitle": building_name[i],
        "website": websites[i]
        }
    masterList.append(schema)

with open('arizona.json', 'w') as f:
    json.dump(masterList, f)