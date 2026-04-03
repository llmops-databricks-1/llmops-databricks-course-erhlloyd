# ruff: noqa: E402
"""
Scraper to handle the gathering of metadata from the website for 4k mushroom entries
and upload to databricks as delta table.
"""

import time

import pandas as pd
from loguru import logger

logger.add("inspect_service.log")

from src.mushroom_data_preprocessing.constants import GERMAN_INDEX_SOURCE
from src.mushroom_data_preprocessing.scraper import (
    retrieve_base_url,
    scrape_individual_mushroom_page,
    scrape_mushroom_table,
)

BASE_URL = retrieve_base_url(GERMAN_INDEX_SOURCE)


class MushroomDataProcessingService:
    def __init__(self):
        self.index_table = pd.DataFrame({})
        self.metadata_table = pd.DataFrame({})

    def _populate_index_table(self) -> None:
        self.index_table = scrape_mushroom_table(GERMAN_INDEX_SOURCE)
        time.sleep(3)

    def _populate_metadata_table(self, debug_limit: int = None) -> None:
        list_of_pages = []
        for link in self.index_table["german_link_url"][0:debug_limit]:
            metadata, _ = scrape_individual_mushroom_page(link)
            list_of_pages.append(metadata)

        self.metadata_table = pd.json_normalize(list_of_pages)

    def process_retrieval(self, debug_limit: int = 10) -> None:
        logger.info("Beginning retrieval of index table...")
        self._populate_index_table()
        logger.info(f"Completed! Index table contains records: {self.index_table.shape}")
        logger.info(f"Beginning retrieval of metadata table with {debug_limit} rows: ...")
        self._populate_metadata_table(debug_limit)
        logger.info(
            f"Completed! Metadata table contains records: {self.metadata_table.shape}"
        )

    def upload_to_delta_lake(self) -> None:
        pass
