import collections
import elasticsearch as elasticsearch
import re

from esctl.main import Esctl
from esctl.utils import Color, flatten_dict
from esctl.override import EsctlCommand, EsctlLister
from esctl.cmd.settings import ClusterSettings


class ClusterAllocationExplain(EsctlLister):
    """Provide explanations for shard allocations in the cluster."""

    def take_action(self, parsed_args):
        try:
            response = Esctl._es.cluster.allocation_explain()
        except elasticsearch.TransportError as e:
            if e.args[0] == 400:
                error_message = e.args[2].get("error").get("reason")
                match = re.match(
                    "^(unable to find any unassigned shards to explain)",
                    error_message,
                )
                if match is not None:
                    self.log.warn(
                        match.group(0).capitalize()
                        + ". This may indicate that all shards are allocated."
                    )

                    return (("Attribute", "Value"), tuple())
        else:
            output = {
                "index": response.get("index"),
                "can_allocate": response.get("can_allocate"),
                "explanation": response.get("allocate_explanation"),
                "last_allocation_status": response.get("unassigned_info").get(
                    "last_allocation_status"
                ),
                "reason": response.get("unassigned_info").get("reason"),
            }

            for node in response.get("node_allocation_decisions"):
                output[node.get("node_name")] = node.get("deciders")[0].get(
                    "explanation"
                )

            return (("Attribute", "Value"), tuple(output.items()))


class ClusterHealth(EsctlLister):
    """Retrieve the cluster health."""

    def take_action(self, parsed_args):
        health = collections.OrderedDict(
            sorted(Esctl._es.cluster.health().items())
        )

        health["status"] = "{}{}{}".format(
            *self.colorize_cluster_status(health["status"])
        )

        return (("Attribute", "Value"), tuple(health.items()))

    def colorize_cluster_status(self, status):
        return (getattr(Color, status.upper(), "END"), status, Color.END)


class ClusterStats(EsctlCommand):
    """Retrieve the cluster status."""

    def take_action(self, parsed_args):
        cluster_stats = self.transform(flatten_dict(Esctl._es.cluster.stats()))
        Esctl._pp.pprint(cluster_stats)

    def transform(self, stats):
        plugins_as_string = ""
        for plugin in stats.get("nodes.plugins"):
            plugins_as_string += "{}@{} ".format(
                plugin.get("classname"), plugin.get("version")
            )

        stats["nodes.plugins"] = plugins_as_string

        return stats


class ClusterRoutingAllocationEnable(EsctlCommand):
    """Change the routing allocation status."""

    settings = ClusterSettings()

    def take_action(self, parsed_args):
        persistency = "transient"
        parsed_args.status = parsed_args.status.upper()

        if parsed_args.persistent:
            persistency = "persistent"

        self.log.debug("Persistency is " + persistency)
        self.log.info(
            "Changing cluster routing allocation to : {}".format(
                parsed_args.status
            )
        )

        self.settings.set(
            "cluster.routing.allocation.enable",
            parsed_args.status,
            persistency=persistency,
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "status", metavar="<status>", help=("Routing allocation status")
        )
        persistency_group = parser.add_mutually_exclusive_group()
        persistency_group.add_argument(
            "--transient",
            action="store_true",
            help=("Set setting as transient (default)"),
        )
        persistency_group.add_argument(
            "--persistent",
            action="store_true",
            help=("Set setting as persistent"),
        )
        return parser
