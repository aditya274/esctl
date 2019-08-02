from unittest import TestCase
from unittest.mock import patch

import esctl.main


class EsctlTestCase(TestCase):
    def _setUp(self):
        self.patcher = patch('esctl.cmd.cluster.Esctl')
        self.MockClass = self.patcher.start()
        self.app = esctl.main.Esctl()

    def mock(self, method_to_mock):
        self.MockClass._es.__setattr__(
            str(method_to_mock) + '.return_value',
            self.fixture()
        )

    def fixture(self):
        raise NotImplementedError()
