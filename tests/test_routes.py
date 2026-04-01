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
CustomerProfile API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, CustomerProfileModel
from .factories import CustomerProfileFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)
BASE_URL = "/customerprofiles"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourResourceService(TestCase):
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
        db.session.query(CustomerProfileModel).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_customerprofile(self):
        """It should Create a new CustomerProfile"""
        test_customerprofile = CustomerProfileFactory()
        logging.debug("Test CustomerProfile: %s", test_customerprofile.serialize())
        response = self.client.post(
            BASE_URL,
            json=test_customerprofile.serialize(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_customerprofile = response.get_json()
        self.assertEqual(new_customerprofile["name"], test_customerprofile.name)
        self.assertEqual(new_customerprofile["userid"], test_customerprofile.userid)
        self.assertEqual(new_customerprofile["email"], test_customerprofile.email)
        self.assertEqual(new_customerprofile["address"], test_customerprofile.address)
        self.assertEqual(new_customerprofile["active"], test_customerprofile.active)

    def test_bad_content_type(self):
        """It should return 415 when Content-Type is not application/json"""
        response = self.client.post(
            BASE_URL,
            json={},
            content_type="text/html",
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_no_content_type(self):
        """It should return 415 when no Content-Type is set"""
        response = self.client.post(
            BASE_URL,
            data="bad data",
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_missing_required_name(self):
        """It should return 400 when name is missing"""
        data = CustomerProfileFactory().serialize()
        del data["name"]
        response = self.client.post(
            BASE_URL, json=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_userid(self):
        """It should return 400 when userid is missing"""
        data = CustomerProfileFactory().serialize()
        del data["userid"]
        response = self.client.post(
            BASE_URL, json=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_required_email(self):
        """It should return 400 when email is missing"""
        data = CustomerProfileFactory().serialize()
        del data["email"]
        response = self.client.post(
            BASE_URL, json=data, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_userid(self):
        """It should return 409 when userid already exists"""
        original = CustomerProfileFactory()
        response = self.client.post(
            BASE_URL, json=original.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        duplicate = CustomerProfileFactory().serialize()
        duplicate["userid"] = original.userid
        response = self.client.post(
            BASE_URL, json=duplicate, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_duplicate_email(self):
        """It should return 409 when email already exists"""
        original = CustomerProfileFactory()
        response = self.client.post(
            BASE_URL, json=original.serialize(), content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        duplicate = CustomerProfileFactory().serialize()
        duplicate["email"] = original.email
        response = self.client.post(
            BASE_URL, json=duplicate, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_method_not_allowed(self):
        """It should return 405 when using wrong HTTP method"""
        response = self.client.delete(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_internal_server_error(self):
        """It should return 500 on internal server error"""
        # Trigger a 500 by calling a route that forces an error
        response = self.client.get("/error")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_error_utility(self):
        """It should log and abort with the given status code"""
        from service.routes import error

        with self.assertRaises(Exception):
            error(status.HTTP_400_BAD_REQUEST, "test error message")

    def test_get_customerprofile(self):
        """It should return a Customer Profile by id"""

        # First create a profile
        test_customerprofile = CustomerProfileFactory()
        response = self.client.post(
            BASE_URL,
            json=test_customerprofile.serialize(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_profile = response.get_json()
        customer_id = new_profile["id"]

        # Now retrieve it
        response = self.client.get(f"{BASE_URL}/{customer_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["name"], test_customerprofile.name)
        self.assertEqual(data["userid"], test_customerprofile.userid)
        self.assertEqual(data["email"], test_customerprofile.email)
        self.assertEqual(data["address"], test_customerprofile.address)
        self.assertEqual(data["active"], test_customerprofile.active)

    def test_get_customerprofile_not_found(self):
        """It should return 404 when Customer Profile is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("not found", data["message"].lower())

    def test_delete_customerprofile(self):
        """It should Delete a Customer Profile"""
        # First create a profile
        test_customerprofile = CustomerProfileFactory()
        response = self.client.post(
            BASE_URL,
            json=test_customerprofile.serialize(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        customer_id = response.get_json()["id"]

        # Now delete it
        response = self.client.delete(f"{BASE_URL}/{customer_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify it's gone
        response = self.client.get(f"{BASE_URL}/{customer_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_customerprofile_not_found(self):
        """It should return 404 when deleting a Customer Profile that does not exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.get_json()
        self.assertIn("not found", data["message"].lower())

    def test_activate_customerprofile(self):
        """It should Activate a Customer Profile"""
        # First create an inactive customer
        test_customerprofile = CustomerProfileFactory(active=False)
        response = self.client.post(
            BASE_URL,
            json=test_customerprofile.serialize(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        customer_id = response.get_json()["id"]

        # Now activate it
        response = self.client.put(f"{BASE_URL}/{customer_id}/activate")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data["active"], True)

    def test_activate_customerprofile_not_found(self):
        """It should return 404 when activating a Customer Profile that does not exist"""
        response = self.client.put(f"{BASE_URL}/0/activate")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
