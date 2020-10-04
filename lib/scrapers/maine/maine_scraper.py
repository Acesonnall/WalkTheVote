import requests
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import usaddress
import sys
sys.path.append('../../ElectionSaver')

import electionsaver

URL = "https://www.maine.gov/sos/cec/elec/munic.html"
t_file = "https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text"
url_data = pd.read_table(t_file, sep = '|')
r = requests.get(URL, verify=False)
soup = BeautifulSoup(r.content, 'html5lib')

all_names = soup.findAll('h2')
county_names = [i.text for i in all_names]
county_names = county_names[2:]
county_names.remove('Lincoln Plt')
county_names.remove('Magalloway Plt')

all_info = soup.findAll('dd')
county_info = [i.text.strip('\n') for i in all_info]
county_info = county_info

phone_nums = []
for i in county_info:
    phone = re.search('Phone: (.*)\nFax', i)
    if phone is None:
        phone_nums.append('None')
    else:
        phone_nums.append(phone.group(1))

phone_num_real = [x for x in phone_nums if x != 'None' and x != ' NH  03579']

for pos, i in enumerate(phone_num_real):
    if i == 'Deblois, ME  04622':
        phone_num_real[pos] = 'None'

county_info_t = pd.DataFrame(url_data)
county_info_t = county_info_t[county_info_t['133 Main Road'] != '226 Wilsons Mills Road']
init_info = county_info_t.columns.tolist()
new_init_info = []

for string in init_info:
    new_string = string.replace("<plaintext>Abbot", "Abbot")
    new_init_info.append(new_string)

add1 = county_info_t['133 Main Road'].tolist()
add2 = county_info_t['Abbot, ME  04406'].tolist()
add1.insert(0, "133 Main Road")
add2.insert(0, "Abbot, ME 04406")
address = [i + " " + j for i, j in zip(add1, add2)]

for pos, i in enumerate(address):
    if i == ' Luckings Gay Route 193':
        address[pos] = '8 Lane Road, Deblois, ME 04622'

clerk_names = county_info_t['Lorna Flint Marshall'].tolist()
clerk_names.insert(0, 'Lorna Flint Marshall')
clerk_positions = ['Municipal Clerk'] * len(county_names)
location_names = [i + ' County Election Office' for i in county_names]
websites = ['https://www.maine.gov/sos/cec/elec/munic.html'] * len(county_names)

def formatAddressData(addressData, countyName):
    mapping = electionsaver.addressSchemaMapping
    parsedDataDict = usaddress.tag(addressData, tag_mapping=mapping)[0]
    try:
        finalAddress = {
            "city": parsedDataDict['city'],
            "state": parsedDataDict['state'],
            "zipCode": parsedDataDict['zipCode']
        }
    except:
        print(f'Error with data {parsedDataDict}')

    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']
    return finalAddress


masterList = []
for i in range(len(county_names)):
    real_address = formatAddressData(address[i], county_names[i])
    if 'locationName' not in real_address:
        real_address['locationName'] = location_names[i]

    schema = {
        "countyName": county_names[i],
        "physicalAddress": real_address,
        "phone": phone_num_real[i],
        "officeSupervisor": clerk_names[i],
        "supervisorTitle": clerk_positions[i],
        "website": websites[i]
    }
    masterList.append(schema)


with open("maine.json", "w") as f:
    json.dump(masterList, f)

