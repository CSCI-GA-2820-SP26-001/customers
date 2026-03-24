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
Test cases for Pet Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import Customer, db, DataValidationError
from .factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  Customer   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomerModel(TestCase):
    """Test Cases for Customer Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Customer).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_example_replace_this(self):
        """It should create a Customer"""
        resource = CustomerFactory()
        resource.create()
        self.assertIsNotNone(resource.id)
        found = Customer.all()
        self.assertEqual(len(found), 1)
        data = Customer.find(resource.id)
        self.assertEqual(data.name, resource.name)

    def test_update_customer(self):
        resource = CustomerFactory()
        resource.create()
        resource.name = "Updated Name"
        resource.update()

        updated = Customer.find(resource.id)
        self.assertEqual(updated.name, "Updated Name")

    def test_delete_customer(self):
        resource = CustomerFactory()
        resource.create()
        resource_id = resource.id

        resource.delete()
        self.assertIsNone(Customer.find(resource_id))

    def test_find_by_userid(self):
        resource = CustomerFactory()
        resource.create()

        found = Customer.find_by_userid(resource.userid)
        self.assertIsNotNone(found)
        self.assertEqual(found.email, resource.email)

    def test_serialize_deserialize(self):
        resource = CustomerFactory()
        data = resource.serialize()
        new_cust = Customer()
        new_cust.deserialize(data)
        self.assertEqual(new_cust.name, resource.name)
        self.assertEqual(new_cust.userid, resource.userid)

    def test_duplicate_userid_raises(self):
        resource1 = CustomerFactory()
        resource1.create()
        resource2 = CustomerFactory(userid=resource1.userid, email='dup@example.com')

        with self.assertRaises(Exception):
            resource2.create()

    def test_update_raises_data_validation_error(self):
        resource = CustomerFactory()
        resource.create()
        resource.name = "new"

        with patch("service.models.db.session.commit", side_effect=Exception("fail")):
            with self.assertRaises(DataValidationError):
                resource.update()

    def test_delete_raises_data_validation_error(self):
        resource = CustomerFactory()
        resource.create()

        with patch("service.models.db.session.commit", side_effect=Exception("fail")):
            with self.assertRaises(DataValidationError):
                resource.delete()

    def test_deserialize_missing_required_fields(self):
        customer = Customer()
        with self.assertRaises(DataValidationError):
            customer.deserialize({"name": "Jeffrey"})

    def test_create_missing_required_fields(self):
        resource = Customer(name="Jeffrey")
        with self.assertRaises(Exception):
            resource.create()  # missing userid and email triggers DataValidationError or DB error

