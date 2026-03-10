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
Test cases for CustomerProfileModel Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.models import db, CustomerProfileModel, DataValidationError
from .factories import CustomerProfileFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  C U S T O M E R P R O F I L E   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestCustomerProfileModel(TestCase):
    """Test Cases for CustomerProfileModel"""

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
        db.session.query(CustomerProfileModel).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_customer_profile(self):
        """It should Create a customer profile"""
        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            address="123 Main St",
            active=True,
        )
        self.assertEqual(str(profile), "<CustomerProfileModel Jane Doe id=[None]>")
        self.assertTrue(profile is not None)
        self.assertEqual(profile.id, None)
        self.assertEqual(profile.name, "Jane Doe")
        self.assertEqual(profile.userid, "janedoe123")
        self.assertEqual(profile.email, "jane@example.com")
        self.assertEqual(profile.address, "123 Main St")
        self.assertEqual(profile.active, True)

        # Test with optional fields omitted and active defaulting to True
        profile2 = CustomerProfileModel(
            name="John Smith",
            userid="johnsmith456",
            email="john@example.com",
            active=True,  # set explicitly since SQLAlchemy defaults only apply at DB level
        )
        self.assertEqual(profile2.address, None)
        self.assertEqual(profile2.active, True)
        self.assertEqual(profile2.product_attributes, None)
        self.assertEqual(profile2.assigned_csm, None)
        self.assertEqual(profile2.arr_value, None)

    def test_update_a_customer_profile(self):
        """It should Update a customer profile"""
        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            active=True,
        )
        profile.create()
        self.assertIsNotNone(profile.id)
        profile.name = "Jane Smith"
        profile.update()
        updated = CustomerProfileModel.find(profile.id)
        self.assertEqual(updated.name, "Jane Smith")

    def test_delete_a_customer_profile(self):
        """It should Delete a customer profile"""
        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            active=True,
        )
        profile.create()
        self.assertIsNotNone(profile.id)
        profile.delete()
        deleted = CustomerProfileModel.find(profile.id)
        self.assertIsNone(deleted)

    def test_list_all_customer_profiles(self):
        """It should List all customer profiles"""
        profiles = CustomerProfileModel.all()
        self.assertEqual(profiles, [])
        for _ in range(5):
            profile = CustomerProfileFactory()
            profile.id = None
            profile.create()
        profiles = CustomerProfileModel.all()
        self.assertEqual(len(profiles), 5)

    def test_find_by_name(self):
        """It should Find a customer profile by name"""
        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            active=True,
        )
        profile.create()
        results = CustomerProfileModel.find_by_name("Jane Doe")
        self.assertEqual(results.count(), 1)
        self.assertEqual(results[0].userid, "janedoe123")

    def test_deserialize_missing_name(self):
        """It should raise DataValidationError when name is missing"""
        profile = CustomerProfileModel()
        self.assertRaises(
            DataValidationError,
            profile.deserialize,
            {"userid": "test123", "email": "test@example.com"},
        )

    def test_deserialize_missing_userid(self):
        """It should raise DataValidationError when userid is missing"""
        profile = CustomerProfileModel()
        self.assertRaises(
            DataValidationError,
            profile.deserialize,
            {"name": "Test User", "email": "test@example.com"},
        )

    def test_deserialize_missing_email(self):
        """It should raise DataValidationError when email is missing"""
        profile = CustomerProfileModel()
        self.assertRaises(
            DataValidationError,
            profile.deserialize,
            {"name": "Test User", "userid": "test123"},
        )

    def test_deserialize_bad_data(self):
        """It should raise DataValidationError when data is not a dict"""
        profile = CustomerProfileModel()
        self.assertRaises(
            DataValidationError,
            profile.deserialize,
            "this is not a dict",
        )

    def test_find_by_name_not_found(self):
        """It should return empty list when name not found"""
        results = CustomerProfileModel.find_by_name("Nobody")
        self.assertEqual(results.count(), 0)

    def test_update_error(self):
        """It should raise DataValidationError on update failure"""
        from unittest.mock import patch

        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            active=True,
        )
        profile.create()
        with patch(
            "service.models.db.session.commit", side_effect=Exception("commit error")
        ):
            self.assertRaises(DataValidationError, profile.update)

    def test_delete_error(self):
        """It should raise DataValidationError on delete failure"""
        from unittest.mock import patch

        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            active=True,
        )
        profile.create()
        with patch(
            "service.models.db.session.commit", side_effect=Exception("commit error")
        ):
            self.assertRaises(DataValidationError, profile.delete)

    def test_create_error(self):
        """It should raise DataValidationError on create failure"""
        from unittest.mock import patch

        profile = CustomerProfileModel(
            name="Jane Doe",
            userid="janedoe123",
            email="jane@example.com",
            active=True,
        )
        with patch(
            "service.models.db.session.commit", side_effect=Exception("commit error")
        ):
            self.assertRaises(DataValidationError, profile.create)
