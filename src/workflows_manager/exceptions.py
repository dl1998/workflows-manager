"""
This module contains custom exceptions.
"""

class InvalidConfiguration(Exception):
    """
    Exception raised when configuration is invalid.
    """


class MissingParameter(InvalidConfiguration):
    """
    Exception raised when parameter is missing.
    """


class InvalidParameter(InvalidConfiguration):
    """
    Exception raised when parameter is invalid.
    """


class MissingStep(Exception):
    """
    Exception raised when step from configuration is not registered.
    """

class UnknownOption(Exception):
    """
    Exception raised when unknown option is passed.
    """
