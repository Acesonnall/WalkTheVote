import re
from pprint import pprint
from typing import List, Tuple

import requests
from pdfreader import SimplePDFViewer, PDFDocument

# prep variable that stores final results
ELECTION_OFFICE_INFO = []


def fix_line(line: str, string_list: List[str], index: int) -> str:
    """
    Helper method to apply fix to lines and splice the fix in
    @param index: position to start amending from
    @param string_list: master list of strings to be amended
    @param line: line to be fixed and spliced in
    @return: fixed line
    """
    line = line + string_list[index + 1]
    string_list[index : index + 2] = [line]
    return line


def anomaly_check(
    line: str, strings_list: List[str], index: int, check_type: str = "DEFAULT"
) -> str:
    """
    Check for edge cases not originally caught when pre-processing the document page.

    Known anomalies: Sometimes attributes that should be together are unexpected
    spread out over an extra list index. This messes up the flow of the code. These
    issues uniquely are only one word long. Since they shouldn't be I just look for
    values that are one word long, look one more index ahead and merge those index
    values. Other anomaly is similar to the last, but it's different in detection. I
    detect that anomaly by making sure an address is complete with a zip code.
    @param index: position to amend from if necessary
    @param strings_list: master list of stings to be amended if anomaly detected
    @param line: line to be checked
    @param check_type: type of check (default or zip code check)
    @return: Corrected line
    """
    # check for address anomaly
    if check_type == "ZIP":
        if not re.search(r"[0-9]{5}", line):
            line = fix_line(line=line, string_list=strings_list, index=index)
    # otherwise check for the usual anomaly
    else:
        if line and " " not in line:
            line = fix_line(line=line, string_list=strings_list, index=index)
    return line


def get_line_ranges(strings_list: List[str]) -> List[Tuple[int, int]]:
    # variable used to define the ranges of strings to be merged together
    from_to = 0

    # for each index and page string of the malformed pdf page strings, create tuple
    # that defines the range of indices with strings to be joined together. '" "'
    # designates a new line.
    return [
        (from_to, from_to := idx)
        # (start, end); start become end as end gets updated
        for idx, page_str in enumerate(strings_list)
        if page_str == " "
    ]


def establish_uniformity(
    strings_list: List[str], line_range_list: List[Tuple[int, int]]
):
    # repair the page strings in reverse
    for start, end in line_range_list[::-1]:
        # merging values within a range
        repaired_line = "".join(strings_list[start:end])
        if repaired_line == " ":
            # delete for the sake of uniformity
            del strings_list[start:end]
        else:
            # slice in repaired string in place of range of malformed strings
            strings_list[start:end] = [repaired_line]
    # remove unnecessary empty index
    strings_list.pop()
    return strings_list


def get_county_election_office_info(strings_list: List[str]):
    """
    Read strings on page and parser out the county, address, and phone numbers. Each
    county clerk office's contact info is uniform so we can use a modulus operator
    too look up exact info.
    @param strings_list: List of strings to be parsed
    """
    # prep helper vars
    county_name, county_addr, phone = ("", "", "")

    for idx, page_line in enumerate(strings_list):
        # check for fucked up shit that slipped through the cracks
        page_line = anomaly_check(
            line=page_line.strip(), strings_list=strings_list, index=idx
        )

        # Get county name
        if idx % 7 == 0:
            county_name = page_line.strip()
        # Get first part of address
        elif idx % 7 == 2:
            county_addr = page_line.strip()
        # Get remainder of address
        elif idx % 7 == 3:
            # check for zip code anomaly
            page_line = anomaly_check(
                line=page_line.strip(),
                strings_list=strings_list,
                check_type="ZIP",
                index=idx,
            )
            county_addr += f" {page_line.strip()}"
        # Get phone number
        elif idx % 7 == 4:
            m = re.search(r"\d{10}", page_line)
            if m:
                phone = m.group(0)
            else:
                raise Exception("Phone number not found. Fatal.")

            ELECTION_OFFICE_INFO.append(
                {"county_name": county_name, "county_addr": county_addr, "phone": phone}
            )
        continue


def navigate_pages(doc: PDFDocument, viewer: SimplePDFViewer):
    for i, page in enumerate(doc.pages(), 1):
        # navigate to page
        viewer.navigate(i)
        # render the page
        viewer.render()

        # collapse that ass
        page_strings: List[str] = viewer.canvas.strings.copy()

        merge_ranges = get_line_ranges(strings_list=page_strings)

        page_strings = establish_uniformity(
            strings_list=page_strings, line_range_list=merge_ranges
        )

        get_county_election_office_info(strings_list=page_strings)


def main():
    # Get the PDF
    r = requests.get(
        "https://www.sos.arkansas.gov/uploads/elections/ARCountyClerks.pdf"
    )

    # Pass byte stream to PDFDocument parser (used for iterating through pages)
    doc = PDFDocument(r.content)
    # Pass byte stream to PDF viewer (used for reading strings on pages)
    viewer = SimplePDFViewer(r.content)
    navigate_pages(doc, viewer)
    pprint(ELECTION_OFFICE_INFO)


if __name__ == "__main__":
    main()
