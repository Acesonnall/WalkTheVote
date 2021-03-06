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
from asyncio import Task, Future
from dataclasses import dataclass, field
from typing import Iterable, Callable, Dict, List

from pymodm import connect
from pymodm.errors import ValidationError
from pymongo import MongoClient
from pymongo.errors import WriteError
from tqdm import tqdm

from lib.definitions import (
    ROOT_DIR,
    Bcolors,
    TEST_DB_URI,
    TEST_DB_ALIAS,
    TEST_DB_NAME,
    LOCAL_DB_URI,
    LOCAL_DB_NAME,
    LOCAL_DB_ALIAS,
)
from lib.errors.wtv_errors import WalkTheVoteError
from lib.handler.wtv_db_schema import (
    State,
    County,
    City,
    ZipCode,
    ElectionOffice,
    MailingAddress,
    PhysicalAddress,
    VALIDATION_RULES,
)
from lib.handler.zip_mapping.zip_mapping_v2 import create_mapping

# Using the same naming scheme, import more scrapers here as they are ready and
# formatted
from lib.scrapers.michigan import michigan_scraper
from lib.scrapers.florida import florida_scraper
from lib.scrapers.north_carolina import north_carolina_scraper
from lib.scrapers.texas import texas_scraper
from lib.scrapers.minnesota import minnesota_scraper
from lib.scrapers.arizona import arizona_scraper
from lib.scrapers.nebraska import nebraska_scraper
from lib.scrapers.georgia import georgia_scraper
from lib.scrapers.california import california_scraper
from lib.scrapers.ohio import ohio_scraper
from lib.scrapers.iowa import iowa_scraper

# from lib.scrapers.pennsylvania import pennsylvania_scraper
from lib.scrapers.illinois import illinois_scraper
from lib.scrapers.wyoming import wyoming_scraper

# from lib.scrapers.maine import maine_scraper
from lib.scrapers.new_hampshire import new_hampshire_scraper

# from lib.scrapers.wisconsin import wisconsin_scraper
from lib.scrapers.missouri import missouri_scraper
from lib.scrapers.massachusetts import massachusetts_scraper
from lib.scrapers.washington import washington_scraper
from lib.scrapers.new_york import new_york_scraper
from lib.scrapers.south_carolina import south_carolina_scraper
from lib.scrapers.utah import utah_scraper
from lib.scrapers.west_virginia import west_virginia_scraper


@dataclass
class Scraper:
    """Scraper data unit

    @param state_name name of state being scraped
    @param get_election_office Callable function to run scraper
    @param data = result of scraper run (loaded from file or from scraper function)
    """

    state_name: str
    get_election_office: Callable
    election_offices: Dict = field(default_factory=dict)


