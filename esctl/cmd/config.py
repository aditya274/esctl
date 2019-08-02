from esctl.override import EsctlLister
from esctl.main import Esctl
from esctl.utils import JSONFormatter


class ConfigContextList(EsctlLister):
    """List all contexts."""

    def take_action(self, parsed_args):
        contexts = []

        for context_name, context_definition in Esctl._config.contexts.items():
            contexts.append(
                {
                    "name": context_name,
                    "user": context_definition.get("user"),
                    "cluster": context_definition.get("cluster"),
                }
            )

        json_formatter = JSONFormatter(contexts)
        return json_formatter.to_lister(
            columns=[("name"), ("user"), ("cluster")]
        )
