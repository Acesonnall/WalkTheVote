import requests
import json
from bs4 import BeautifulSoup 
import re 
import json 
import pandas as pd

URL = "https://vt.ncsbe.gov/BOEInfo/PrintableVersion/"
r = requests.get(URL)
soup = BeautifulSoup(r.content, 'html5lib')
all_elems = soup.find_all('script')
test = all_elems[16].text.split("var data = ")[1].split("// initialize")[0]
json.loads(test)
all_elems_js = json.loads(test)

to_del = ['Coordinates', 'CountyId', 'DirectorName', 'MapLink', 'OfficeName', 'OfficePhoneNumExt', 'MailingAddr1', 'MailingAddr2', 'MailingAddrCSZ']

for element in all_elems_js: 
    [element.pop(key) for key in to_del] 
    newAddy = element['PhysicalAddr1'] + ' ' + element['PhysicalAddr2'] + element['PhysicalAddrCSZ']
    element['newAddress'] = newAddy

addr_del = ['PhysicalAddr1', 'PhysicalAddr2', 'PhysicalAddrCSZ']
for element in all_elems_js: 
    [element.pop(key) for key in addr_del]

print(all_elems_js)