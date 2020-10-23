import io
import json
import os
import time

import cloudscraper
import pandas as pd
import us

from lib.definitions import Bcolors, ROOT_DIR
from lib.errors.wtv_errors import WalkTheVoteError

DIRECTORY = os.path.join(ROOT_DIR, "handler", "zip_mapping")


def create_mapping():
    csv_path = os.path.join(DIRECTORY, "zip_code_database.csv")
    if not os.path.isfile(csv_path):
        raise WalkTheVoteError(
            f'Prerequisite CSV file needed to create database mapping.\n\nPlease go to '
            f'https://www.unitedstateszipcodes.org/zip-code-database/ and download\nthe'
            f' free zip code database file to {DIRECTORY}.\n\nMake sure the downloaded '
            f'file is named "zip_code_database.csv"'
        )
    mapping_df = pd.read_csv(csv_path)
    final_mapping = {}
    for (
        zip_code,
        primary_city,
        acceptable_cities,
        unacceptable_cities,
        state,
        county,
    ) in zip(
        mapping_df["zip"].values,
        mapping_df["primary_city"].values,
        mapping_df["acceptable_cities"].values,
        mapping_df["unacceptable_cities"].values,
        mapping_df["state"].values,
        mapping_df["county"].values,
    ):
        a_cities = ""
        u_cities = ""
        if not pd.isna(acceptable_cities):
            a_cities = f", {acceptable_cities}"
        if not pd.isna(unacceptable_cities):
            u_cities = f", {unacceptable_cities}"
        final_mapping[f"{zip_code:05}"] = {
            f"{primary_city}{a_cities}{u_cities}": {
                county: str(us.states.lookup(state))
            }
        }

    with open(os.path.join(DIRECTORY, "mapping.json"), "w") as f:
        json.dump(final_mapping, f)
    return final_mapping


if __name__ == "__main__":
    start = time.time()
    try:
        create_mapping()
    except WalkTheVoteError as e:
        print(e)
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
