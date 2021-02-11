import json
import usaddress
from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
import os

county_names = ['Kent', 'New Castle', 'Sussex']
loc_names = [i + ' County Office' for i in county_names]
addies = ['905 S. Governors Ave Ste 170 Dover DE 19904',
          'Carvel State Office Building, 820 North French St Suite 400, Wilmington DE 19801',
          '119 N. Race St, Georgetown DE 19947']
phone_nums = ['(302) 739-4498', '(302) 577-3464', '(302) 856-5367']
emails = ['votekc@delaware.gov', 'votencc@delaware.gov', 'votesc@delaware.gov']
officer_names = ['Ralph Artigliere', 'Tracey N. Dixon', 'Kenneth A. McDowell']
officer_positions = ["County Director"] * len(county_names)
websites = ['https://elections.delaware.gov/locations.shtml'] * len(county_names)

def formatAddressData(address, countyName):
    mapping = electionsaver.addressSchemaMapping

    parsedDataDict = usaddress.tag(address, tag_mapping=mapping)[0]

    finalAddress = {
        "state": "Delaware",
        "zipCode": parsedDataDict["zipCode"],
    }
    if "streetNumberName" in parsedDataDict:
        finalAddress["streetNumberName"] = parsedDataDict["streetNumberName"]
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

with open(os.path.join(ROOT_DIR, "scrapers", "delaware", "delaware.json"), "w") as f:
    json.dump(masterList, f)