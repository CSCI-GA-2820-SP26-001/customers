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
TestCustomer API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Customer
from .factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomerService(TestCase):
    """REST API Server Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
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
        db.session.query(Customer).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should return service metadata on the root URL"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "Customers Service")
        self.assertEqual(data["version"], "1.0")
        self.assertEqual(data["customers_url"], "/customers")

    def test_create_customer(self):
        payload = {
            "name": "Alice",
            "userid": "alice1",
            "email": "alice1@example.com",
            "address": "1 Main St",
        }
        resp = self.client.post("/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        self.assertEqual(data["name"], "Alice")
        self.assertEqual(data["userid"], "alice1")

    def test_list_customers(self):
        CustomerFactory().create()
        CustomerFactory().create()

        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 2)

    def test_get_customer(self):
        customer = CustomerFactory()
        customer.create()

        resp = self.client.get(f"/customers/{customer.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], customer.id)

    def test_update_customer(self):
        customer = CustomerFactory()
        customer.create()
        payload = {
            "name": "Bob",
            "userid": customer.userid,
            "email": customer.email,
            "address": "99 Lane",
        }

        resp = self.client.put(f"/customers/{customer.id}", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        updated = Customer.find(customer.id)
        self.assertEqual(updated.name, "Bob")

    def test_delete_customer(self):
        customer = CustomerFactory()
        customer.create()

        resp = self.client.delete(f"/customers/{customer.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIsNone(Customer.find(customer.id))

    def test_update_customer_not_found(self):
        resp = self.client.put(
            "/customers/99999",
            json={"name":"NotThere","userid":"x","email":"x@example.com"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_customer_not_found(self):
        resp = self.client.get("/customers/99999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_content_type(self):
        resp = self.client.post("/customers", data="{}", content_type="text/plain")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_no_content_type(self):
        resp = self.client.post("/customers", data='{"name":"NoCT"}')
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_customer_missing_fields(self):
        resp = self.client.post("/customers", json={"name": "NoUser"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        resp = self.client.post("/customers/1", json={})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_internal_server_error(self):
        resp = self.client.get("/error")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["error"], "Internal Server Error")

