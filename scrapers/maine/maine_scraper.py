import requests
from bs4 import BeautifulSoup 
import re 
import json 
import csv
import io
import urllib3
import pandas as pd
import usaddress
import sys
sys.path.append('../../ElectionSaver')

import electionsaver

t_file = "https://www.maine.gov/tools/whatsnew/index.php?topic=cec_clerks_registrars&v=text"

url_data = pd.read_table(t_file, sep = '|')

county_info = pd.DataFrame(url_data)

init_info = county_info.columns.tolist() 
new_init_info = []

for string in init_info: 
    new_string = string.replace("<plaintext>Abbot", "Abbot")
    new_init_info.append(new_string)

phone = county_info['(207) 876-3198'].tolist()
county = county_info['<plaintext>Abbot'].tolist()
add1 = county_info['133 Main Road'].tolist()
add2 = county_info['Abbot, ME  04406'].tolist()
firstlast = county_info['Lorna Flint Marshall'].tolist()

county.insert(0, "Abbot")
add1.insert(0, "133 Main Road")
add2.insert(0, "Abbot, ME 04406")
phone.insert(0, "(207) 876-3340")
firstlast.insert(0, "Lorna Flint Marshall")

address = [i + " " + j for i, j in zip(add1, add2)]

def formatAddressData(addressData):
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
for i in range(len(county)):
    schema = {
        "countyName": county[i],
        "physicalAddress": formatAddressData(f'{add1[i]} {add2[i]}'),
        "phone": phone[i],
        "officeSupervisor": firstlast[i]
    }
    masterList.append(schema)


with open("maine.json", "w") as f:
    json.dump(masterList, f)

