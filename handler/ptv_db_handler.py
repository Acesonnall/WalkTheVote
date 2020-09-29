"""Scraper CLI for running scrapers

Command-Line Interface for running scrapers more easily and dumping results to the
Pog the Vote data
"""
import os
import time

import pandas as pd
from pymodm import (
    connect,
    MongoModel,
    EmbeddedMongoModel,
    CharField,
    ReferenceField,
    ListField,
    EmbeddedDocumentField,
    EmailField,
)
from pymongo import WriteConcern


class Address(EmbeddedMongoModel):
    state = CharField(verbose_name="Name of state", required=True)
    zip_code = CharField(verbose_name="Name of zip code", required=True)
    location_name = CharField(verbose_name="Name of election office", required=True)
    street = CharField(verbose_name="Name of street", required=True)
    apt_unit = CharField(verbose_name="Apartment or unit number")
    po_box = CharField(verbose_name="Name of PO Box")


class ElectionOffice(MongoModel):
    physical_address = EmbeddedDocumentField(
        Address, verbose_name="Phyiscal address information", required=True
    )
    phone_number = CharField(verbose_name="Office phone number", required=True)
    email_address = EmailField(verbose_name="Office email address")
    office_supervisor = CharField(verbose_name="Name of office supervisor")
    supervisor_title = CharField(verbose_name="Job title of office supervisor")
    website = CharField(verbose_name="Website data was fetched from", required=True)


class State(MongoModel):
    state_name = CharField(
        verbose_name="Name of State", primary_key=True, required=True
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = os.environ.get("MONGO_DB_TEST_ALIAS")


class County(MongoModel):
    county_name = CharField(verbose_name="Name of county", primary_key=True)
    parent_states = ListField(
        ReferenceField(State), verbose_name="States county belongs to", required=True
    )
    election_offices = ListField(
        ReferenceField(
            ElectionOffice, verbose_name="County election office information"
        )
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = os.environ.get("MONGO_DB_TEST_ALIAS")


class City(MongoModel):
    city_name = CharField(verbose_name="Name of city", primary_key=True, required=True)
    parent_counties = ListField(
        ReferenceField(County), verbose_name="Counties city belongs to", required=True
    )
    election_offices = ListField(
        ReferenceField(ElectionOffice, verbose_name="City election office information")
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = os.environ.get("MONGO_DB_TEST_ALIAS")


class ZipCode(MongoModel):
    zip_code = CharField(
        verbose_name="Zip Code",
        primary_key=True,
        min_length=5,
        max_length=5,
        required=True,
    )
    parent_city = ReferenceField(
        City, verbose_name="City zip code belongs to", required=True
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = os.environ.get("MONGO_DB_TEST_ALIAS")


def main():
    print(f"Start: {time.time()}")
    df = pd.read_csv("../scrapers/zip_county_mapping/out.csv")

    connect(os.environ.get('MONGO_DB_TEST_URI'), alias=os.environ.get("MONGO_DB_TEST_ALIAS"))

    for row in df.itertuples():
        print(f"Index {row.Index} start time: {time.time()}")
        State(state_name=row.State).save()
        County.objects.raw({"_id": row.County}).update(
            {
                "$setOnInsert": {"_id": row.County},
                "$addToSet": {"parent_states": row.State},
            },
            upsert=True,
        )
        City.objects.raw({"_id": row.Cities}).update(
            {
                "$setOnInsert": {"_id": row.Cities},
                "$addToSet": {"parent_counties": row.County},
            },
            upsert=True,
        )
        padded_zip = f"{row.Zip:05}"
        ZipCode.objects.raw({"_id": padded_zip}).update(
            {"$setOnInsert": {"_id": padded_zip, "parent_city": row.Cities}},
            upsert=True,
        )
        print(f"Index {row.Index} end time: {time.time()}")

    print(f"End: {time.time()}")


if __name__ == "__main__":
    main()
