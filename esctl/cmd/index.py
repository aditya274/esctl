from esctl.override import EsctlCommand, EsctlLister
from esctl.cmd.settings import IndexSettings
from esctl.main import Esctl
from esctl.utils import JSONFormatter, print_output


class IndexCreate(EsctlCommand):
    """Create an index."""

    def take_action(self, parsed_args):
        self.log.info(
            "Creating index {} with {} shards and {} replicas".format(
                parsed_args.index, 0, 0
            )
        )
        Esctl._es.indices.create(index=parsed_args.index)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "index", metavar="<index>", help=("Index to create")
        )
        return parser


class IndexList(EsctlLister):
    """List all indices."""

    settings = IndexSettings()

    def take_action(self, parsed_args):
        indices = Esctl._es.cat.indices(format="json")
        json_formatter = JSONFormatter(indices)
        return json_formatter.to_lister(
            columns=[
                ("index"),
                ("health",),
                ("status"),
                ("uuid", "UUID"),
                ("pri", "Primary"),
                ("rep", "Replica"),
                ("docs.count"),
                ("docs.deleted"),
                ("store.size"),
                ("pri.store.size", "Primary Store Size"),
            ]
        )


class IndexClose(EsctlCommand):
    """Close an index."""

    settings = IndexSettings()

    def take_action(self, parsed_args):
        self.log.info("Closing index " + parsed_args.index)
        Esctl._es.indices.close(index=parsed_args.index)

    def get_parser(self, prog_name):
        parser = super(IndexClose, self).get_parser(prog_name)
        parser.add_argument(
            "index", metavar="<index>", help=("Index to close")
        )
        return parser


class IndexDelete(EsctlCommand):
    """Delete an index."""

    settings = IndexSettings()

    def take_action(self, parsed_args):
        self.log.info("Deleting index " + parsed_args.index)
        Esctl._es.indices.delete(index=parsed_args.index)

    def get_parser(self, prog_name):
        parser = super(IndexDelete, self).get_parser(prog_name)
        parser.add_argument(
            "index", metavar="<index>", help=("Index to delete")
        )
        return parser


class IndexOpen(EsctlCommand):
    """Open an index."""

    settings = IndexSettings()

    def take_action(self, parsed_args):
        self.log.info("Opening index " + parsed_args.index)
        Esctl._es.indices.open(index=parsed_args.index)

    def get_parser(self, prog_name):
        parser = super(IndexOpen, self).get_parser(prog_name)
        parser.add_argument(
            "index", metavar="<index>", help=("Index to close")
        )
        return parser
