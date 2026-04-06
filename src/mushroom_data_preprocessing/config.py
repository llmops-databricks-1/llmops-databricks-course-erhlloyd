import os

from dynaconf import Dynaconf
from loguru import logger

pth = os.path.dirname(__file__)
settings_files_yml = os.path.join(pth, "../../project_config.yml")
logger.debug(f"Settings_files set to: {settings_files_yml}")

settings = Dynaconf(
    envvar_prefix="MUSHROOM",
    settings_files=[settings_files_yml],
    environments=False,
)
