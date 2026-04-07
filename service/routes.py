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
Customer Service

This service implements a REST API that allows you to Create, Read, Update
and Delete Customer
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import Customer
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    app.logger.info("Request for root URL received.")

    response = {
        "name": "Customers Service",
        "version": "1.0",
        "customers_url": "/customers",
    }

    return jsonify(response), status.HTTP_200_OK


######################################################################
# HEALTH
######################################################################
@app.route("/health")
def health():
    """Health check for monitors (e.g. Kubernetes liveness/readiness)"""
    app.logger.info("Health check requested")
    return jsonify({"status": "OK"}), status.HTTP_200_OK


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


def check_content_type(expected: str) -> None:
    """Checks that the request Content-Type matches what the API expects."""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            description=f"Content-Type must be {expected}",
        )
    if request.headers["Content-Type"] != expected:
        app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            description=f"Content-Type must be {expected}",
        )


######################################################################
# CREATE A NEW CUSTOMER
######################################################################
@app.route("/customers", methods=["POST"])
def create_customer():
    """Create a new Customer"""
    app.logger.info("Request to create a customer")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.debug("Received data: %s", data)

    try:
        customer = Customer()
        customer.deserialize(data)
        customer.create()
        app.logger.info("Created customer with id: %s", customer.id)
        return (
            jsonify(customer.serialize()),
            status.HTTP_201_CREATED,
            {
                "Location": url_for(
                    "get_customer", customer_id=customer.id, _external=True
                )
            },
        )
    except Exception as e:
        app.logger.error("Error creating customer: %s", str(e))
        abort(status.HTTP_400_BAD_REQUEST, description=str(e))


######################################################################
# READ A CUSTOMER
######################################################################
@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    """Get a Customer by id"""
    app.logger.info("Request to get customer with id: %s", customer_id)
    customer = Customer.find(customer_id)
    if not customer:
        app.logger.warning("Customer with id: %s not found", customer_id)
        abort(status.HTTP_404_NOT_FOUND, description="Customer not found")

    app.logger.info("Returning customer with id: %s", customer_id)
    return jsonify(customer.serialize()), status.HTTP_200_OK


######################################################################
# UPDATE A CUSTOMER
######################################################################
@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    """Update a Customer"""
    app.logger.info("Request to update customer with id: %s", customer_id)
    check_content_type("application/json")

    customer = Customer.find(customer_id)
    if not customer:
        app.logger.warning("Customer with id: %s not found", customer_id)
        abort(status.HTTP_404_NOT_FOUND, description="Customer not found")

    data = request.get_json()
    app.logger.debug("Received data: %s", data)

    try:
        customer.deserialize(data)
        customer.update()
        app.logger.info("Updated customer with id: %s", customer_id)
        return jsonify(customer.serialize()), status.HTTP_200_OK
    except Exception as e:
        app.logger.error("Error updating customer: %s", str(e))
        abort(status.HTTP_400_BAD_REQUEST, description=str(e))


######################################################################
# DELETE A CUSTOMER
######################################################################
@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    """Delete a Customer"""
    app.logger.info("Request to delete customer with id: %s", customer_id)
    customer = Customer.find(customer_id)
    if customer:
        customer.delete()
        app.logger.info("Deleted customer with id: %s", customer_id)

    return "", status.HTTP_204_NO_CONTENT


######################################################################
# LIST ALL CUSTOMERS
######################################################################
@app.route("/customers", methods=["GET"])
def list_customers():
    """Get all Customers, optionally filtered by name"""
    app.logger.info("Request to list all customers")
    name = request.args.get("name")
    if name:
        app.logger.info("Filtering customers by name: %s", name)
        customers = Customer.find_by_name(name)
    else:
        customers = Customer.all()
    results = [customer.serialize() for customer in customers]
    app.logger.info("Returning %d customers", len(results))
    return jsonify(results), status.HTTP_200_OK


@app.route("/error")
def trigger_error():
    """Intentionally triggers a server error for testing"""
    app.logger.info("Triggering internal server error")
    abort(status.HTTP_500_INTERNAL_SERVER_ERROR)


######################################################################
# A C T I V A T E   A   C U S T O M E R
######################################################################
@app.route("/customers/<int:customer_id>/activate", methods=["PUT"])
def activate_customer(customer_id):
    """
    Activate a Customer
    This endpoint will set active=True on a Customer based on its id
    """
    app.logger.info("Request to Activate Customer with id [%s]", customer_id)
    customer = Customer.find(customer_id)
    if not customer:
        app.logger.warning("Customer with id [%s] was not found", customer_id)
        abort(
            status.HTTP_404_NOT_FOUND, f"Customer with id '{customer_id}' was not found"
        )
    customer.active = True
    customer.update()
    app.logger.info("Customer with id [%s] has been activated", customer_id)
    return jsonify(customer.serialize()), status.HTTP_200_OK
