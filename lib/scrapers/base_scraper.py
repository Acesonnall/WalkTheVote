"""Generic scraper

The scraper class with all other scrapers will inherit from.
"""
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self):
        """ TODO: Write documentation once purpose of method is further defined
        """
        pass
