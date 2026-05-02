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

    def test_health(self):
        """It should return JSON health status for probes"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.content_type, "application/json")
        data = resp.get_json()
        self.assertEqual(data, {"status": "OK"})

    def test_admin_ui_page(self):
        """It should serve the HTML admin console for managers"""
        resp = self.client.get("/admin")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", resp.content_type)
        html = resp.data.decode()
        self.assertIn("Customers Admin", html)
        self.assertIn('id="btn-execute"', html)
        self.assertIn('id="admin-operation"', html)
        self.assertIn('id="admin-page"', html)
        self.assertIn('id="admin-customers-table"', html)

    def test_create_customer(self):
        """It should Create a new Customer"""
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
        """It should List all Customers"""
        CustomerFactory().create()
        CustomerFactory().create()

        resp = self.client.get("/customers")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 2)

    def test_get_customer(self):
        """It should Get a Customer by id"""
        customer = CustomerFactory()
        customer.create()

        resp = self.client.get(f"/customers/{customer.id}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["id"], customer.id)

    def test_update_customer(self):
        """It should Update a Customer"""
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
        """It should Delete a Customer"""
        customer = CustomerFactory()
        customer.create()

        resp = self.client.delete(f"/customers/{customer.id}")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        self.assertIsNone(Customer.find(customer.id))

    def test_delete_customer_not_found(self):
        """It should return 404 when deleting a Customer that does not exist"""
        resp = self.client.delete("/customers/99999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_customer_not_found(self):
        """It should return 404 when updating a Customer that does not exist"""
        resp = self.client.put(
            "/customers/99999",
            json={"name": "NotThere", "userid": "x", "email": "x@example.com"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_customer_not_found(self):
        """It should return 404 when Customer is not found"""
        resp = self.client.get("/customers/99999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_content_type(self):
        """It should return 415 when Content-Type is wrong"""
        resp = self.client.post("/customers", data="{}", content_type="text/plain")
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_no_content_type(self):
        """It should return 415 when no Content-Type is set"""
        resp = self.client.post("/customers", data='{"name":"NoCT"}')
        self.assertEqual(resp.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_customer_missing_fields(self):
        """It should return 400 when required fields are missing"""
        resp = self.client.post("/customers", json={"name": "NoUser"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_method_not_allowed(self):
        """It should return 405 when using wrong HTTP method"""
        resp = self.client.post("/customers/1", json={})
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_internal_server_error(self):
        """It should return 500 on internal server error"""
        resp = self.client.get("/error")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = resp.get_json()
        self.assertEqual(data["error"], "Internal Server Error")

    def test_activate_customer(self):
        """It should Activate a Customer"""
        customer = CustomerFactory(active=False)
        customer.create()

        resp = self.client.put(f"/customers/{customer.id}/activate")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(data["active"], True)

    def test_activate_customer_not_found(self):
        """It should return 404 when activating a Customer that does not exist"""
        resp = self.client.put("/customers/99999/activate")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_customers_by_name(self):
        """It should return customers filtered by name"""
        customer1 = CustomerFactory(name="Alice")
        customer2 = CustomerFactory(name="Bob")
        customer1.create()
        customer2.create()

        resp = self.client.get("/customers?name=Alice")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Alice")

    def test_query_customers_by_name_case_insensitive(self):
        """It should return customers filtered by name case-insensitively"""
        customer = CustomerFactory(name="Alice")
        customer.create()

        resp = self.client.get("/customers?name=alice")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 1)

    def test_query_customers_by_name_no_match(self):
        """It should return empty list when no customers match"""
        customer = CustomerFactory(name="Alice")
        customer.create()

        resp = self.client.get("/customers?name=NoMatch")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.get_json()
        self.assertEqual(len(data), 0)
