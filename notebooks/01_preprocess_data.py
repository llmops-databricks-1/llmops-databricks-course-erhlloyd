# Databricks notebook source
"""
STEP 01: Scrape the data from the website.
"""

# COMMAND ----------
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

# COMMAND ----------
BASE_URL = "https://www.pilzsuchmaschine.de/123pilze"
TABLE_PAGE = f"{BASE_URL}/2015Alphabethisch-LAT.htm"

from mushroom_data_preprocessing.constants import GERMAN_SOURCE
from mushroom_data_preprocessing.scraper import scrape_mushroom_table

# COMMAND ----------
df = scrape_mushroom_table(GERMAN_SOURCE)

# COMMAND ----------
print(f"{df.shape}")