"""
Test Factory to make fake objects for testing
"""

import factory
from service.models import Customer


class CustomerFactory(factory.Factory):
    """Creates fake customers for testing"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Customer

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("first_name")
    userid = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.userid}@example.com")
    address = factory.Faker("address")
    active = True
    product_attributes = factory.LazyFunction(lambda: "{}")
    assigned_csm = factory.Faker("name")
    arr_value = factory.LazyFunction(lambda: 0.0)

