import requests
from bs4 import BeautifulSoup as bs
import re
import json
import random
import usaddress
from string import printable

requests.packages.urllib3.disable_warnings() 

BASE_URL = "https://mvic.sos.state.mi.us/Clerk"

# found via Network tab in developer tools
NEW_URL = "https://mvic.sos.state.mi.us/Voter/SearchByCounty"

r = requests.get(BASE_URL, verify=False)
soup = bs(r.content, 'html.parser')

countyData = []

def getCountyNames():
    options = soup.find_all('option')
    for option in options:
        if 'County' in option.text or 'COUNTY' in option.text:
            thisCountyName = option.text.replace(" ", "+")
            if 'IRON' in option.text:
                thisCountyName = "Iron"
            thisCountyId = option['value']
            countyData.append({'CountyName': thisCountyName, 'CountyID': thisCountyId})

getCountyNames()

def requestDataForOneCounty(countyData):
    req = requests.post(NEW_URL, countyData, verify=False)
    _soup = bs(req.content, 'html.parser')

    data = _soup.find(id='pnlClerk').find(class_ = 'card-body').text
    example = {"\t": None, "\n": " ", "\r":None}
    table = data.maketrans(example)
    cleaned = data.translate(table)

    res = formatDataIntoSchema(countyData['CountyName'], cleaned)
    return res

# postResponseData is a string that that lists county clerk name, address, phone, fax, email, and business hours in that order
def formatDataIntoSchema(countyName, postResponseData):
    cleanedData = re.sub("[^{}]+".format(printable), "", postResponseData)
    cleanedCountyName = countyName.replace("+", " ").replace(" County", "")

    #print(cleanedData)

    phoneRegex = re.search('Phone:(.*)  Fax:', cleanedData)
    phone = 'None' if phoneRegex is None else phoneRegex[1]

    emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleanedData)
    email = 'None' if emailRegex is None else emailRegex[0]

    # janky as fuck, but search stops after first match
    # and our code cleaned it up in such a way that address is always 
    # 3 spaces after the end of the clerk name
    clerkRegex = re.search('.+?(?=   )', cleanedData)
    clerkData = 'None' if clerkRegex is None else clerkRegex[0]

    tmpcd = clerkData.split(",")
    firstLast = tmpcd[0].strip()
    clerkTitle = 'N/A' if len(tmpcd) == 1 else tmpcd[1].strip()

    addressData = cleanedData.replace(clerkData, '').split("Phone:")[0]

    # dealing with stupid edge cases
    if cleanedCountyName == "Keweenaw":
        addressData = addressData.replace('5095 4th', '5095 4th St')
    
    if cleanedCountyName == "Oakland":
        addressData = addressData.replace('Building 12 East', 'Building 12')

    if cleanedCountyName == "Wayne":
        addressData = addressData.replace('Bldg', 'Building')

    if cleanedCountyName == "Kent":
        addressData = addressData.replace('T Grand', 'Grand')

    if cleanedCountyName == "Missaukee":
        addressData = addressData.replace('111 S Canal St', '')

    splitAddresses = addressData.split("Mailing address:")

    physicalAddress = formatAddressData(splitAddresses[0], cleanedCountyName)
    
    schema = {
        "countyName": cleanedCountyName,
        "physicalAddress": physicalAddress,
        "phone": phone,
        "email": email,
        "officeSupervisor": firstLast,
        "supervisorTitle": clerkTitle,
    }

    if len(splitAddresses) > 1: # there is a mailing address as well
        mailing = splitAddresses[1]

        #another edge case
        if cleanedCountyName == "Iosco":
            mailing = mailing.replace('422 W. Lake Street, County Building', 'County Building 422 W. Lake Street')
        
        mailingAddress = formatAddressData(mailing, cleanedCountyName)
        schema["mailingAddress"] = mailingAddress

    #print(schema)
    return schema

def formatAddressData(addressData, countyName):
    addressSchemaMapping = {
        'BuildingName': 'locationName',
        'CornerOf': 'locationName',
        'IntersectionSeparator':'locationName',
        'LandmarkName': 'locationName',
        'NotAddress': 'locationName',
        'SubaddressType': 'aptNumber',
        'SubaddressIdentifier': 'aptNumber',
        'AddressNumber': 'streetNumberName',
        'StreetName': 'streetNumberName',
        'StreetNamePreDirectional': 'streetNumberName',
        'StreetNamePreModifier': 'streetNumberName',
        'StreetNamePreType': 'streetNumberName',
        'StreetNamePostDirectional': 'streetNumberName',
        'StreetNamePostModifier': 'streetNumberName',
        'StreetNamePostType': 'streetNumberName',
        'OccupancyType': 'aptNumber',
        'OccupancyIdentifier': 'aptNumber',
        'Recipient': 'locationName',
        'PlaceName': 'city',
        'USPSBoxGroupID': 'poBox',
        'USPSBoxGroupType': 'poBox',
        'USPSBoxID': 'poBox',
        'USPSBoxType': 'poBox',
        'StateName': 'state',
        'ZipCode': 'zipCode'
    }
    parsedDataDict = usaddress.tag(addressData, tag_mapping=addressSchemaMapping)[0]
    
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
        if countyName == "Montmorency":
            finalAddress['streetNumberName'] = finalAddress['streetNumberName'] + " M-32"
    if 'locationName' in parsedDataDict:
        finalAddress['locationName'] = parsedDataDict['locationName']
    if 'aptNumber' in parsedDataDict:
        finalAddress['aptNumber'] = parsedDataDict['aptNumber']
        if countyName == "Oakland":
            finalAddress['aptNumber'] = finalAddress['aptNumber'] + " East"
    if 'poBox' in parsedDataDict:
        finalAddress['poBox'] = parsedDataDict['poBox']
    return finalAddress



masterList = []
# do stuff to all counties
numScraped = 0
for county in countyData:
    data = requestDataForOneCounty(county)
    masterList.append(data)
    numScraped += 1
    print(f'[Michigan] Scraped {data["countyName"]} county: #{numScraped} of {len(countyData)} .... [{round((numScraped/len(countyData)) * 100, 2)}%]')

# output to JSON
with open('michigan.json', 'w') as f:
    json.dump(masterList, f)
