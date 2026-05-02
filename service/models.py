"""
Models for Customer

All of the models are stored in this module
"""

import logging
import re

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


def _friendly_integrity_message(exc: IntegrityError) -> str:
    """Turn a DB unique/constraint error into a short API message."""
    raw = " ".join(
        part
        for part in (
            str(exc.orig) if getattr(exc, "orig", None) else "",
            str(exc),
        )
        if part
    ).lower()
    if re.search(r"\b(userid|user_id|ix_customer_userid)\b", raw) or (
        "userid" in raw and "unique" in raw
    ):
        return "A customer with this user id already exists."
    if re.search(r"\b(email|ix_customer_email)\b", raw) or (
        "email" in raw and ("unique" in raw or "duplicate" in raw)
    ):
        return "A customer with this email already exists."
    if "unique" in raw or "duplicate key" in raw:
        return "A customer with this user id or email already exists."
    return "Could not save the customer (database constraint)."


class Customer(db.Model):  # pylint: disable=too-many-instance-attributes
    """
    Class that represents a Customer
    """

    ##################################################
    # Table Schema
    ##################################################
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(63), nullable=False)
    userid = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    address = db.Column(db.String(256), nullable=True)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    product_attributes = db.Column(db.String(256), nullable=True)
    assigned_csm = db.Column(db.String(128), nullable=True)
    arr_value = db.Column(db.Float(), nullable=True)

    def __repr__(self):
        return f"<Customer {self.name} id=[{self.id}]>"

    def create(self):
        """
        Creates a Customer to the database
        """
        logger.info("Creating %s", self.name)
        self.id = None  # pylint: disable=invalid-name
        try:
            db.session.add(self)
            db.session.commit()
            db.session.refresh(self)
        except IntegrityError as err:
            db.session.rollback()
            logger.error("Integrity error creating record: %s", self)
            raise DataValidationError(_friendly_integrity_message(err)) from err
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self, exc_info=True)
            msg = str(e)
            if len(msg) > 200:
                msg = "Could not create the customer. See server logs for details."
            raise DataValidationError(msg) from e

    def update(self):
        """
        Updates a Customer to the database
        """
        logger.info("Saving %s", self.name)
        try:
            db.session.commit()
        except IntegrityError as err:
            db.session.rollback()
            logger.error("Integrity error updating record: %s", self)
            raise DataValidationError(_friendly_integrity_message(err)) from err
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self, exc_info=True)
            msg = str(e)
            if len(msg) > 200:
                msg = "Could not update the customer. See server logs for details."
            raise DataValidationError(msg) from e

    def delete(self):
        """Removes a Customer from the data store"""
        logger.info("Deleting %s", self.name)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Customer into a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "userid": self.userid,
            "email": self.email,
            "address": self.address,
            "active": self.active,
            "product_attributes": self.product_attributes,
            "assigned_csm": self.assigned_csm,
            "arr_value": self.arr_value,
        }

    def deserialize(self, data):
        """Deserializes a Customer from a dictionary"""
        try:
            self.name = data["name"]
            self.userid = data["userid"]
            self.email = data["email"]

            # optionals
            self.address = data.get("address")
            self.active = data.get("active", True)
            self.product_attributes = data.get("product_attributes")
            self.assigned_csm = data.get("assigned_csm")
            self.arr_value = data.get("arr_value")

        except AttributeError as error:
            raise DataValidationError("Invalid attribute: " + error.args[0]) from error
        except KeyError as error:
            raise DataValidationError(
                "Invalid Customer: missing " + error.args[0]
            ) from error
        except TypeError as error:
            raise DataValidationError(
                "Invalid Customer: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Customers in the database"""
        logger.info("Processing all Customers")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Customer by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_name(cls, name):
        """Returns all Customers with the given name

        Args:
            name (string): the name of the Customers you want to match
        """
        logger.info("Processing name query for %s ...", name)
        return cls.query.filter(cls.name.ilike(name))

    @classmethod
    def find_by_userid(cls, userid):
        """Returns a Customer with the given userid"""
        logger.info("Processing userid query for %s ...", userid)
        return cls.query.filter(cls.userid == userid).one_or_none()
