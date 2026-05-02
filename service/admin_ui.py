######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
######################################################################
"""Browser admin console for internal customer operations (managers)."""

from flask import Blueprint, render_template

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
)


@admin_bp.route("/admin")
def admin_dashboard():
    """Serve the single-page admin UI backed by the JSON REST API."""
    return render_template("admin/index.html")
