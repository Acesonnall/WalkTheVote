import os

import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup

from lib.definitions import ROOT_DIR


def get_state_zip_info(scraper, url, name):
    r = scraper.get(url)
    state_soup = BeautifulSoup(r.content, "html5lib")

    zips_html = state_soup.findAll("div", class_="col-xs-12 prefix-col1")[1:]
    cities_html = state_soup.findAll("div", class_="col-xs-12 prefix-col3")[1:]
    counties_html = state_soup.findAll("div", class_="col-xs-12 prefix-col4")[1:]

    zips = [zipcode.text.strip() for zipcode in zips_html]
    cities = [city.text.strip() for city in cities_html]
    counties = [county.text.strip() for county in counties_html]

    info_df = pd.DataFrame(
        {"Zip": zips, "State": name, "Cities": cities, "County": counties},
        columns=["Zip", "State", "Cities", "County"],
    )
    return info_df


def create_mapping():
    c_scraper = cloudscraper.create_scraper()
    html_obj = c_scraper.get(
        "https://www.unitedstateszipcodes.org/printable-zip-code-maps/"
    )
    soup = BeautifulSoup(html_obj.content, "html5lib")

    state_hrefs = soup.findAll("ul", class_="list-unstyled state-links")[1].findAll(
        "a", href=True
    )
    state_abbrs = [state["href"] for state in state_hrefs]
    state_names = [state.text.strip() for state in state_hrefs]

    base_url = "https://www.unitedstateszipcodes.org"
    state_urls = [base_url + abbr for abbr in state_abbrs]

    zip_info_df = pd.DataFrame(columns=["Zip", "State", "Cities", "County"])

    for i in range(len(state_names)):
        state_name = state_names[i]
        state_url = state_urls[i]
        state_info_df = get_state_zip_info(c_scraper, state_url, state_name)

        zip_info_df = zip_info_df.append(state_info_df, ignore_index=True)

    zip_info_df.to_csv(
        path_or_buf=os.path.join(ROOT_DIR, r"handler\zip_county_mapping\mapping.csv"),
        encoding="utf-8", index=False)
    return zip_info_df


if __name__ == "__main__":
    create_mapping()
