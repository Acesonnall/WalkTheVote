import re
from pprint import pprint

import requests
from pdfreader import SimplePDFViewer, PDFDocument

r = requests.get(
    "https://elections.wi.gov/sites/elections.wi.gov/files/2020-08/WI%20County"
    "%20Clerks%20Updated%208-7-20.pdf "
)

doc = PDFDocument(r.content)
viewer = SimplePDFViewer(r.content)
county_name, county_addr = ("", "")
info = []
for i, page in enumerate(doc.pages(), 1):
    viewer.navigate(i)
    viewer.render()
    for j, s in enumerate(viewer.canvas.strings):
        if not county_name:
            m = re.search(r"\D+(?=\s-)", s)
            if m:
                county_name = f"{m.group(0)} Election Office"
        if not county_addr:
            m = re.search(r"(?<=MUNICIPAL ADDRESS :).*", s)
            if m:
                county_addr = f"{m.group(0)} {viewer.canvas.strings[j + 1]}"
                info.append({"county_name": county_name, "county_addr": county_addr})
                county_name, county_addr = ("", "")

pprint(info)
