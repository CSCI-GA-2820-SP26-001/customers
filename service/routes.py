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
CustomerProfileModel Service

This service implements a REST API that allows you to Create, Read, Update
and Delete CustomerProfileModel
"""

from flask import jsonify, request, url_for, abort
from flask import current_app as app  # Import Flask application
from service.models import CustomerProfileModel
from service.common import status  # HTTP Status Codes


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        "Reminder: return some useful information in json format about the service here",
        status.HTTP_200_OK,
    )


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
# C R E A T E   A   C U S T O M E R   P R O F I L E
######################################################################
@app.route("/customerprofiles", methods=["POST"])
def create_customerprofiles():
    """
    Create a Customer Profile
    This endpoint will create a Customer Profile based the data in the body that is posted
    """
    app.logger.info("Request to Create a Customer Profile...")
    check_content_type("application/json")
    profile = CustomerProfileModel()
    # Get the data from the request and deserialize it
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    profile.deserialize(data)

    # Check for duplicate userid
    if CustomerProfileModel.query.filter_by(userid=profile.userid).first():
        abort(status.HTTP_409_CONFLICT, description="userid already exists")

    # Check for duplicate email
    if CustomerProfileModel.query.filter_by(email=profile.email).first():
        abort(status.HTTP_409_CONFLICT, description="email already exists")

    # Save the new Customer Profile to the database
    profile.create()
    app.logger.info("CustomerProfile with new id [%s] saved!", profile.id)
    # Return the location of the new Customer Profile
    location_url = url_for("create_customerprofiles", _external=True)
    return (
        jsonify(profile.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location_url},
    )


######################################################################
# Checks the ContentType of a request
######################################################################
def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )
    if request.headers["Content-Type"] == content_type:
        return
    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# Logs error messages before aborting
######################################################################
def error(status_code, reason):
    """Logs the error and then aborts"""
    app.logger.error(reason)
    abort(status_code, reason)


@app.route("/error")
def trigger_error():
    """Triggers a 500 error for testing purposes"""
    abort(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error")
