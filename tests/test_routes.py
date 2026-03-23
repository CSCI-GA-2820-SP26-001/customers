######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Customer API Service Test Suite
"""
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.common import status
from service.models import db, Customer, DataValidationError
from service.common.error_handlers import bad_request

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
class TestCustomerService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Customer).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_customers(self):
        """It should return all customers as a JSON array with 200 OK"""
        customer1 = Customer(first_name="John", last_name="Doe", address="123 Main St")
        customer2 = Customer(
            first_name="Jane", last_name="Smith", address="456 Oak Ave"
        )
        customer3 = Customer(first_name="Bob", last_name="Jones", address="789 Pine Rd")
        customer1.create()
        customer2.create()
        customer3.create()

        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

    def test_list_customers_empty(self):
        """It should return an empty JSON array when no customers exist"""
        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_404_not_found(self):
        """It should return 404 for unknown routes"""
        resp = self.client.get("/unknown-route")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        data = resp.get_json()
        self.assertIn("status", data)

    def test_405_method_not_allowed(self):
        """It should return 405 when method is not allowed"""
        resp = self.client.delete("/customers")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        data = resp.get_json()
        self.assertIn("status", data)

    def test_400_bad_request(self):
        """It should return 400 for bad request"""
        with app.test_request_context():
            response = bad_request(DataValidationError("bad data"))
            self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)

    def test_request_validation_error(self):
        """It should handle DataValidationError and return 400"""
        with app.test_request_context():
            from service.common.error_handlers import request_validation_error

            response = request_validation_error(DataValidationError("invalid"))
            self.assertEqual(response[1], status.HTTP_400_BAD_REQUEST)

    def test_415_unsupported_media_type(self):
        """It should return 415 for unsupported media type"""
        with app.test_request_context():
            from service.common.error_handlers import mediatype_not_supported

            response = mediatype_not_supported(Exception("unsupported"))
            self.assertEqual(response[1], status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_500_internal_server_error(self):
        """It should return 500 for internal server error"""
        with app.test_request_context():
            from service.common.error_handlers import internal_server_error

            response = internal_server_error(Exception("server error"))
            self.assertEqual(response[1], status.HTTP_500_INTERNAL_SERVER_ERROR)
