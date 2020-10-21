import requests
from bs4 import BeautifulSoup
import re
import json
import usaddress
from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
import os

URL = "https://sos.oregon.gov/elections/Pages/countyofficials.aspx"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')

all_names = soup.findAll('h3')
county_names = [i.text.replace('\n', '').replace('\xa0', '').replace('\u200b', '') for i in all_names][:-1]
all_info = soup.findAll('p')
all_info_text = [i.text.replace('<p class="ms-rteElement-P">', '') for i in all_info][1:]

info_name_add = [i for i in all_info_text if 'Fax' not in i and 'Mailing' not in i and 'TTY' not in i and 'Gold Beach' not in i and '.org' not in i and '\n\n' not in i and '\n\u200b\u200b' not in i]

officer_names = [i.split(',')[0] for i in info_name_add]

test_counties = [str(i).replace('<p class="ms-rteElement-P">', '') for i in all_info if 'OR ' in str(i) and 'Mailing' not in str(i)][1:]

addies = [i.split('<br/>', 1)[1].replace('\xa0', ' ').replace('\r\n   ', '').replace('<br/>', ' ').replace('</p>', '').replace('\u200b', '').strip() for i in test_counties if '<br/>' in i]

addies.insert(0, '1995 3rd St, Suite 150, Baker City, OR 97814-3365')
addies.insert(3, '820 Exchange St, Suite 220, Astoria, OR 97103-4609')
addies.insert(7, '29821 Ellensburg Ave, 2nd Floor, Gold Beach, OR 97444')
addies.insert(8, '1300 NW Wall St, Suite 202, Bend, OR 97703-1960')

addies = [i.replace('\xa0', '') for i in addies]

emails = []

for i in all_info_text:
    emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', i)
    if emailRegex is None:
        emails.append('None')
    else:
        emails.append(emailRegex.group(0))

emails = [i for i in emails if i != 'None']
emails = [i[12:] if len(i) > 22 else i for i in emails]
emails.insert(3, 'clerk@co.clatsop.or.us​')
emails = [i.replace('\u200b', '') for i in emails]

phone_nums = [i.split('/TTY')[0].replace('\n', '').strip()[:12] for i in all_info_text if 'TTY' in i]
phone_nums.insert(3, '503-325-8511')
lane_ind = county_names.index('Lane')
phone_nums.insert(lane_ind, '541-682-4234')

websites = ['https://sos.oregon.gov/elections/Pages/countyofficials.aspx'] * len(county_names)
officer_positions = [i + ' County Clerk' for i in county_names]
loc_names = [i + ' County Election Office' for i in county_names]

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Oregon",
        "zipCode": parsedDataDict["zipCode"],
    }
    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"]
        if countyName == "Baker":
            finalAddress["streetNumberName"] = "1995 3rd St"
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
    real_address = formatAddressData(addies[i], county_names[i])
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

with open(os.path.join(ROOT_DIR, "scrapers", "oregon", "oregon.json"), "w") as f:
    json.dump(masterList, f)