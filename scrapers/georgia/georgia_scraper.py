import requests
from bs4 import BeautifulSoup 
import re 
import json 
import csv
import io
import urllib3
import pandas as pd

def format_address(info_str):
    info_str = info_str.replace('\n<br/>', ' ')
    info_str = info_str.replace('<br/>\n', ' ')
    info_str = info_str.replace('<br/>', ' ')

    start_ind = info_str.index('</h4>') + 5
    end_ind = info_str.index('</td>')

    address = info_str[start_ind:end_ind].strip()
    address = address.replace('\n', ', ')
    address = address.replace('  ', ' ')

    return address

def get_phone_number(info_str):
    phone_num_index = info_str.index('Telephone: ') + len('Telephone: ')

    phone_number = []
    for c in info_str[phone_num_index:]:
        if str.isdigit(c):
            phone_number.append(c)
        elif c in ['(', ')', '-', ' ']:
            phone_number.append(c)
        else:
            break
    print(phone_number)
    return ''.join(phone_number)

f = open("./log.txt", "w")

# Get list of county names from registrar to populate form
registrar_url = 'https://elections.sos.ga.gov/Elections/countyregistrars.do'
r = requests.get(registrar_url)
soup = BeautifulSoup(r.content, 'html5lib')
county_option_list = soup.findAll(attrs={"name" : "idTown"})[0].findAll('option')

id_list = [county_option['value'] for county_option in county_option_list]
county_list = [county_option.string for county_option in county_option_list]

# Use list of counties and IDs to get county info for each county
info_url = 'https://elections.sos.ga.gov/Elections/contactinfo.do'

county_info = {}

for i in range(len(id_list)):
    county_id = id_list[i]
    county_name = county_list[i]
    r = requests.post(info_url, data={'idTown':county_id,'SubmitCounty':'Submit','contactType':'R'})
    soup = BeautifulSoup(r.content, 'html5lib')
    table = soup.find("table", {'id':'Table1'})
    rows = table.find_all("tr")

    phys_info_str, mail_info_str, phone_number = '', '', ''

    if 'Physical Address:' in rows[0].getText() and 'SAME AS ABOVE' not in rows[0].getText():
        phys_info_str = str(rows[0])
        phys_address = format_address(phys_info_str)

    mail_info_str = str(rows[1])
    mail_address = format_address(mail_info_str)

    if 'Telephone: ' in rows[2].getText():
        contact_info_str = rows[2].getText()
        phone_number = get_phone_number(contact_info_str)
