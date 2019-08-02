import sys

from esctl.override import EsctlCommand, EsctlLister
from esctl.main import Esctl
from esctl.utils import JSONFormatter
from esctl.cmd.settings import ClusterSettings


class NodeHotThreads(EsctlCommand):
    """Print hot threads on each nodes."""

    def take_action(self, parsed_args):
        print(Esctl._es.nodes.hot_threads(type=parsed_args.type))

    def get_parser(self, prog_name):
        parser = super(NodeHotThreads, self).get_parser(prog_name)
        parser.add_argument(
            "type",
            metavar="<type>",
            help=("Type"),
            choices=["cpu", "wait", "block"],
            default="cpu",
            nargs="?",
        )
        return parser


class NodeList(EsctlLister):
    """List nodes."""

    def take_action(self, parsed_args):
        nodes = Esctl._es.cat.nodes(format="json")

        json_formatter = JSONFormatter(nodes)
        return json_formatter.to_lister(
            columns=[
                ("ip", "IP"),
                ("heap.percent", "Heap %"),
                ("ram.percent", "RAM %"),
                ("cpu"),
                ("load_1m"),
                ("load_5m"),
                ("load_15m"),
                ("node.role", "Role"),
                ("master"),
                ("name"),
            ]
        )
