import unittest

from esctl.utils import JSONFormatter


class TestCreateColumnNameFromKey(unittest.TestCase):
    def setUp(self):
        self.json_formatter = JSONFormatter({})

    def test_title_interpolation(self):
        cases = [
            {"input": ("foobar",), "expected_output": "Foobar"},
            {"input": ("foo_bar",), "expected_output": "Foo Bar"},
            {"input": ("foo.bar",), "expected_output": "Foo Bar"},
            {"input": ("foo-bar",), "expected_output": "Foo-Bar"},
        ]

        for element in cases:
            self.assertEqual(
                self.json_formatter._create_column_name_from_key(
                    element.get("input")
                ),
                element.get("expected_output"),
            )

    def test_title_from_second_item(self):
        cases = [{"input": ("foo", "bar"), "expected_output": "bar"}]

        for element in cases:
            self.assertEqual(
                self.json_formatter._create_column_name_from_key(
                    element.get("input")
                ),
                element.get("expected_output"),
            )
