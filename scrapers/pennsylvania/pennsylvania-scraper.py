import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import usaddress
sys.path.append('../../ElectionSaver')

import electionsaver

URL = "https://www.votespa.com/Resources/Pages/Contact-Your-Election-Officials.aspx"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')

all_names = soup.findAll('option')
county_names = [i.text.replace(' County', '') for i in all_names]
county_names = county_names[1:]
all_info = soup.findAll('script', type = "text/javascript")
all_info = all_info[34]

county_info = []

tmp1 = all_info.string.split('MapPopup.init(')[1]
tmp2 = tmp1.split(');var')[0]
data = json.loads(tmp2)
subdata = data['data']
items = subdata['Items']
county_info_text = []
websites = []
for i in items:
    tag = items[i][3]['FieldContent']
    website = items[i][5]['FieldContent'].split(',')[0]
    if website == "":
        website = "https://www.sullivancounty-pa.us/offices/election-bureau"
    websites.append(website)
    subsoup = BeautifulSoup(tag, 'html.parser')
    county_info_text.append(str(subsoup))

emails = []
phone_nums = []
for i in county_info_text:
    emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', i)
    phoneRegex = re.search(r'(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$', i)
    if emailRegex is None:
        emails.append('None')
    else:
        emails.append(emailRegex.group(0))
    if phoneRegex is None:
        phone_nums.append('None')
    else:
        phone_nums.append('(' + phoneRegex.group(0)[:13].split('<br/>')[0].strip('<'))

phone_replace = ['(610) 891-4673', '(570) 278-4600', '(814) 432-9508']
counter = 0
for pos, i in enumerate(phone_nums):
    if i == 'None':
        phone_nums[pos] = phone_replace[counter]
        counter += 1

all = []

for i in county_info_text:
    info = re.search('<br/>(.*)<br/>', i)
    if info is None:
        all.append('None')
    else:
        all.append(info.group(0))

name_remove = ['Chief', 'Director', 'Government']
address_2 = []
for i in all:
    lists = i.split('<br/>')
    for j in lists:
        if 'PA' in j:
            address_2.append(j)

address_2 = address_2[:-1]
address_2_ind = []
for i in all:
    lists = i.split('<br/>')
    for j in lists:
        if 'PA' in j:
            address_2_ind.append(lists.index(j))

for pos, i in enumerate(address_2):
    if 'Montgomery' in i:
        address_2[pos] = 'Norristown, PA 19401'

address_1_ind = [i - 1 for i in address_2_ind][:-1]
address_0_ind = [i - 2 for i in address_2_ind][:-1]
clerk_pos_ind = [i - 3 for i in address_2_ind][:-1]

address_1 = []
address_0 = []
clerk_pos_init_0 = []
all_lists = []
for i in all:
    lists = i.split('<br/>')
    all_lists.append(lists)

for index, lst in enumerate(all_lists):
    indexToFind_1 = address_1_ind[index]
    indexToFind_0 = address_0_ind[index]
    clerkInd = clerk_pos_ind[index]
    address_1.append(lst[indexToFind_1])
    address_0.append(lst[indexToFind_0])
    clerk_pos_init_0.append(lst[clerkInd])

for pos, i in enumerate(address_0):
    if 'Director' in i or 'Clerk' in i or 'Sisler' in i or 'Tioga' in i or 'Lackawanna' in i:
        address_0[pos] = 'None'

full_address = [a.replace('None', '') + ' ' + b + ' ' + c for a, b, c in zip(address_0, address_1, address_2)]

full_address = [i.strip() for i in full_address]

clerk_pos_init = []
clerk_pos_real = []

for index, lst in enumerate(all_lists):
    indexToFind_0 = address_0_ind[index]
    clerk_pos_init.append(lst[indexToFind_0])

for i in clerk_pos_init:
    if 'Director' in i or 'Clerk' in i or 'Director' in i or 'Chief' in i:
        clerk_pos_real.append(i)
    else:
        clerk_pos_real.append('None')

clerk_pos_real_0 = []
for i in clerk_pos_init_0:
    if 'Director' in i or 'Clerk' in i or 'Supervisor' in i or 'Secretary' in i or 'Designee' in i or 'Manager' in i:
        clerk_pos_real_0.append(i)
    else:
        clerk_pos_real_0.append('None')

full_clerk = [a.replace('None', '') + b.replace('None', '') for a, b in zip(clerk_pos_real, clerk_pos_real_0)]
for pos, i in enumerate(full_clerk):
    if i == '':
        full_clerk[pos] = 'Director of Elections'

full_clerk = [i.replace('<p>', '').replace('</p>', '').replace('Cambria County', '') for i in full_clerk]

clerk_names_0 = []
for i in county_info_text:
    name = re.search('\u200b(.*)<br/>', i)
    if name is None:
        clerk_names_0.append('None')
    else:
        clerk_names_0.append(name.group(0))

clerk_names_real = []
for i in clerk_names_0:
    if '<p>' in i:
        name = re.search('<p>(.*)<br/>', i)
    elif 'None' in i:
        name = 'None'
    else:
        name = re.search('\u200b(.*)<br/>', i)
    if name == 'None':
        clerk_names_real.append('None')
    else:
        clerk_names_real.append(name.group(1).split('<br/>')[0].replace('\xa0', '').split('<')[0])

clerk_replace = ['None', 'Tina Kiger', 'None', 'Nadeen Manzoni', 'Ms. Lisa R. Rivett', 'Melanie R. Ostrander', 'Ms. Florence Kellett']

counter = 0
for pos, i in enumerate(clerk_names_real):
    if i == 'None':
        clerk_names_real[pos] = clerk_replace[counter]
        counter += 1
    elif i == 'Director, Chester Co. Voter Svcs':
        clerk_names_real[pos] = 'None'
    elif i == 'Ms. ':
        clerk_names_real[pos] = 'Ms. Macy Rudock'

masterList = []

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    if countyName == "Monroe":
        address = 'Historic Courthouse 326 Laurel St Ste 22 Brainerd, MN 56401'

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Pennsylvania",
        "zipCode": parsedDataDict['zipCode'],

    }

    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
        if countyName == "Monroe":
            finalAddress['streetNumberName'] = "One Quaker Plaza"
    else:
        if countyName == "Montgomery":
            finalAddress['streetNumberName'] = "425 Swede St."
        print(f'{countyName} County might be a mailing address...')

    if 'city' in parsedDataDict:
        finalAddress['city'] = parsedDataDict['city']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
        if countyName == "Montgomery":
            finalAddress['locationName'] = 'Montgomery County Voter Services'
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
        if countyName == "Monroe":
            finalAddress['aptNumber'] = "Rm. 105"
        if countyName == "Montgomery":
            finalAddress['aptNumber'] = "Suite 602"
    return finalAddress

for i in range(len(county_names)):
    real_address = formatAddressData(full_address[i], county_names[i])
    schema = {
        "countyName": county_names[i],
        "physicalAddress": real_address,
        "phone": phone_nums[i],
        "email": emails[i],
        "officeSupervisor": clerk_names_real[i],
        "supervisorTitle": full_clerk[i],
        "website": websites[i]
        }
    if emails[i] == 'None':
        schema.pop('email')
    if full_clerk[i] == 'None':
        schema.pop('supervisorTitle')
    if clerk_names_real[i] == 'None':
        schema.pop('officeSupervisor')
    masterList.append(schema)

with open('pennsylvania.json', 'w') as f:
    json.dump(masterList, f)