from typing import Dict

import pytest

from workflows_manager.utils.reference_resolver import get_variable, BaseType, ReferenceResolver


def create_match_side_effect(variables: Dict[str, BaseType]):
    def match_side_effect(group: str):
        return variables.get(group, None)

    return match_side_effect


class Test:
    def test_get_variable(self):
        variables = {
            "key1": {
                "key2": {
                    "key3": "value"
                }
            }
        }
        assert get_variable(variables, "key1.key2.key3") == "value"
        assert get_variable(variables, "key1.key2.key4") is None
        assert get_variable(variables, "key1.key2.key4", "default") == "default"
        assert get_variable(variables, "key1.key2") == {"key3": "value"}
        assert get_variable(variables, "key1.key2.key4") is None


class TestReferenceResolver:
    @pytest.mark.parametrize("value, expected", [
        ("{string}", "value"),
        ("{integer}", 1),
        ("{float}", 1.0),
        ("{boolean}", True),
        ("{list}", [1, 2, 3]),
        ("{dict}", {"key": "value"}),
    ], ids=[
        "string",
        "integer",
        "float",
        "boolean",
        "list",
        "dict",
    ])
    def test_resolve_element(self, value: str, expected: BaseType):
        variables = {
            "string": "value",
            "integer": 1,
            "float": 1.0,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }
        resolver = ReferenceResolver(variables)
        assert resolver.resolve_element(value) == expected

    def test_resolve(self):
        variables = {
            "string": "value",
            "integer": 1,
            "float": 1.0,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "reference_string": "{string}",
            "reference_integer": "{integer}",
            "reference_float": "{float}",
            "reference_boolean": "{boolean}",
            "reference_list": "{list}",
            "reference_dict": "{dict}",
            "reference_all": "{string} {integer} {float} {boolean} {list} {dict}",
            "reference_to_dict_key": {
                "key": "{dict.key}"
            },
            "reference_to_list": [
                "{string}", "{integer}", "{float}", "{boolean}", "{list}", "{dict}"
            ],
            "reference_to_reference": "{reference_string}",
        }
        resolver = ReferenceResolver(variables)
        expected = {
            "string": "value",
            "integer": 1,
            "float": 1.0,
            "boolean": True,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "reference_string": "value",
            "reference_integer": 1,
            "reference_float": 1.0,
            "reference_boolean": True,
            "reference_list": [1, 2, 3],
            "reference_dict": {"key": "value"},
            "reference_all": "value 1 1.0 True [1, 2, 3] {'key': 'value'}",
            "reference_to_dict_key": {
                "key": "value"
            },
            "reference_to_list": [
                "value", 1, 1.0, True, [1, 2, 3], {"key": "value"}
            ],
            "reference_to_reference": "value",
        }
        assert resolver.resolve() == expected

    @pytest.mark.parametrize("variables", [
        {
            "key1": "{key2}",
            "key2": "{key1}"
        },
        {
            "key1": "{key2}",
            "key2": "{key3}",
            "key3": "{key4}",
            "key4": "{key1}"
        },
    ], ids=[
        "two keys",
        "four keys",
    ])
    def test_resolve_circular_reference(self, variables: Dict[str, BaseType]):
        try:
            ReferenceResolver(variables).resolve()
            assert False
        except ValueError as e:
            assert str(e) == "Circular reference detected for key: key1."