class WtvDbHandler:
    """Walk The Vote database handler.

    @param self.preloaded boolean variable to help determine whether database was
    already with loaded with zip -> city -> county -> state mapping. Helps improve
    run time.
    @param self.scrapers list of state scraper objects each containing their own
    information needed to load database with election office information
    """

    def __init__(self, db_uri, db_alias):
        self.preloaded = self._is_db_preloaded()
        self.scrapers = []
        self.failed_scraper_data_retrieval_msgs = []

        try:
            connect(db_uri, alias=db_alias)
        except Exception as e:
            raise WalkTheVoteError(
                f"{Bcolors.FAIL}Problem connecting to database: {db_alias}{Bcolors.ENDC}"
            ) from e

        # Map get_election_office() function of scrapers to corresponding state name
        for imported_scraper_module in self._get_imported_scrapers():
            state_name = re.search(
                r"[a-z_]+(?=\.[a-z_]+scraper)", imported_scraper_module.__name__
            ).group()
            module = getattr(imported_scraper_module, "get_election_offices")
            self.scrapers.append(Scraper(state_name, module))

    @staticmethod
    def _get_imported_scrapers() -> Iterable:
        """Yields list of imported scraper modules"""

        # Iterate through imported modules and yield only scraper modules. Dependent on
        # path naming scheme being named
        # "lib.scrapers.[LOWER_CASE_STATE_NAME].[LOWER_CASE_STATE_NAME]_scraper"
        for name, val in globals().items():
            if isinstance(val, types.ModuleType) and (
                re.match("lib.scraper.*", val.__name__)
            ):
                yield val

    @staticmethod
    def _get_mapping():
        """Loads zip, state, county, city mapping from file or directly from funcition

        @return: DataFrame loaded with the mapping information
        """
        mapping_dict = None
        while mapping_dict is None:
            try:
                with open(
                    os.path.join(ROOT_DIR, "handler", "zip_mapping", "mapping.json"),
                    "r",
                ) as f:
                    mapping_dict = json.load(f)
                print(f"{Bcolors.OKBLUE}Mapping data loaded.{Bcolors.ENDC}\n")
            except FileNotFoundError as e:
                print(
                    f"{Bcolors.OKBLUE}Mapping data file not yet existent in directory. "
                    f"Attempting to loading mapping from script instead. This could "
                    f"""take a while so go grab some coffee.
 ( 
  )
c[]{Bcolors.ENDC}"""
                )
                try:
                    mapping_dict = create_mapping()
                except WalkTheVoteError as e:
                    raise WalkTheVoteError(f"{Bcolors.FAIL}{e}{Bcolors.ENDC}")
                print(f"{Bcolors.OKBLUE}Load successful.{Bcolors.ENDC}")
            except Exception as e:
                raise WalkTheVoteError(
                    f"{Bcolors.FAIL}Unknown error loading mapping file{Bcolors.ENDC}"
                ) from e
        return mapping_dict

    @staticmethod
    def _is_db_preloaded():
        """Weak checking to see if database is already preloaded with data
        @rtype: bool
        """

        client = MongoClient(LOCAL_DB_URI)
        db = client[LOCAL_DB_NAME]
        return not len(db.list_collection_names()) < 4

    async def _preload_db(self):
        """Preload the database with the zip, city, county, state mapping"""
        if not self.preloaded:
            print(
                f"{Bcolors.OKBLUE}Database is not yet preloaded. Creating zip code "
                f"mappings.{Bcolors.ENDC} "
            )
            mapping_dict = self._get_mapping()
            self.set_validation_rules()
            # TODO: Only way to speed this up is with an async MongoDB driver
            for zip_code, parent_city in tqdm(
                mapping_dict.items(), desc="preloading db", total=len(mapping_dict)
            ):
                parent_city, parent_county = list(parent_city.items())[0]
                parent_county, parent_state = list(parent_county.items())[0]
                State(state_name=parent_state).save()
                county_id = f"{parent_state}.{parent_county}"

                County.objects.raw({"_id": county_id}).update(
                    {"$setOnInsert": {"_id": county_id, "parent_state": parent_state}},
                    upsert=True,
                )
                city_id = f"{parent_state}.{parent_county}.{parent_city}"
                City.objects.raw({"_id": city_id}).update(
                    {"$setOnInsert": {"_id": city_id, "parent_county": county_id}},
                    upsert=True,
                )
                padded_zip = zip_code
                ZipCode.objects.raw({"_id": padded_zip}).update(
                    {"$setOnInsert": {"_id": padded_zip, "parent_city": city_id}},
                    upsert=True,
                )

        self.preloaded = True

    @staticmethod
    async def _get_scraper_data(scraper) -> str:
        """Run scraper function and assign results to data variable of scraper
        object
        """
        try:
            scraper.election_offices = await scraper.get_election_office()
        except Exception as e:
            raise WalkTheVoteError(
                f"{Bcolors.WARNING}Problem getting election office data from "
                f"{scraper.state_name}_scraper.py: {e}{Bcolors.ENDC}"
            )
        else:
            return scraper.state_name

    # TODO: Implement code to handle loading of select states rather than all of them
    #  (useful for if we need to issue targeted updates)
    async def _get_election_office_info(self, states=None):
        """Dynamically acquire data from scrapers in a non-IO blocking fashion"""
        if not self.preloaded:
            await self._preload_db()

        tasks: List[Task] = []
        print(
            f"{Bcolors.OKBLUE}Loading scraper data for "
            f'{"all" if not states else len(states)} states...{Bcolors.ENDC}'
        )
        for scraper in self.scrapers:
            state_name = " ".join(
                s.capitalize() for s in scraper.state_name.split(sep="_")
            )
            try:
                with open(
                    os.path.join(
                        ROOT_DIR,
                        "scrapers",
                        scraper.state_name,
                        f"{scraper.state_name}.json",
                    )
                ) as scraper_results_file:
                    print(
                        f"{Bcolors.OKBLUE}Pre-existing data file found for "
                        f"{state_name}{Bcolors.ENDC}."
                    )
                    scraper.election_offices = json.load(scraper_results_file)
            except FileNotFoundError:
                print(
                    f"{Bcolors.OKBLUE}Pre-existing data file not found for "
                    f"{state_name}. Loading from scraper.{Bcolors.ENDC}"
                )
                tasks.append(asyncio.create_task(self._get_scraper_data(scraper)))
        if tasks:
            future: Future
            for future in asyncio.as_completed(tasks):
                try:
                    scraper_states_name = await future
                except WalkTheVoteError as e:
                    self.failed_scraper_data_retrieval_msgs.append(e)
                else:
                    print(
                        f"{Bcolors.OKBLUE}{scraper_states_name} scraper data loaded "
                        f"into memory\n "
                        f"{Bcolors.ENDC}"
                    )

    async def load_election_office_info(self):
        """Insert election office information gathered from scrapers into the
        database"""
        await self._get_election_office_info()
        issues = []
        for scraper in tqdm(self.scrapers, desc="Loading office info into database"):
            s_data: Dict
            for s_data in scraper.election_offices:
                # Get addresses. If either don't exist, default to an empty dict so get
                # methods below still work
                physical_address = s_data.get("physicalAddress", {})
                mailing_address = s_data.get("mailingAddress", {})
                county_name = s_data.get("countyName")
                # Try to get city name from physical first, default to mailing
                city_name = s_data.get(
                    "cityName",
                    physical_address.get("city", mailing_address.get("city")),
                )
                state_name = physical_address.get("state", mailing_address.get("state"))
                try:
                    # Try to get zip code from physical first, default to mailing
                    zip_code = physical_address.get(
                        "zipCode", mailing_address.get("zipCode")
                    )[:5]
                    zip_code_doc = ZipCode.objects.get({"_id": zip_code})
                    election_office = ElectionOffice(
                        phone_number=s_data.get("phone"),
                        email_address=s_data.get("email"),
                        office_supervisor=s_data.get("officeSupervisor"),
                        supervisor_title=s_data.get("supervisorTitle"),
                        website=s_data.get("website"),
                    )
                    if physical_address:
                        election_office.physical_address = PhysicalAddress(
                            location_name=physical_address.get("locationName"),
                            street=physical_address.get("streetNumberName"),
                            apt_unit=physical_address.get("aptNumber"),
                            po_box=physical_address.get("poBox"),
                            city=city_name,
                            state=physical_address.get("state"),
                            zip_code=zip_code,
                        )
                    if mailing_address:
                        election_office.mailing_address = MailingAddress(
                            location_name=mailing_address.get("locationName"),
                            street=mailing_address.get("streetNumberName"),
                            apt_unit=mailing_address.get("aptNumber"),
                            po_box=mailing_address.get("poBox"),
                            city=city_name,
                            state=mailing_address.get("state"),
                            zip_code=zip_code,
                        )
                    if county_name:
                        election_office.county_name = county_name
                        county_id = zip_code_doc.parent_city.parent_county.county_name
                        County.objects.raw({"_id": county_id}).update(
                            {"$set": {"election_office": election_office.to_son()}},
                            upsert=True,
                        )
                    else:
                        city_id = zip_code_doc.parent_city.city_name
                        City.objects.raw({"_id": city_id}).update(
                            {"$set": {"election_office": election_office.to_son()}},
                            upsert=True,
                        )
                except ZipCode.DoesNotExist as e:
                    print(
                        f"{Bcolors.OKBLUE}\nCould not load "
                        f"{county_name if not None else city_name}, {state_name} data: "
                        f"{type(e).__name__}{Bcolors.ENDC}"
                    )
                    issues.append(
                        {
                            "county": county_name,
                            "city": city_name,
                            "election_office": s_data,
                        }
                    )
                except (WriteError, TypeError) as e:
                    print(
                        f"{Bcolors.OKBLUE}\nCould not load "
                        f"{county_name if county_name is not None else city_name}, "
                        f"{state_name} data: {e}{Bcolors.ENDC}"
                    )
                    issues.append(
                        {
                            "county": county_name,
                            "city": city_name,
                            "election_office": s_data,
                        }
                    )
                except ValidationError as e:
                    print(
                        f"{Bcolors.OKBLUE}\nCould not load "
                        f"{county_name if not None else city_name}, {state_name} data: "
                        f"{e}{Bcolors.ENDC}"
                    )
                    issues.append(
                        {
                            "county": county_name,
                            "city": city_name,
                            "election_office": s_data,
                        }
                    )
        with open(os.path.join(ROOT_DIR, "issues.json"), "w") as f:
            json.dump(issues, f)

    @staticmethod
    def set_validation_rules():
        client = MongoClient(LOCAL_DB_URI)
        db = client[LOCAL_DB_NAME]
        collection_names = db.list_collection_names()
        if "county" not in collection_names:
            db.create_collection(
                "county", validator=VALIDATION_RULES["county"]["validator"]
            )
        if "city" not in collection_names:
            db.create_collection(
                "city", validator=VALIDATION_RULES["city"]["validator"]
            )


async def main():
    os.path.exists(os.path.join(ROOT_DIR, "scrapers", "new_hamphsire"))
    wtv_db = WtvDbHandler(LOCAL_DB_URI, LOCAL_DB_ALIAS)
    try:
        await wtv_db.load_election_office_info()
    except WalkTheVoteError as e:
        print(e)

    if wtv_db.failed_scraper_data_retrieval_msgs:
        print(*wtv_db.failed_scraper_data_retrieval_msgs, sep="\n\n")


if __name__ == "__main__":
    # asyncio.run(main()) causes error when program completes
    # https://github.com/aio-libs/aiohttp/issues/4324
    start = time.time()
    asyncio.get_event_loop().run_until_complete(main())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
