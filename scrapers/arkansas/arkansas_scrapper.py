import re
from pprint import pprint
from typing import List

import requests
from pdfreader import SimplePDFViewer, PDFDocument

# Get the PDF
r = requests.get("https://www.sos.arkansas.gov/uploads/elections/ARCountyClerks.pdf")

# Pass byte stream to PDFDocument parser (used for iterating through pages)
doc = PDFDocument(r.content)
# Pass byte stream to PDF viewer (used for reading strings on pages)
viewer = SimplePDFViewer(r.content)

# prep variable that stores final results
info = []


def fix_line(line: str) -> str:
    """
    Helper method to apply fix to lines and splice the fix in
    @param line: line to be fixed and spliced in
    @return: fixed line
    """
    line = line + page_strings[idx + 1]
    page_strings[idx: idx + 2] = [line]
    return line


def anomaly_check(line: str, check_type: str = "DEFAULT") -> str:
    """
    Check for edge cases not originally caught when pre-processing the document page.

    Known anomalies: Sometimes attributes that should be together are unexpected
    spread out over an extra list index. This messes up the flow of the code. These
    issues uniquely are only one word long. Since they shouldn't be I just look for
    values that are one word long, look one more index ahead and merge those index
    values. Other anomaly is similar to the last, but it's different in detection. I
    detect that anomaly by making sure an address is complete with a zip code.
    @param line: line to be checked
    @param check_type: type of check (default or zip code check)
    @return: Corrected line
    """
    # check for address anomaly
    if check_type == "ZIP":
        if not re.search(r"[0-9]{5}", line):
            line = fix_line(line)
    # otherwise check for the usual anomaly
    else:
        if line and " " not in line:
            line = fix_line(line)
    return line


for i, page in enumerate(doc.pages(), 1):
    # navigate to page
    viewer.navigate(i)
    # render the page
    viewer.render()

    # collapse that ass
    page_strings: List[str] = viewer.canvas.strings.copy()

    # variable used to define the ranges of strings to be merged together
    from_to = 0

    # for each index and page string of the malformed pdf page strings, create tuple
    # that defines the range of indices with strings to be joined together. '" "'
    # designates a new line.
    merge_ranges = [
        (from_to, from_to := idx)  # (start, end); start become end as end gets updated
        for idx, page_str in enumerate(page_strings)
        if page_str == " "
    ]

    # repair the page strings in reverse
    for start, end in merge_ranges[::-1]:
        # merging values within a range
        repaired_line = "".join(page_strings[start:end])
        if repaired_line == " ":
            # delete for the sake of uniformity
            del page_strings[start:end]
        else:
            # slice in repaired string in place of range of malformed strings
            page_strings[start:end] = [repaired_line]

    # remove unnecessary empty index
    page_strings.pop()

    # prep helper vars
    county_name, county_addr, phone = ("", "", "")

    # read strings on page and parser out the county, address, and phone numbers.
    # Each county clerk office's contact info is uniform so we can use a modulus
    # operator too look up exact info.
    for idx, page_line in enumerate(page_strings):
        # check for fucked up shit that slipped through the cracks
        page_line = anomaly_check(page_line.strip())

        # Get county name
        if idx % 7 == 0:
            county_name = page_line.strip()
        # Get first part of address
        elif idx % 7 == 2:
            county_addr = page_line.strip()
        # Get remainder of address
        elif idx % 7 == 3:
            # check for zip code anomaly
            page_line = anomaly_check(page_line.strip(), "ZIP")
            county_addr += f" {page_line.strip()}"
        # Get phone number
        elif idx % 7 == 4:
            m = re.search(r"\d{10}", page_line)
            if m:
                phone = m.group(0)
            else:
                raise Exception("Phone number not found. Fatal.")

            info.append(
                {"county_name": county_name, "county_addr": county_addr, "phone": phone}
            )
        continue

pprint(info)
