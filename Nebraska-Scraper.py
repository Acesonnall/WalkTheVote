import requests
from bs4 import BeautifulSoup as bs
import re
import re
from string import printable

# emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleanedData)

BASE_URL = "https://sos.nebraska.gov/elections/election-officials-contact-information"

r = requests.get(BASE_URL)
soup = bs(r.content, 'html.parser')

elems = soup.find_all(class_='col-sm-6')

for e in elems:
    cleanedData = re.sub("[^{}]+".format(printable), "", e.text)

    # (.*) matches EVERYTIHNG between "Name: " and "Party"
    # the space is important
    nameRegex = re.search('Name:(.*)Party Affiliation:', cleanedData)
    name = 'None' if nameRegex is None else nameRegex[1]
    Names: str = name.strip()

    addyRegex = re.search('Address:(.*)City', cleanedData)
    Addy = 'None' if addyRegex is None else addyRegex[1]
    streetNumberName: str = Addy.strip()

    cityRegex = re.search('City:(.*)Zip', cleanedData)
    cities = 'None' if cityRegex is None else cityRegex[1]
    City: str = cities.strip()

    countyRegex = re.search('County:(.*)Name:', cleanedData)
    count = 'None' if countyRegex is None else countyRegex[1]
    noParens = count.split("(")[0]
    County: str = noParens.strip()

    zipRegex = re.search('Code:(.*)Phone', cleanedData)
    z = 'None' if zipRegex is None else zipRegex[1]
    zipCode: str = z.strip()

    phoRegex = re.search('Number:(.*)Fax', cleanedData)
    ph = 'None' if phoRegex is None else phoRegex[1]
    Phone: str = ph.strip()

    emRegex = re.search('Email Address:(.*)County', cleanedData)
    e = 'None' if emRegex is None else emRegex[1]
    Email: str = e.strip()

    schema = {
        "countyName": County,
        "physicalAddress": {
            "streetNumberName": streetNumberName,
            "city": City,
            "state": 'Nebraska',
            "county": County,
            "zipCode": zipCode,
        },
        "phone": Phone,
        "officeSupervisor": Names,
        "Link": "https://sos.nebraska.gov/elections/election-officials-contact-information"
    }
    print(schema)
