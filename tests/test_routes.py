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
from datetime import datetime, timedelta
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Customer, IdempotencyKey
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
        db.session.query(IdempotencyKey).delete()  # clean up idempotency keys
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

    ######################################################################
    #  I D E M P O T E N C Y   T E S T S
    ######################################################################

    def test_create_customer_with_idempotency_key(self):
        """It should create a customer normally when an Idempotency-Key is provided"""
        payload = {
            "name": "Idem",
            "userid": "idem1",
            "email": "idem1@example.com",
            "address": "100 Key St",
        }
        resp = self.client.post(
            "/customers",
            json=payload,
            headers={"Idempotency-Key": "key-happy-path"},
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        self.assertEqual(data["name"], "Idem")
        self.assertEqual(data["userid"], "idem1")

    def test_create_customer_idempotent_replay(self):
        """It should return the same response when the same key+payload is sent twice"""
        payload = {
            "name": "Replay",
            "userid": "replay1",
            "email": "replay1@example.com",
            "address": "200 Retry Rd",
        }
        headers = {"Idempotency-Key": "key-replay"}

        # First request — creates the customer
        resp1 = self.client.post("/customers", json=payload, headers=headers)
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        data1 = resp1.get_json()

        # Second request — same key, same payload (a retry)
        resp2 = self.client.post("/customers", json=payload, headers=headers)
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        data2 = resp2.get_json()

        # Should get back the SAME customer id (no duplicate created)
        self.assertEqual(data1["id"], data2["id"])
        self.assertEqual(data1["name"], data2["name"])

        # Verify only ONE customer exists in the database
        all_customers = self.client.get("/customers")
        self.assertEqual(len(all_customers.get_json()), 1)

    def test_create_customer_same_key_different_payload(self):
        """It should return 409 Conflict when the same key is reused with different data"""
        headers = {"Idempotency-Key": "key-conflict"}

        # First request
        payload1 = {
            "name": "Original",
            "userid": "conflict1",
            "email": "conflict1@example.com",
        }
        resp1 = self.client.post("/customers", json=payload1, headers=headers)
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)

        # Second request — same key but DIFFERENT data
        payload2 = {
            "name": "Sneaky Different",
            "userid": "conflict2",
            "email": "conflict2@example.com",
        }
        resp2 = self.client.post("/customers", json=payload2, headers=headers)
        self.assertEqual(resp2.status_code, status.HTTP_409_CONFLICT)

    def test_create_customer_without_idempotency_key(self):
        """It should still work normally when no Idempotency-Key header is sent"""
        payload = {
            "name": "NoKey",
            "userid": "nokey1",
            "email": "nokey1@example.com",
        }
        # No Idempotency-Key header — should work exactly as before
        resp = self.client.post("/customers", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.get_json()
        self.assertEqual(data["name"], "NoKey")

    def test_create_customer_idempotency_key_expired(self):
        """It should treat an expired key as a new request"""
        payload = {
            "name": "Expired",
            "userid": "expired1",
            "email": "expired1@example.com",
        }
        headers = {"Idempotency-Key": "key-expired"}

        # First request — creates the customer
        resp1 = self.client.post("/customers", json=payload, headers=headers)
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        data1 = resp1.get_json()

        # Manually age the idempotency key to 25 hours ago (past the 24h window)
        idem_record = IdempotencyKey.query.filter_by(key="key-expired").first()
        idem_record.created_at = datetime.utcnow() - timedelta(hours=25)
        db.session.commit()

        # Send again with a new userid/email (since old customer still exists
        # with the unique userid, we use different values to avoid DB conflict)
        payload2 = {
            "name": "Expired",
            "userid": "expired2",
            "email": "expired2@example.com",
        }
        resp2 = self.client.post("/customers", json=payload2, headers=headers)
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        data2 = resp2.get_json()

        # Should be a DIFFERENT customer (new ID) since the key expired
        self.assertNotEqual(data1["id"], data2["id"])

