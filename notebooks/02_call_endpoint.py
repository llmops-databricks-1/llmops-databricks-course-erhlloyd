# Databricks notebook source
"""
STEP 02: Create and call endpoint with dataset
"""

# COMMAND ----------
from databricks.sdk import WorkspaceClient
from loguru import logger
from openai import OpenAI
from pyspark.sql import SparkSession

from mushroom_data_preprocessing.config import settings

# COMMAND ----------
w = WorkspaceClient()
spark = SparkSession.builder.getOrCreate()

settings.configure("dev")

host = settings.get("host")
token = w.tokens.create(lifetime_seconds=1200).token_value

client = OpenAI(api_key=token, base_url=f"{host.rstrip('/')}/serving-endpoints")

model_name = settings.get("llm_endpoint")
catalog = settings.dev.get("catalog")
schema = settings.dev.get("schema")
table_name = "mushroom_metadata"

query = f"""
  SELECT *
  FROM {catalog}.{schema}.{table_name}
  LIMIT 5
  """

# COMMAND ----------
query_df = spark.sql(query)
all_text = query_df.toPandas().to_markdown(index=False)
logger.info("Query success: connected to data")


# COMMAND ----------
response = client.chat.completions.create(
    model=model_name,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a helpful AI assistant with access to "
                "a mushroom dataset, which is in German and which you will have to translate."
                "Questions will be posed to you in English."
                "If the data is insufficient to answer, say you don't know."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Mushroom metadata:\n\n{all_text}\n\n"
                "I have a mushroom which is white. Which mushroom could it be?"
            ),
        },
    ],
    max_tokens=500,
    temperature=0.7,
)

logger.info("Response:")
logger.info(response.choices[0].message.content)
logger.info(f"Tokens used: {response.usage.total_tokens}")
logger.info(f"Input tokens: {response.usage.prompt_tokens}")
logger.info(f"Output tokens: {response.usage.completion_tokens}")
