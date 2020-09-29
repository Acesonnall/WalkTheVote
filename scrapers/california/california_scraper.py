import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import usaddress
sys.path.append('../../ElectionSaver')

import electionsaver

URL = "https://www.sos.ca.gov/elections/voting-resources/county-elections-offices/"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')

all_names = soup.findAll('h2')
county_names = [i.text.strip('\xa0') for i in all_names]
county_names = county_names[:-4]

all_info = soup.findAll('li')
county_info = [i.text.strip('\xa0') for i in all_info]
county_info = county_info[18:500]

no_emails = ['Alameda', 'Sutter', 'Ventura']
no_email_index = [county_names.index(i) for i in no_emails]

emails = [i.strip('E-Mail:').replace('\xa0', '') for i in county_info if 'E-Mail:' in i]
hours = [i.strip('Hours: ').strip('(707) 263-2742 FaxHours:') for i in county_info if 'Hours: ' in i]
phone = [i.strip(', option 1') for i in county_info if '(' in i
         and 'Fax' not in i
         and '(800)' not in i
         and '(888)' not in i
         and 'Library' not in i
         and 'Hall' not in i
         and '(916) 375-6490' not in i
         and '(866)' not in i]

add_id = ['Street', 'Road', 'Ave', 'Court ', 'lane', 'Blvd', 'Hwy', 'Drive', 'Place', 'St.', 'Real', 'Square', 'Memorial']

addresses = []
real_addresses = []
for i in county_info:
    for j in add_id:
        if j in i and 'CA' not in i:
            addresses.append(i)

#function to remove duplicates
def rem_dups(add, real_add):
    for i in add:
        if i not in real_add:
            real_add.append(i)

rem_dups(addresses, real_addresses)

add_index = []
real_add_index = []
for i in real_addresses:
    for j in county_info:
        if i == j:
            add_index.append(county_info.index(j))

rem_dups(add_index, real_add_index)

clerks = [i.replace('\xa0', '') for i in county_info if ',' in i and 'CA' not in i
              and 'Room' not in i
              and 'Suite' not in i
              and 'Street' not in i
              and 'Hours' not in i
              and 'Floor' not in i
              and 'Drive' not in i
              and 'Avenue' not in i
              and 'option' not in i
              and 'Hall' not in i]

clerk_name = [i.split(',')[0] for i in clerks]
clerk_position = [i.split(',')[1].strip() for i in clerks]

real_add_index_2 = [i + 1 for i in real_add_index]
real_addresses_2 = [county_info[i] for i in real_add_index_2]

replace_adds = ['Martinez, CA 94553', 'San Francisco, CA 94102-4635', 'Downieville, CA 95936-0398', 'Ventura, CA 93009-1200']

counter = 0
for pos, i in enumerate(real_addresses_2):
    if 'CA' not in i:
        real_addresses_2[pos] = replace_adds[counter]
        counter += 1

for i in no_email_index:
    emails.insert(i, "None")

emails = [i.strip(' ') for i in emails]

ind_LA = county_names.index('Los Angeles')
phone.insert(ind_LA, '(800) 815-2666')

masterList = []

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping
    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    try:
        finalAddress = {
            "city": parsedDataDict["city"],
            "state": parsedDataDict['state'],
            "zipCode": parsedDataDict['zipCode'],
        }
    except:
        print(f'Error with data for {countyName} county, data is {parsedDataDict}')

    return finalAddress

def formatStreetNumber(streetNumberName, countyName):
    mapping = electionsaver.addressSchemaMapping

    if countyName == "Glenn":
        streetNumberName = streetNumberName.replace(', 2nd Street', '')

    parsedDataDict = usaddress.tag(streetNumberName, tag_mapping=mapping)[0]

    finalAddress = {}

    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']

    if countyName == "San Francisco":
        finalAddress = {
            "streetNumberName": "1 Dr. Carlton B Goodlett Place",
            "locationName": "City Hall",
            "aptNumber": "Room 48"
        }

    #print(f'Error with data for {countyName} county, data is {parsedDataDict}')

    return finalAddress



for i in range(len(county_names)):
    addressSchema = formatAddressData(real_addresses_2[i], county_names[i])
    streetSubSchema = formatStreetNumber(real_addresses[i], county_names[i])
    if 'streetNumberName' in streetSubSchema:
        addressSchema['streetNumberName'] = streetSubSchema['streetNumberName']
    if 'aptNumber' in streetSubSchema:
        addressSchema['aptNumber'] = streetSubSchema['aptNumber']
    if 'locationName' in streetSubSchema:
        addressSchema['locationName'] = streetSubSchema['locationName']
    schema = {
        "countyName": county_names[i],
        "streetNumberName": addressSchema,
        "phone": phone[i],
        "officeSupervisor": clerk_name[i],
        "supervisorTitle": clerk_position[i],
        "email": emails[i]
        }

    noEmailsLocal = ["Merced", "Alameda", "Ventura", "Sutter"]
    if county_names[i] in noEmailsLocal:
        schema.pop('email')

    masterList.append(schema)

#print(masterList)

with open('_california.json', 'w') as f:
    json.dump(masterList, f)