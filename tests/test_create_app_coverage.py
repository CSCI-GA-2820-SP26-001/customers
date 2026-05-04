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
Exercise create_app() and before_request branches for coverage (Codecov patch).
"""

import logging
import os
from unittest import TestCase
from unittest.mock import patch

import wsgi
from service import create_app
from service.models import db

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


class TestCreateAppLifecycle(TestCase):
    """service.__init__: session reset hook and create_all failure under pytest."""

    @classmethod
    def setUpClass(cls):
        wsgi.app.config.setdefault("TESTING", True)
        wsgi.app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        wsgi.app.logger.setLevel(logging.CRITICAL)

    def tearDown(self):
        with wsgi.app.app_context():
            try:
                db.session.remove()
            except RuntimeError:
                pass

    def test_before_request_calls_remove_when_rollback_raises(self):
        """If rollback() fails, before_request still clears the session via remove()."""
        client = wsgi.app.test_client()
        with patch.object(db.session, "rollback", side_effect=RuntimeError("rollback")):
            with patch.object(db.session, "remove") as mock_remove:
                resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        mock_remove.assert_called()

    def test_create_all_failure_is_reraised_under_pytest(self):
        """db.create_all() errors propagate when pytest is loaded (no sys.exit)."""
        with patch.object(db, "create_all", side_effect=RuntimeError("no db")):
            with self.assertRaises(RuntimeError) as ctx:
                create_app()
        self.assertIn("no db", str(ctx.exception))
