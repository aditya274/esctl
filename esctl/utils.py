import logging
import os
import yaml
import sys
from pathlib import Path

import cerberus


class Color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


class JSONFormatter:
    """docstring for JSONFormatter."""

    def __init__(self, json):
        super(JSONFormatter, self).__init__()
        self.json = json

    def _create_column_name_from_key(self, tup):
        column_name = ""

        if len(tup) == 1:
            column_name = tup[0]
            if "." in column_name:
                column_name = column_name.replace(".", " ")
            if "_" in column_name:
                column_name = column_name.replace("_", " ")

            column_name = column_name.title()
        else:
            column_name = tup[1]

        return column_name

    def _ensure_params_format(self, raw_list):
        valid_list = []

        for element in raw_list:
            if isinstance(element, str):
                element = (element,)
            valid_list.append(
                (element[0], self._create_column_name_from_key(element))
            )

        return tuple(valid_list)

    def to_lister(self, columns=[]):

        columns = self._ensure_params_format(columns)

        headers = []
        for element in columns:
            headers.append(element[1])
        headers = tuple(headers)

        lst = []
        for obj in self.json:
            row = []
            for element in columns:
                row.append(obj.get(element[0]))
            lst.append(tuple(row))

        return (headers, tuple(lst))

    def to_show_one(self, lines=[]):
        lines = self._ensure_params_format(lines)

        keys = []
        values = []

        for line in lines:
            keys.append(line[1])
            values.append(self.json.get(line[0]))

        return (tuple(keys), tuple(values))


class Context:
    """docstring for Context."""

    def __init__(self, name, **kwargs):
        super(Context, self).__init__()
        self.LOG = logging.getLogger(__name__)
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)


class ConfigFileParser:
    """docstring for ConfigFileParser."""

    log = logging.getLogger(__name__)

    def __init__(self):
        super(ConfigFileParser, self).__init__()
        self.path = os.path.expanduser("~") + "/.esctlrc"
        self.log.debug("Trying to load config file : {}".format(self.path))

    def _create_default_config_file(self):
        self.log.info(
            "{} config file does not exists. Creating a default one...".format(
                self.path
            )
        )
        default_config = {
            "settings": {},
            "clusters": {"localhost": {"servers": ["http://localhost:9200"]}},
            "users": {},
            "contexts": {"localhost": {"cluster": "localhost"}},
            "default-context": "localhost",
        }

        with open(self.path, "w") as config_file:
            yaml.dump(default_config, config_file, default_flow_style=False)

    def _ensure_config_file_is_valid(self, document):
        schema = {
            "settings": {"type": "dict"},
            "clusters": {"type": "dict"},
            "users": {"type": "dict"},
            "contexts": {"type": "dict"},
            "default-context": {"type": "string"},
        }
        cerberus_validator = cerberus.Validator(schema)

        if not cerberus_validator.validate(document):
            for error in cerberus_validator._errors:
                self.log.error(
                    "Invalid type for configuration field '{0}'. Should be {1}. Got '{2}'".format(
                        error.field, error.constraint, error.value
                    )
                )

            raise SyntaxError(
                "{} doesn't match expected schema".format(self.path)
            )

    def load_configuration(self):
        self.log.debug("Loading configuration...")
        config_blocks = [
            "clusters",
            "contexts",
            "default-context",
            "settings",
            "users",
        ]

        if not Path(self.path).is_file():
            self._create_default_config_file()

        with open(self.path, "r") as config_file:
            try:
                self.raw = yaml.safe_load(config_file)
            except yaml.YAMLError as err:
                self.log.critical("Cannot read YAML from {}".format(self.path))
                self.log.critical(str(err.problem) + str(err.problem_mark))
                sys.exit(1)

        try:
            self._ensure_config_file_is_valid(self.raw)
        except SyntaxError as err:
            sys.exit(1)

        for config_block in config_blocks:
            if not hasattr(self, config_block):
                setattr(self, config_block, None)
            self.load_config_block(config_block)
            self.log.debug(
                "{}: {}".format(config_block, getattr(self, config_block))
            )

    def load_config_block(self, key):
        if key in self.raw:
            setattr(self, key, self.raw.get(key))
        else:
            self.log.debug("Cannot find config block : " + key)

    def get_context_informations(self, context_name):
        user = self.users.get(self.contexts.get(context_name).get("user"))
        cluster = self.clusters.get(
            self.contexts.get(context_name).get("cluster")
        )

        # Merge global settings and per-cluster settings.
        # Cluster-level settings override global settings
        if 'settings' in cluster:
            settings = {**self.settings, **cluster.get('settings')}
        else:
            settings = {**self.settings}

        return Context(context_name, user=user, cluster=cluster, settings=settings)


def print_success(message):
    print("{}{}{} {}".format(Color.GREEN, "SUCCESS", Color.END, message))


def print_output(message):
    print("{}".format(message))


def flatten_dict(dictionary):
    def expand(key, value):
        if isinstance(value, dict):
            return [(key + "." + k, v) for k, v in flatten_dict(value).items()]
        else:
            return [(key, value)]

    items = [item for k, v in dictionary.items() for item in expand(k, v)]

    return dict(items)


def colorize(str, color):
    return "{}{}{}".format(color, str, Color.END)
