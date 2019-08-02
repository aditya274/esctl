from esctl.override import EsctlLister
from esctl.main import Esctl
from esctl.utils import Color, JSONFormatter, colorize


class CatAllocation(EsctlLister):
    """Show shard allocation.

    Provides a snapshot of how shards have located around the cluster and the
    state of disk usage.
    """

    def take_action(self, parsed_args):
        allocation = Esctl._es.cat.allocation(format="json")

        allocation = self.transform(allocation)

        return JSONFormatter(allocation).to_lister(
            columns=[
                ("shards"),
                ("disk.indices"),
                ("disk.used"),
                ("disk.avail"),
                ("disk.total"),
                ("disk.percent", "Disk %"),
                ("host"),
                ("ip", "IP"),
                ("node"),
            ]
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def transform(self, allocation):
        nodes = []

        for node in allocation:
            if int(node.get("disk.percent")) > 90:
                node["disk.percent"] = colorize(
                    node["disk.percent"], Color.RED
                )

            elif int(node.get("disk.percent")) > 75:
                node["disk.percent"] = colorize(
                    node["disk.percent"], Color.YELLOW
                )

            nodes.append(node)

        return nodes
