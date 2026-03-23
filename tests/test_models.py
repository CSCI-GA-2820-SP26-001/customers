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
Test cases for Customer Model
"""
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from wsgi import app
from service.models import Customer, DataValidationError, db
from tests.factories import CustomerFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  C U S T O M E R   M O D E L   T E S T   C A S E S
######################################################################
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
        db.session.query(Customer).delete()
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_customer(self):
        """It should create a Customer"""
        customer = CustomerFactory()
        customer.create()
        self.assertIsNotNone(customer.id)
        found = Customer.all()
        self.assertEqual(len(found), 1)
        data = Customer.find(customer.id)
        self.assertEqual(data.first_name, customer.first_name)
        self.assertEqual(data.last_name, customer.last_name)

    def test_update_customer(self):
        """It should update a Customer"""
        customer = CustomerFactory()
        customer.create()
        customer.first_name = "Updated"
        customer.update()
        found = Customer.find(customer.id)
        self.assertEqual(found.first_name, "Updated")

    def test_delete_customer(self):
        """It should delete a Customer"""
        customer = CustomerFactory()
        customer.create()
        customer.delete()
        found = Customer.all()
        self.assertEqual(len(found), 0)

    def test_serialize_customer(self):
        """It should serialize a Customer"""
        customer = CustomerFactory()
        data = customer.serialize()
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)
        self.assertIn("address", data)

    def test_deserialize_customer(self):
        """It should deserialize a Customer"""
        data = {"first_name": "John", "last_name": "Doe", "address": "123 Main St"}
        customer = Customer()
        customer.deserialize(data)
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.last_name, "Doe")

    def test_deserialize_missing_first_name(self):
        """It should raise DataValidationError if first_name is missing"""
        customer = Customer()
        with self.assertRaises(DataValidationError):
            customer.deserialize({"last_name": "Doe"})

    def test_deserialize_missing_last_name(self):
        """It should raise DataValidationError if last_name is missing"""
        customer = Customer()
        with self.assertRaises(DataValidationError):
            customer.deserialize({"first_name": "John"})

    def test_deserialize_bad_data_type(self):
        """It should raise DataValidationError on bad data type"""
        customer = Customer()
        with self.assertRaises(DataValidationError):
            customer.deserialize("not a dict")

    def test_repr(self):
        """It should return a string representation"""
        customer = Customer(first_name="John", last_name="Doe")
        self.assertIn("John", str(customer))

    def test_create_db_error(self):
        """It should raise DataValidationError on create db error"""
        customer = CustomerFactory()
        with patch(
            "service.models.db.session.commit", side_effect=Exception("db error")
        ):
            with self.assertRaises(DataValidationError):
                customer.create()

    def test_update_db_error(self):
        """It should raise DataValidationError on update db error"""
        customer = CustomerFactory()
        customer.create()
        with patch(
            "service.models.db.session.commit", side_effect=Exception("db error")
        ):
            with self.assertRaises(DataValidationError):
                customer.update()

    def test_delete_db_error(self):
        """It should raise DataValidationError on delete db error"""
        customer = CustomerFactory()
        customer.create()
        with patch(
            "service.models.db.session.delete", side_effect=Exception("db error")
        ):
            with self.assertRaises(DataValidationError):
                customer.delete()
