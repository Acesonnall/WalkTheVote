"""Scraper handler

Interface for dynamically preloading a database with zip to county mappings as well as
dynamically loading election office information from the scrapers
"""
import asyncio
import json
import os
import re
import time
import types
from asyncio import Task
from dataclasses import dataclass, field
from typing import Iterable, Callable, Dict, List

import pandas as pd
from pymodm import connect
from tqdm import tqdm

from definitions import ROOT_DIR, LOCAL_DB_URI, LOCAL_DB_ALIAS, LOCAL_DB_NAME, bcolors
from errors.wtv_errors import WalkTheVoteError
from handler.wtv_db_schema import State, County, City, ZipCode, ElectionOffice, Address
from handler.zip_county_mapping.zip_to_county import create_mapping

# Using the same naming scheme, import more scrapers here as they are ready and
# formatted
from scrapers.michigan import michigan_scraper
from scrapers.florida import florida_scraper


@dataclass
class Scraper:
    """ Scraper data unit

    @param state_name name of state being scraped
    @param get_election_office Callable function to run scraper
    @param data = result of scraper run (loaded from file or from scraper function)
    """

    state_name: str
    get_election_office: Callable
    data: Dict = field(default_factory=dict)


class WtvDbHandler:
    """Walk The Vote database handler.
    
    @param self.mapping_df table of zip code, state, county, and city mappings
    @param self.scrapper_funcs [state_name] -> scraper_function dictionary mapping
    """

    def __init__(self, db_uri, db_alias):
        self.preloaded = self._is_db_preloaded()
        self.scrapers = []

        try:
            connect(db_uri, alias=db_alias)
        except Exception as e:
            raise WalkTheVoteError(f"Problem connecting to database: {db_alias}") from e

        # Map get_election_office() function of scrapers to corresponding state name
        for imported_scraper_module in self._get_imported_scrapers():
            state_name = re.search(
                r"(?<=\.)([a-z]+_*)+(?=\.)", imported_scraper_module.__name__
            ).group()
            module = getattr(imported_scraper_module, "get_election_offices")
            self.scrapers.append(Scraper(state_name, module))

    @staticmethod
    def _get_imported_scrapers() -> Iterable:
        """ Yields list of imported scraper modules
        """

        # Iterate through imported modules and yield only scraper modules. Dependent on
        # path naming scheme being named
        # "scrapers.[LOWER_CASE_STATE_NAME].[LOWER_CASE_STATE_NAME]_scraper"
        for name, val in globals().items():
            if isinstance(val, types.ModuleType) and (
                re.match("scraper.*", val.__name__)
            ):
                yield val

    def _get_mapping(self):
        """ Loads zip, state, county, city mapping from file or directly from funcition

        @return: DataFrame loaded with the mapping information
        """
        tries = 1
        wait_seconds = 2
        mapping_df = None
        while mapping_df is None:
            try:
                print(
                    f"{bcolors.OKBLUE}Attempt {tries}: Loading mapping data.{bcolors.ENDC}"
                )
                mapping_df = pd.read_csv(os.path.join(ROOT_DIR, r"handler\mapping.csv"))
                print(f"{bcolors.OKBLUE}Mapping data loaded.{bcolors.ENDC}")
            except FileNotFoundError as e:
                if tries <= 3:
                    print(
                        f"{bcolors.OKBLUE}Attempt {tries}: Mapping data file not "
                        f"found. Creaing mapping.{bcolors.ENDC} "
                    )
                    create_mapping()
                    tries += 1
                    print(
                        f"{bcolors.OKBLUE}Retrying in {wait_seconds} seconds.{bcolors.ENDC}"
                    )
                    time.sleep(wait_seconds)
                else:
                    raise WalkTheVoteError(
                        f"File not found after {tries} attempts"
                    ) from e
            except Exception as e:
                raise WalkTheVoteError("Unknown error loading mapping file") from e
        return mapping_df

    @staticmethod
    def _is_db_preloaded():
        """ Weak checking to see if database is already preloaded with data
        @rtype: bool
        """
        from pymongo import MongoClient

        client = MongoClient(LOCAL_DB_URI)
        db = client[LOCAL_DB_NAME]
        return not len(db.list_collection_names()) < 4

    async def preload_db(self):
        """ Preload the database with the zip, city, county, state mapping
        """
        if not self.preloaded:
            print(
                f"{bcolors.OKBLUE}Database is not yet preloaded. Creating zip code to "
                f"county mappings.{bcolors.ENDC} "
            )
            mapping_df = self._get_mapping()
            total_rows = len(mapping_df.index)
            # TODO: Only way to speed this up is with an async MongoDB driver
            for row in tqdm(
                mapping_df.itertuples(), desc="preloading db", total=total_rows
            ):
                State(state_name=row.State).save()
                county_id = f"{row.State}.{row.County}"

                County.objects.raw({"_id": county_id}).update(
                    {"$setOnInsert": {"_id": county_id, "parent_state": row.State}},
                    upsert=True,
                )
                city_id = f"{row.State}.{row.County}.{row.Cities}"
                City.objects.raw({"_id": city_id}).update(
                    {"$setOnInsert": {"_id": city_id, "parent_county": county_id}},
                    upsert=True,
                )
                padded_zip = f"{row.Zip:05}"
                ZipCode.objects.raw({"_id": padded_zip}).update(
                    {"$setOnInsert": {"_id": padded_zip, "parent_city": city_id}},
                    upsert=True,
                )

        self.preloaded = True

    @staticmethod
    async def _get_scraper_data(scraper):
        """ Run scraper function and assign results to data variable of scraper
        object
        """
        scraper.data = await scraper.get_election_office()

    # TODO: Implement code to handle loading of select states rather than ALL (useful
    #  for if we need to issue updates without reloading the entire db)
    async def get_election_office_info(self, states=None):
        """ Dynamically acquire data from scrapers in a non-IO blocking fashion
        """
        if not self.preloaded:
            await self.preload_db()
        else:
            tasks: List[Task] = []
            print(
                f"{bcolors.OKBLUE}Loading scraper data for "
                f'{"all" if not states else len(states)} states...{bcolors.ENDC}'
            )
            for scraper in self.scrapers:
                try:
                    with open(
                        os.path.join(
                            ROOT_DIR,
                            rf"scrapers\{scraper.state_name}\{scraper.state_name}.json",
                        )
                    ) as scraper_results_file:
                        print(
                            f"{bcolors.OKBLUE}Pre-existing data file found for "
                            f"{scraper.state_name.capitalize()}{bcolors.ENDC}."
                        )
                        scraper.data = json.load(scraper_results_file)
                except FileNotFoundError as e:
                    print(
                        f"{bcolors.OKBLUE}Pre-existing data file not found for "
                        f"{scraper.state_name.capitalize()}. Loading from scraper."
                        f"{bcolors.ENDC}\n"
                    )
                    tasks.append(asyncio.create_task(self._get_scraper_data(scraper)))
            if tasks:
                await asyncio.gather(*tasks)
            print(f"{bcolors.OKBLUE}Scraper data loaded into memory{bcolors.ENDC}")

    def load_election_office_info(self):
        """ Insert election office information gathered from scrapers into the database
        """
        for scraper in tqdm(self.scrapers, desc="loading office info"):
            s_data: Dict
            for s_data in scraper.data:
                address = s_data.get("physicalAddress")
                is_mailing = False
                if not address:
                    address = s_data.get("mailingAddress")
                    is_mailing = True

                # TODO: Add support for county names (dependent on eventual schema)
                if "countyName" in s_data:
                    election_office = ElectionOffice(
                        county_name=f'{s_data.get("countyName")} County',
                        address=Address(
                            location_name=address.get("locationName"),
                            street=address.get("streetNumberName"),
                            apt_unit=address.get("aptNumber"),
                            po_box=address.get("poBox"),
                            state=address.get("state"),
                            zip_code=address.get("zipCode")[:5],
                            is_mailing=is_mailing,
                        ),
                        phone_number=s_data.get("phone"),
                        email_address=s_data.get("email"),
                        office_supervisor=s_data.get("officeSupervisor"),
                        supervisor_title=s_data.get("supervisorTitle"),
                        website=s_data.get("website"),
                    )
                    zip_code_doc = ZipCode.objects.raw(
                        {"_id": election_office.address.zip_code}
                    )[0]
                    county_id = zip_code_doc.parent_city.parent_county.county_name
                    County.objects.raw({"_id": county_id}).update(
                        {"$set": {"election_office": election_office.to_son()}},
                        upsert=True,
                    )


async def main():
    wtv_db = WtvDbHandler(LOCAL_DB_URI, LOCAL_DB_ALIAS)
    await wtv_db.preload_db()
    await wtv_db.get_election_office_info()
    wtv_db.load_election_office_info()


if __name__ == "__main__":
    # asyncio.run(main()) causes error when program completes
    # https://github.com/aio-libs/aiohttp/issues/4324
    start = time.time()
    asyncio.get_event_loop().run_until_complete(main())
    end = time.time()
    print(f"{bcolors.OKBLUE}Completed in {end - start} seconds.{bcolors.ENDC}")
