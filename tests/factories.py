"""
Test Factory to make fake objects for testing
"""

import factory
from factory import Faker
from service.models import CustomerProfileModel


class CustomerProfileFactory(factory.Factory):
    """Creates fake Customer Profiles for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = CustomerProfileModel

    id = factory.Sequence(lambda n: n)
    name = Faker("name")
    userid = factory.Sequence(lambda n: f"user{n}")  # sequence ensures uniqueness
    email = factory.LazyAttribute(
        lambda o: f"{o.userid}@example.com"
    )  # ensures uniqueness
    address = Faker("address")
    active = True
    product_attributes = None
    assigned_csm = None
    arr_value = None
