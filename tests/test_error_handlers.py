######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
######################################################################
"""Tests for service.common.error_handlers helpers."""

from unittest import TestCase

from service.common.error_handlers import bad_request, _api_error_message
from service.models import DataValidationError
from wsgi import app


class _ErrWithDesc:
    def __init__(self, description):
        self.description = description

    def __str__(self):
        return "SHOULD_NOT_USE_WHEN_DESC_OK"


class _ErrFallback:
    """description not usable; str(self) used."""

    def __init__(self, description):
        self.description = description

    def __str__(self):
        return "fallback message"


class TestBadRequestHandler(TestCase):
    """bad_request branch when error is DataValidationError."""

    def test_bad_request_uses_str_for_data_validation_error(self):
        """It should use str(error) for DataValidationError (not Werkzeug description)."""
        with app.app_context():
            response, status_code = bad_request(
                DataValidationError("missing required field")
            )
        self.assertEqual(status_code, 400)
        data = response.get_json()
        self.assertEqual(data["message"], "missing required field")


class TestApiErrorMessage(TestCase):
    """Unit tests for _api_error_message."""

    def test_prefers_non_empty_string_description(self):
        """It should strip and return a string description from the error."""
        err = _ErrWithDesc("  Customer not found  ")
        self.assertEqual(_api_error_message(err), "Customer not found")

    def test_falls_back_when_description_blank(self):
        """It should use str(error) when description is only whitespace."""
        err = _ErrFallback("   ")
        self.assertEqual(_api_error_message(err), "fallback message")

    def test_falls_back_when_description_not_string(self):
        """It should use str(error) when description is not a str."""
        err = _ErrFallback(404)
        self.assertEqual(_api_error_message(err), "fallback message")
