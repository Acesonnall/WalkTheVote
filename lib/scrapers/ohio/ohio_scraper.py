import requests 
from bs4 import BeautifulSoup
import re
import json
import sys
import usaddress
sys.path.append('../../ElectionSaver')

import electionsaver

URL = "https://www.sos.state.oh.us/elections/elections-officials/county-boards-of-elections-directory/"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')

office_elems = soup.find_all('div', class_='wysiwyg-content')
name_elems = soup.find_all('div', class_ = 'list-item-blocks-grid__title')
county_names = []

for i in name_elems:
    c_name = i.text
    county_names.append(c_name.replace(' County', ''))

all_elems = []
for i in office_elems:
    if "Telephone" in i.text:
        all_elems.append(i.text)

phone = []
addies = []
ohours = []
websites = []

for i in all_elems:
    office_hours = re.search('Office Hours: (.*) Telephone', i)
    phone_num = re.search('Telephone: (.*) Fax', i)
    address = re.search('\nGet Directions  (.*) Office', i)
    website = re.search('Website:(.*)\n\t', i)
    if office_hours is None:
        ohours.append('None')
    else:
        ohours.append(office_hours.group(1).strip().replace(' Telephone: (614) 525-3100 Absentee Department', ''))
    if phone_num is None:
        phone.append('None')
    else:
        phone.append(phone_num.group(1).strip('\xa0').replace(' or (614) 322-5270 ', '').replace('Absentee Department Telephone: (614) 525-3470', '').strip())
    if address is None:
        addies.append('None')
    else:
        addies.append(address.group(1))
    if website is None:
        websites.append('None')
    else:
        websites.append(website.group(1).strip())

phone_replace = ['(419) 674-2211', '(419) 213-4001 ']
addies_replace = ['111 S. Nelson Ave., Suite 4 Wilmington, OH 45177', '104 East Sugar St. Mt. Vernon, OH 43050', 'Ohio Means Jobs Building 1301 Monroe Street Toledo, OH 43604', '627 Market Street Zanesville, OH 43701', '470 Grant St. Akron, OH 44311', '1362 East Ervin Road Van Wert, OH 45891']

counter = 0
for pos, i in enumerate(phone):
    if i == 'None':
        phone[pos] = phone_replace[counter]
        counter += 1

for pos, i in enumerate(ohours):
    if i == 'None':
        ohours[pos] = '8:30 a.m. - 4:30 p.m. (Monday - Friday)'

count = 0
for pos, i in enumerate(addies):
    if i == 'None':
        addies[pos] = addies_replace[count]
        count += 1

addies = [i.split('Mailing')[0].strip().replace('\xa0', '') for i in addies]
websites = ['www.' + i if i[:4] != 'www.' else i for i in websites]
email_add = [i.lower()[:8].replace(' ', '') + '@OhioSoS.gov' for i in county_names]
loc_name = [i + ' County Election Office' for i in county_names]

masterList = []

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping
    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Ohio",
        "zipCode": parsedDataDict["zipCode"],
    }
    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"]
    else:
        if countyName == "Vinton":
            finalAddress["streetNumberName"] = "31935 OH-93"
    if "city" in parsedDataDict:
        finalAddress["city"] = parsedDataDict["city"]
    if "poBox" in parsedDataDict:
        finalAddress["poBox"] = parsedDataDict["poBox"]
    if "locationName" in parsedDataDict:
        finalAddress["locationName"] = parsedDataDict["locationName"]
        if countyName == "Vinton":
            finalAddress["locationName"] = "Community Building"
    if "aptNumber" in parsedDataDict:
        finalAddress["aptNumber"] = parsedDataDict["aptNumber"]
        if countyName == "Vinton":
            finalAddress.pop("aptNumber")
    return finalAddress

for i in range(len(county_names)):
    real_address = formatAddressData(addies[i], county_names[i])
    if "locationName" not in real_address:
        real_address["locationName"] = loc_name[i]

    schema = {
        "countyName": county_names[i],
        "physicalAddress": real_address,
        "phone": phone[i],
        "email": email_add[i],
        "website": websites[i],
    }

    masterList.append(schema)

with open('ohio.json', 'w') as f:
    json.dump(masterList, f)