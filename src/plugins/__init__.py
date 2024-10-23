from pathlib import Path
import pkgutil
from importlib import import_module

PLUGINS_DIR = Path(__file__).parent


def init_plugins(logger):
    return list(
        map(
            lambda mod: mod.init(logger),
            map(
                lambda mod: mod.module_finder.find_spec(mod.name).loader.load_module(mod.name),
                pkgutil.iter_modules([PLUGINS_DIR])
            )
        )
    )
