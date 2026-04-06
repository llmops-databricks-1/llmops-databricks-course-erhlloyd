# we similarly make use of pydantic here


import os

from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="MUSHROOM",
    settings_files=[os.path.join(os.getcwd(), "project_config.yml")],
    environments=False,
)
