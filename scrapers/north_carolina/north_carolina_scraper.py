import requests
import json
from bs4 import BeautifulSoup 
import re 
import json 
import pandas as pd
import usaddress
import sys
sys.path.append('../../ElectionSaver')

import electionsaver

def formatAddressData(addressData, countyName):
    mapping = electionsaver.addressSchemaMapping
    if countyName == "MITCHELL":
        addressData = addressData.replace('108BAKERSVILLE', '108 BAKERSVILLE')
    if countyName == "BURKE":
        addressData = addressData.replace('100MORGANTON', '100 MORGANTON')
    if countyName == "JACKSON":
        addressData = addressData.replace('1SYLVA', '1 SYLVA')
    if countyName == "ROWAN":
        addressData = addressData.replace('D10SALISBURY', 'D10 SALISBURY')
    if countyName == "SAMPSON":
        addressData = addressData.replace('110CLINTON', '110 CLINTON')
    if countyName == "YANCEY":
        addressData = addressData.replace('2BURNSVILLE', '2 BURNSVILLE')
        
    parsedDataDict = usaddress.tag(addressData, tag_mapping=mapping)[0]

    finalAddress = {
        "city": parsedDataDict['city'],
        "state": parsedDataDict['state'],
        "zipCode": parsedDataDict['zipCode']
    }

    if 'streetNumberName' in parsedDataDict:
        finalAddress['streetNumberName'] = parsedDataDict['streetNumberName']
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']    
    return finalAddress

URL = "https://vt.ncsbe.gov/BOEInfo/PrintableVersion/"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html.parser')
all_elems = soup.find_all('script')
test = str(all_elems[16]).split("var data = ")[1].split("// initialize")[0]

json.loads(test)
all_elems_js = json.loads(test)

to_del = ['Coordinates', 'CountyId', 'MapLink', 'OfficeName', 'OfficePhoneNumExt', 'MailingAddr1', 'MailingAddr2', 'MailingAddrCSZ']

def renameKey(src, dest):
    for element in all_elems_js:
        element[dest] = element[src]
        element.pop(src)

for element in all_elems_js: 
    [element.pop(key) for key in to_del] 
    newAddy = element['PhysicalAddr1'] + ' ' + element['PhysicalAddr2'] + element['PhysicalAddrCSZ']
    cleanedData = formatAddressData(newAddy, element['Name'])
    element['newAddress'] = cleanedData

renameKey('Name', 'countyName')
renameKey('newAddress', 'physicalAddress')
renameKey('OfficePhoneNum', 'phone')
renameKey('Email', 'email')
renameKey('OfficeHours', 'officeHours')
renameKey('DirectorName', 'officeSupervisor')
renameKey('WebsiteAddr', 'website')

addr_del = ['PhysicalAddr1', 'PhysicalAddr2', 'PhysicalAddrCSZ', 'FaxNum']
for element in all_elems_js: 
    [element.pop(key) for key in addr_del]

with open('north_carolina.json', 'w') as f:
    json.dump(all_elems_js, f)
