""" Schema
"""

from pymodm import (
    EmbeddedMongoModel,
    CharField,
    MongoModel,
    EmbeddedDocumentField,
    EmailField,
    ReferenceField,
)
from pymongo import WriteConcern

from lib.definitions import LOCAL_DB_ALIAS


class PhysicalAddress(EmbeddedMongoModel):
    state = CharField(verbose_name="Name of state", required=True)
    city = CharField(verbose_name="Name of city", required=True)
    zip_code = CharField(
        verbose_name="Name of zip code", min_length=5, max_length=5, required=True
    )
    location_name = CharField(verbose_name="Name of election office", required=True)
    street = CharField(verbose_name="Name of street", required=True)
    apt_unit = CharField(verbose_name="Apartment or unit number")
    po_box = CharField(verbose_name="Name of PO Box")


class MailingAddress(PhysicalAddress):
    street = CharField(verbose_name="Name of street")


class ElectionOffice(EmbeddedMongoModel):
    county_name = CharField(verbose_name="Name of county", required=True)
    physical_address = EmbeddedDocumentField(
        PhysicalAddress, verbose_name="Phyiscal address information"
    )
    mailing_address = EmbeddedDocumentField(
        MailingAddress, verbose_name="Mailing address information"
    )
    phone_number = CharField(verbose_name="Office phone number", required=True)
    email_address = EmailField(verbose_name="Office email address")
    office_supervisor = CharField(verbose_name="Name of office supervisor")
    supervisor_title = CharField(verbose_name="Job title of office supervisor")
    website = CharField(verbose_name="Website data was fetched from", required=True)

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = LOCAL_DB_ALIAS


class State(MongoModel):
    state_name = CharField(
        verbose_name="Name of State", primary_key=True, required=True
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = LOCAL_DB_ALIAS


class County(MongoModel):
    county_name = CharField(verbose_name="Name of county", primary_key=True)
    parent_state = ReferenceField(
        State, verbose_name="States county belongs to", required=True
    )
    election_office = EmbeddedDocumentField(
        ElectionOffice, verbose_name="County election office information"
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = LOCAL_DB_ALIAS


class City(MongoModel):
    city_name = CharField(verbose_name="Name of city", primary_key=True, required=True)
    parent_county = ReferenceField(
        County, verbose_name="County city belongs to", required=True
    )
    election_office = ReferenceField(
        ElectionOffice, verbose_name="City election office information"
    )

    class Meta:
        write_concern = WriteConcern(j=True)
        connection_alias = LOCAL_DB_ALIAS


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
        connection_alias = LOCAL_DB_ALIAS
