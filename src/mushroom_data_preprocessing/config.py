import os

from dynaconf import Dynaconf
from loguru import logger

settings_files_yml = "../project_config.yml"
logger.debug(f"Settings_files set to: {settings_files_yml}")

settings = Dynaconf(
    envvar_prefix="MUSHROOM",
    settings_files=[settings_files_yml],
    environments=False,
)
logger.debug(f"settings configured files: {settings._loaded_files}")

if settings._loaded_files:
    logger.debug(f"{os.path.exists(settings._loaded_files[0])}")
