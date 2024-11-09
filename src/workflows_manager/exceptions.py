"""
This module contains custom exceptions.
"""

class InvalidConfiguration(Exception):
    """
    Exception raised when configuration is invalid.
    """
    pass


class MissingParameter(InvalidConfiguration):
    """
    Exception raised when parameter is missing.
    """
    pass


class MissingStep(Exception):
    """
    Exception raised when step from configuration is not registered.
    """
    pass

class UnknownOption(Exception):
    """
    Exception raised when unknown option is passed.
    """
    pass
