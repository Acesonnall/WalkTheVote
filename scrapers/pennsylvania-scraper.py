import requests
from bs4 import BeautifulSoup as bs
import json
import re
import re
from string import printable

# emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleanedData)
from typing import List

BASE_URL = "https://www.votespa.com/Resources/Pages/Contact-Your-Election-Officials.aspx"

r = requests.get(BASE_URL)
soup = bs(r.content, 'html.parser')

elems = soup.findAll('script', type='text/javascript')
inform = elems[34]

county = []

tmp1 = inform.string.split('MapPopup.init(')[1]
tmp2 = tmp1.split(');var')[0]
data = json.loads(tmp2)
subdata = data['data']
items = subdata['Items']
for i in items:
    tag = items[i][3]['FieldContent']
    subsoup = bs(tag)
    print(subsoup)


# for e in in
#     cleanedData = re.sub("[^{}]+".format(printable), "", e.text)
#     County_name = re.search('Field Content: (.*) county', e)
#     if County_name is None:
#         county.append('None')
#     else:
#         county.append(County_name.group(1))
#     county = County_name.strip()


