"""
Test Factory to make fake objects for testing
"""

import factory
from factory import Faker
from factory.fuzzy import FuzzyChoice
from service.models import CustomerProfileModel


class CustomerFactory(factory.Factory):
    """Creates fake customers for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Customer

    id = factory.Sequence(lambda n: n)
    name = Faker("name")
    userid = factory.Sequence(lambda n: f"user{n}")  # sequence ensures uniqueness
    email = factory.LazyAttribute(
        lambda o: f"{o.userid}@example.com"
    )  # ensures uniqueness
    address = Faker("address")
    active = FuzzyChoice(choices=[True, False])
    product_attributes = None
    assigned_csm = None
    arr_value = None
