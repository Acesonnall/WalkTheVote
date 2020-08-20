"""Iowa scraper
"""
import logging

from bs4 import BeautifulSoup
from selenium import webdriver

from scrapers.base_scraper import BaseScraper

# create logger
LOG = logging.getLogger("iowa_scraper")
LOG.setLevel(logging.DEBUG)

# create console handler and set level to debug.
# logging.StreamHandler(sys.stdout) to print to stdout instead of the default stderr
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
LOG.addHandler(ch)


class IowaScraper(BaseScraper):
    def __init__(self):
        """Instantiates top-level url to begin scraping from
        """
        self.root_url = (
            "https://sos.iowa.gov/elections/auditors/auditor.asp?CountyID=00"
        )

    def scrape(self) -> int:
        """ TODO: Write documentation once purpose of method is further defined.

        This code will only work on Windows as it stands now.
        """
        exit_code = 0
        webdriver_path = r"C:\Users\omarc\Downloads\edgedriver_win64\msedgedriver.exe"

        # Using selenium webdriver over requests due to needing a more sophisticated
        # way to bypass captcha for gov websites that use it. Only works on Windows
        # for now and there are some simple pre-reqs needed before it can work.
        # More info: https://selenium-python.readthedocs.io/index.html
        try:
            LOG.info("Starting webdriver...")
            driver = webdriver.Edge(webdriver_path)

            # Execute GET request
            LOG.info(f"Fetching {self.root_url}...")
            driver.get(self.root_url)

            # Convert the response into an easily parsable object
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Print out results for testing
            LOG.info(f"Test parse:\n{soup.article.table}")

            # Close browser driver
            driver.close()
        except Exception as e:
            LOG.error(f"Exception: {e}")

        return exit_code


def main() -> int:
    iowa_scraper = IowaScraper()
    exit_code = iowa_scraper.scrape()

    return exit_code


if __name__ == "__main__":
    exit(main())
