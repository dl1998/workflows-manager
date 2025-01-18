"""
Module to resolve references in a dictionary.
"""
import re
from typing import Union, Optional, List, Dict, Any, Iterator, ItemsView, Tuple

BaseType = Union[int, float, bool, str, list, dict]

CLEANUP_REGEX_PATTERN = re.compile(r'(?<!{)(?:{{)*(?P<captured>{\s*(?P<variable>[a-zA-Z][\w\\.]*)\s*})(?:}})*(?!})')


def get_variable(variables: Dict[str, BaseType], key_path: str, default: Any = None) -> BaseType:
    """
    Get variable from dictionary by key.

    :param variables: The dictionary to search for the key.
    :type variables: Dict[str, BASE_TYPE]
    :param key_path: The key path to search for in the dictionary. The key path is a string with keys separated by dots.
    :type key_path: str
    :param default: The default value to return if the key is not found.
    :type default: Any
    :return: The value of the key in the dictionary or the default value if the key is not found.
    :rtype: BASE_TYPE
    """
    path = key_path.split('.')
    value = variables
    for key in path:
        value = value.get(key, None)
        if value is None:
            break
    if value is None:
        value = default
    return value


class ReferenceResolver:
    """
    Class to resolve references in a dictionary.

    :param variables: The dictionary to resolve the references in.
    :type variables: Dict[str, BASE_TYPE]
    """

    def __init__(self, variables: Dict[str, BaseType]):
        self.__variables = variables

    def __substitute_placeholder(self, match: re.Match, value: str) -> BaseType:
        """
        Substitute a placeholder in a string.

        :param match: The match object from the regular expression.
        :type match: re.Match
        :param value: The value to substitute the placeholder in.
        :type value: str
        :return: The value with the placeholder substituted.
        :rtype: BASE_TYPE
        """
        variable_name = match.group("variable")
        captured = match.group("captured")
        if value == captured:
            return get_variable(self.__variables, variable_name, captured)
        return value.replace(captured, str(get_variable(self.__variables, variable_name, captured)))

    def __substitute_value(self, value: str, key: Optional[str] = None) -> Optional[BaseType]:
        """
        Substitute a value in a string.

        :param value: The value to substitute.
        :type value: str
        :param key: The key to check for circular references.
        :type key: Optional[str]
        :return: The value with the placeholder substituted.
        :rtype: Optional[BASE_TYPE]
        """
        if not isinstance(value, str):
            return value
        placeholder = CLEANUP_REGEX_PATTERN.search(value)
        if placeholder:
            if key is not None and isinstance(self.__variables, dict) and placeholder.group('variable') == key:
                raise ValueError(f'Circular reference detected for key: {key}.')
            return self.__substitute_placeholder(placeholder, value)
        return value

    @staticmethod
    def __get_elements(container: Union[Dict[str, BaseType], List[BaseType]]
                       ) -> Union[ItemsView[str, BaseType], Iterator[Tuple[int, BaseType]]]:
        """
        Get the elements of a container.

        :param container: The container to get the elements of. Can be a dictionary or a list.
        :type container: Union[Dict[str, BASE_TYPE], List[BASE_TYPE]]
        :return: The elements of the container.
        :rtype: Union[ItemsView[str, BASE_TYPE], Iterator[Tuple[int, BASE_TYPE]]]
        """
        if isinstance(container, dict):
            return container.items()
        return enumerate(container)

    def __resolve_element(self, element: BaseType, key: Optional[str] = None) -> BaseType:
        """
        Resolve an element in a dictionary.

        :param element: The element to resolve.
        :type element: BASE_TYPE
        :param key: The key to check for circular references.
        :type key: Optional[str]
        :return: The resolved element.
        :rtype: BASE_TYPE
        """
        while True:
            substitute = self.__substitute_value(element, key)
            if element == substitute:
                break
            element = substitute
        if not isinstance(element, str):
            return element
        return element.replace('{{', '{').replace('}}', '}')

    def resolve_element(self, element: BaseType) -> BaseType:
        """
        Resolve an element in a dictionary.

        :param element: The element to resolve.
        :type element: BASE_TYPE
        :return: The resolved element.
        :rtype: BASE_TYPE
        """
        return self.__resolve_element(element)

    def __resolve_elements(self, elements: Union[Dict[str, BaseType], List[BaseType]]):
        """
        Resolve the elements in a dictionary.

        :param elements: The elements to resolve.
        :type elements: Union[Dict[str, BASE_TYPE], List[BASE_TYPE]]
        """
        for key_or_index, value in self.__get_elements(elements):
            if isinstance(value, (dict, list)):
                self.__resolve_elements(value)
                continue
            if not isinstance(value, str):
                continue
            key = key_or_index if isinstance(elements, dict) else None
            value = self.__resolve_element(value, key)
            elements[key_or_index] = value

    def resolve(self) -> Dict[str, BaseType]:
        """
        Resolve the references in the dictionary.

        :return: The dictionary with the references resolved.
        :rtype: Dict[str, BASE_TYPE]
        """
        self.__resolve_elements(self.__variables)
        return self.__variables
