import logging
import time
import gzip
import sys

from cliff.command import Command
from cliff.lister import Lister
from cliff.show import ShowOne
from urllib3.util.retry import Retry
from urllib3.exceptions import (
    ReadTimeoutError,
    SSLError as UrllibSSLError,
    NewConnectionError,
)
from elasticsearch.transport import Transport
from elasticsearch import ConnectionError, ConnectionTimeout, SSLError
from elasticsearch.connection import Urllib3HttpConnection
from elasticsearch.connection_pool import ConnectionPool
from elasticsearch.serializer import (
    JSONSerializer,
    Deserializer,
    DEFAULT_SERIALIZERS,
)
from elasticsearch.compat import urlencode


class EsctlCommand(Command):
    """docstring for EsctlCommand."""

    log = logging.getLogger(__name__)


class EsctlLister(Lister):
    """docstring for EsctlLister."""

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(EsctlLister, self).get_parser(prog_name)
        group = self._formatter_group
        group.add_argument(
            "-a",
            "--attribute",
            help="specify the attribute(s) to include (comma separated).",
        )
        return parser

    def get_by_attribute_name(self, attribute, data):
        attribute = attribute.split(",")
        data = dict((k, v) for k, v in data)
        return tuple([(attr, data.get(attr)) for attr in attribute])

    def run(self, parsed_args):
        parsed_args = self._run_before_hooks(parsed_args)
        self.formatter = self._formatter_plugins[parsed_args.formatter].obj
        column_names, data = self.take_action(parsed_args)

        if "attribute" in parsed_args and parsed_args.attribute is not None:
            data = self.get_by_attribute_name(parsed_args.attribute, data)

        column_names, data = self._run_after_hooks(
            parsed_args, (column_names, data)
        )
        self.produce_output(parsed_args, column_names, data)
        return 0


class EsctlShowOne(ShowOne):
    """docstring for EsctlShowOne."""

    log = logging.getLogger(__name__)


class EsctlUrllib3HttpConnection(Urllib3HttpConnection):

    log = logging.getLogger(__name__)

    def perform_request(
        self,
        method,
        url,
        params=None,
        body=None,
        timeout=None,
        ignore=(),
        headers=None,
    ):
        url = self.url_prefix + url
        if params:
            url = "%s?%s" % (url, urlencode(params))
        full_url = self.host + url

        start = time.time()
        try:
            kw = {}
            if timeout:
                kw["timeout"] = timeout

            # in python2 we need to make sure the url and method are not
            # unicode. Otherwise the body will be decoded into unicode too and
            # that will fail (#133, #201).
            if not isinstance(url, str):
                url = url.encode("utf-8")
            if not isinstance(method, str):
                method = method.encode("utf-8")

            request_headers = self.headers
            if headers:
                request_headers = request_headers.copy()
                request_headers.update(headers)
            if self.http_compress and body:
                try:
                    body = gzip.compress(body)
                except AttributeError:
                    # oops, Python2.7 doesn't have `gzip.compress` let's try
                    # again
                    body = gzip.zlib.compress(body)

            try:
                response = self.pool.urlopen(
                    method,
                    url,
                    body,
                    retries=Retry(False),
                    headers=request_headers,
                    **kw
                )
            except NewConnectionError as error:
                self.log.error(error.args[0])
                sys.exit(-1)

            duration = time.time() - start
            raw_data = response.data.decode("utf-8")
        except Exception as e:
            self.log_request_fail(
                method, full_url, url, body, time.time() - start, exception=e
            )
            if isinstance(e, UrllibSSLError):
                raise SSLError("N/A", str(e), e)
            if isinstance(e, ReadTimeoutError):
                raise ConnectionTimeout("TIMEOUT", str(e), e)
            raise ConnectionError("N/A", str(e), e)

        # raise errors based on http status codes, let the client handle those if needed
        if (
            not (200 <= response.status < 300)
            and response.status not in ignore
        ):
            self.log_request_fail(
                method,
                full_url,
                url,
                body,
                duration,
                response.status,
                raw_data,
            )
            self._raise_error(response.status, raw_data)

        self.log_request_success(
            method, full_url, url, body, response.status, raw_data, duration
        )

        return response.status, response.getheaders(), raw_data


