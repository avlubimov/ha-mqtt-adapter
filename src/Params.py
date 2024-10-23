import configparser


class Params:
    username: str
    password: str
    host: str
    verbose: int
    port: int = 1883
    timeout: int = 60

    def __init__(self, options):
        config = configparser.ConfigParser()
        if len(config.read(options.config_file)) == 0:
            raise (Exception(f"file {options.config_file} not found or uncorrect"))
        for key in self.__annotations__:
            if key in config.defaults():
                setattr(self, key, self.__annotations__[key](config.defaults()[key]))
            if hasattr(options, key) and getattr(options, key):
                setattr(self, key, self.__annotations__[key](getattr(options, key)))

    def __str__(self):
        result = ""
        for key in self.__annotations__:
            result += f"{key}:{getattr(self, key, None)}\n"
        return result
