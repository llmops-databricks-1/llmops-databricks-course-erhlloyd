from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="MUSHROOM",
    settings_files=["../../project_config.yml"],
    environments=False,
)