def get_host_info(node_info, host):
    """
    Simple callback that takes the node info from `/_cluster/nodes` and a
    parsed connection information and return the connection information. If
    `None` is returned this node will be skipped.
    Useful for filtering nodes (by proximity for example) or if additional
    information needs to be provided for the :class:`~elasticsearch.Connection`
    class. By default master only nodes are filtered out since they shouldn't
    typically be used for API operations.
    :arg node_info: node information from `/_cluster/nodes`
    :arg host: connection information (host, port) extracted from the node info
    """
    # ignore master only nodes
    if node_info.get("roles", []) == ["master"]:
        return None
    return host


class EsctlTransport(Transport):

    log = logging.getLogger(__name__)

    """
    Encapsulation of transport-related to logic. Handles instantiation of the
    individual connections as well as creating a connection pool to hold them.
    Main interface is the `perform_request` method.
    """

    def __init__(
        self,
        hosts,
        connection_class=EsctlUrllib3HttpConnection,
        connection_pool_class=ConnectionPool,
        host_info_callback=get_host_info,
        sniff_on_start=False,
        sniffer_timeout=None,
        sniff_timeout=0.1,
        sniff_on_connection_fail=False,
        serializer=JSONSerializer(),
        serializers=None,
        default_mimetype="application/json",
        max_retries=3,
        retry_on_status=(502, 503, 504),
        retry_on_timeout=False,
        send_get_body_as="GET",
        **kwargs
    ):
        """
        :arg hosts: list of dictionaries, each containing keyword arguments to
            create a `connection_class` instance
        :arg connection_class: subclass of :class:`~elasticsearch.Connection` to use
        :arg connection_pool_class: subclass of :class:`~elasticsearch.ConnectionPool` to use
        :arg host_info_callback: callback responsible for taking the node information from
            `/_cluser/nodes`, along with already extracted information, and
            producing a list of arguments (same as `hosts` parameter)
        :arg sniff_on_start: flag indicating whether to obtain a list of nodes
            from the cluser at startup time
        :arg sniffer_timeout: number of seconds between automatic sniffs
        :arg sniff_on_connection_fail: flag controlling if connection failure triggers a sniff
        :arg sniff_timeout: timeout used for the sniff request - it should be a
            fast api call and we are talking potentially to more nodes so we want
            to fail quickly. Not used during initial sniffing (if
            ``sniff_on_start`` is on) when the connection still isn't
            initialized.
        :arg serializer: serializer instance
        :arg serializers: optional dict of serializer instances that will be
            used for deserializing data coming from the server. (key is the mimetype)
        :arg default_mimetype: when no mimetype is specified by the server
            response assume this mimetype, defaults to `'application/json'`
        :arg max_retries: maximum number of retries before an exception is propagated
        :arg retry_on_status: set of HTTP status codes on which we should retry
            on a different node. defaults to ``(502, 503, 504)``
        :arg retry_on_timeout: should timeout trigger a retry on different
            node? (default `False`)
        :arg send_get_body_as: for GET requests with body this option allows
            you to specify an alternate way of execution for environments that
            don't support passing bodies with GET requests. If you set this to
            'POST' a POST method will be used instead, if to 'source' then the body
            will be serialized and passed as a query parameter `source`.
        Any extra keyword arguments will be passed to the `connection_class`
        when creating and instance unless overridden by that connection's
        options provided as part of the hosts parameter.
        """

        # serialization config
        _serializers = DEFAULT_SERIALIZERS.copy()
        # if a serializer has been specified, use it for deserialization as well
        _serializers[serializer.mimetype] = serializer
        # if custom serializers map has been supplied, override the defaults with it
        if serializers:
            _serializers.update(serializers)
        # create a deserializer with our config
        self.deserializer = Deserializer(_serializers, default_mimetype)

        self.max_retries = max_retries
        self.retry_on_timeout = retry_on_timeout
        self.retry_on_status = retry_on_status
        self.send_get_body_as = send_get_body_as

        # data serializer
        self.serializer = serializer

        # store all strategies...
        self.connection_pool_class = connection_pool_class
        self.connection_class = connection_class

        # ...save kwargs to be passed to the connections
        self.kwargs = kwargs
        self.hosts = hosts

        # ...and instantiate them
        self.set_connections(hosts)
        # retain the original connection instances for sniffing
        self.seed_connections = self.connection_pool.connections[:]

        # sniffing data
        self.sniffer_timeout = sniffer_timeout
        self.sniff_on_connection_fail = sniff_on_connection_fail
        self.last_sniff = time.time()
        self.sniff_timeout = sniff_timeout

        # callback to construct host dict from data in /_cluster/nodes
        self.host_info_callback = host_info_callback

        if sniff_on_start:
            self.sniff_hosts(True)
