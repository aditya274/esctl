import logging
import elasticsearch as elasticsearch
from abc import ABC
import sys

from box import Box
from esctl.main import Esctl


class Settings(ABC):
    """Abstract class for settings management."""

    log = logging.getLogger(__name__)

    def __init__(self):
        super(Settings, self).__init__()

    def get(self, sections):
        raise NotImplementedError()

    def set(self, sections, value):
        raise NotImplementedError()


class ClusterSettings(Settings):
    """Handle cluster-level settings."""

    def __init__(self):
        super(ClusterSettings, self).__init__()

    def get(self, key, persistency="transient"):
        settings = Esctl._es.cluster.get_settings(
            include_defaults=True, flat_settings=True
        ).get(persistency)

        if key in settings:
            return settings.get(key).upper()
        else:
            self.log.error(
                "{} does not exists in cluster settings".format(key)
            )
            return None

    def set(self, sections, value, persistency="transient"):
        try:
            Esctl._es.cluster.put_settings(
                body={persistency: {sections: value}}
            )
        except elasticsearch.TransportError as error:
            self.log.critical(
                error.args[2].get("error").get("reason").capitalize()
            )


class IndexSettings(Settings):
    """Handle index-level settings."""

    def __init__(self, index="_all"):
        super(IndexSettings, self).__init__()
        self.index = index

    def get(self, setting_name):
        try:
            settings = Esctl._es.indices.get_settings(
                index=self.index, include_defaults=True, flat_settings=True
            )
        except elasticsearch.exceptions.NotFoundError as err:
            self.log.error(
                "{} : {}".format(
                    err.info.get("error")
                    .get("root_cause")[0]
                    .get("reason")
                    .capitalize(),
                    self.index,
                )
            )
            sys.exit(1)
        else:
            return [
                Box(
                    {
                        "index": index_name,
                        "setting": setting_name,
                        "value": index_settings.get("settings").get(
                            setting_name
                        ),
                    }
                )
                for index_name, index_settings in sorted(settings.items())
            ]

    def set(self, sections, value):
        try:
            Esctl._es.indices.put_settings(
                index=self.index, body={sections: value}, flat_settings=True
            )
        except elasticsearch.TransportError as err:
            self.log.error(
                "{} : {}".format(
                    err.info.get("error")
                    .get("root_cause")[0]
                    .get("reason")
                    .capitalize(),
                    self.index,
                )
            )
            sys.exit(1)
