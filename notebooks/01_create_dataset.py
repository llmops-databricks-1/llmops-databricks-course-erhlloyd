# Databricks notebook source
"""
STEP 01: Scrape the data from the website and create delta table.
"""

# COMMAND ----------
from mushroom_data_preprocessing.service import MushroomDataProcessingService

# COMMAND ----------
dataset_service = MushroomDataProcessingService()

# COMMAND ----------
dataset_service.process()
