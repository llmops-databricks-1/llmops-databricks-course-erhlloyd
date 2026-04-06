# ruff: noqa: E402
"""
Scraper to handle the gathering of metadata from the website for 4k mushroom entries
and upload to databricks as delta table.
"""

import os
import time

import pandas as pd
from loguru import logger

logger.add("inspect_service.log")

from databricks.connect import DatabricksSession
from pyspark.sql import SparkSession
from pyspark.sql.types import ArrayType, StringType, StructField, StructType

from mushroom_data_preprocessing.config import settings
from mushroom_data_preprocessing.constants import GERMAN_INDEX_SOURCE
from mushroom_data_preprocessing.scraper import (
    retrieve_base_url,
    scrape_individual_mushroom_page,
    scrape_mushroom_table,
)

BASE_URL = retrieve_base_url(GERMAN_INDEX_SOURCE)


class MushroomDataProcessingService:
    def __init__(self):
        settings.configure(os.getenv("ENV_FOR_DYNACONF", "dev"))
        remote_profile_name = settings.get("remote_profile_name")

        self.index_table = pd.DataFrame({})
        self.metadata_table = pd.DataFrame({})
        try:
            self.spark = SparkSession.builder.getOrCreate()
        except RuntimeError:
            self.spark = (
                DatabricksSession.builder.serverless()
                .profile(remote_profile_name)
                .getOrCreate()
            )

    def _populate_index_table(self) -> None:
        self.index_table = scrape_mushroom_table(GERMAN_INDEX_SOURCE)
        time.sleep(3)

    def _populate_metadata_table(
        self, start_index: int = 0, end_index: int = 100
    ) -> None:
        list_of_pages = []
        for i, link in enumerate(
            self.index_table["german_link_url"][start_index:end_index]
        ):
            logger.debug(f"Working on link: {link}")
            metadata, _ = scrape_individual_mushroom_page(link)
            list_of_pages.append(metadata)
            if not i % 10:
                logger.debug("Sleep to avoid rate-limiting...")
                time.sleep(5)

        self.metadata_table = pd.json_normalize(list_of_pages)

    def process_retrieval(self, start_index: int = 0, end_index: int = 100) -> None:
        logger.info("Beginning retrieval of index table...")
        self._populate_index_table()
        logger.info(f"Completed! Index table contains records: {self.index_table.shape}")
        logger.info(
            "Beginning retrieval of metadata table "
            f"with {str(end_index - start_index)} rows: ..."
        )
        self._populate_metadata_table(start_index, end_index)
        logger.info(
            f"Completed! Metadata table contains records: {self.metadata_table.shape}"
        )
        self.metadata_table.to_csv("all_2.csv")

    def _create_schema(self) -> StructType:
        nested_image_links = ArrayType(
            StructType(
                [
                    StructField("link_url", StringType(), True),
                    StructField("thumbnail_url", StringType(), True),
                    StructField("alt_text", StringType(), True),
                    StructField("width", StringType(), True),
                    StructField("height", StringType(), True),
                ]
            )
        )

        characteristics = [
            StructField(column_name, StringType(), True)
            for column_name in self.metadata_table.columns
            if column_name.startswith("characteristics")
        ]

        base_schema = [
            StructField("edibility", StringType(), True),
            StructField("name", StringType(), False),
            StructField("images_links", nested_image_links, True),
        ]

        schema = StructType(base_schema + characteristics)

        return schema

    def reconfigure_env(self, env: str) -> None:
        settings.configure(env)

    def upload_to_delta_lake(self) -> None:
        if not settings.configured:
            logger.info("Settings not configured for environment, using dev env...")
            self.reconfigure_env("dev")

        schema = self._create_schema()

        spark_df = self.spark.createDataFrame(self.metadata_table, schema=schema)

        CATALOG = settings.dev.get("catalog")
        SCHEMA = settings.dev.get("schema")
        TABLE_NAME = "mushroom_metadata"

        # Create schema if it doesn't exist
        logger.debug(f"Creating schema {CATALOG}.{SCHEMA}...")
        self.spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
        logger.debug(f"Schema {CATALOG}.{SCHEMA} ready")

        fqn_table = f"{CATALOG}.{SCHEMA}.{TABLE_NAME}"

        spark_df.write.format("delta").mode("overwrite").option(
            "mergeSchema", "true"
        ).saveAsTable(fqn_table)

    def process(self) -> None:
        logger.info("Processing scraping of dataset from website...")
        self.process_retrieval()
        logger.info("Scraping completed! Processing upload to delta lake...")
        self.upload_to_delta_lake()
        logger.info("Upload completed!")
