# Customers Service

[![CI](https://github.com/CSCI-GA-2820-SP26-001/customers/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-SP26-001/customers/actions)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-SP26-001/customers/branch/master/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-SP26-001/customers)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

REST API for **Customer** records (Flask + SQLAlchemy + PostgreSQL). All responses are **JSON**, including errors (see `service/common/error_handlers.py`).

**Base URL (local):** `http://localhost:8080`

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| **GET** | `/` | Service metadata JSON (`name`, `version`, `customers_url`) |
| **GET** | `/admin` | Browser admin UI for internal staff (HTML; drives the JSON API) |
| **GET** | `/customers` | List all customers (JSON array; `200`; empty DB → `[]`) |
| **POST** | `/customers` | Create a customer (`201` + `Location` header) |
| **GET** | `/customers/<id>` | Read one customer (`200` or `404`) |
| **PUT** | `/customers/<id>` | Replace a customer (`200` or `404`; body same shape as create) |
| **DELETE** | `/customers/<id>` | Delete (`204` empty body, or `404` if id does not exist) |
| **GET** | `/error` | Test-only route that triggers `500` (for error-handler tests) |

### Request headers

- **POST** and **PUT** require `Content-Type: application/json`.

### JSON body (POST / PUT)

| Field | Type | Required |
|-------|------|----------|
| `name` | string | yes |
| `userid` | string | yes (unique) |
| `email` | string | yes (unique) |
| `address` | string | no |
| `active` | boolean | no (default `true`) |
| `product_attributes` | string | no |
| `assigned_csm` | string | no |
| `arr_value` | number | no |

`id` is assigned by the server and returned in responses.

### Typical HTTP status codes

| Code | When |
|------|------|
| `200` | OK (GET list/one, PUT success) |
| `201` | Created (POST) |
| `204` | No content (DELETE) |
| `400` | Bad request / validation (e.g. create/update) |
| `404` | Not found (GET/PUT one customer) |
| `415` | Wrong or missing `Content-Type` for POST/PUT |
| `500` | Server error (e.g. `/error` test route) |

---

## Run locally

**Prerequisites:** Python 3.x, PostgreSQL (or set `DATABASE_URI`).

```bash
pipenv install --dev
export DATABASE_URI="postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
export PORT=8080
honcho start
```

Open `http://localhost:8080/`.

**VS Code Dev Containers:** PostgreSQL is defined in `.devcontainer/docker-compose.yml` — use **Reopen in Container**, then run from `/app`.

---

## Test & lint

```bash
export DATABASE_URI="postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
make test
make lint
```

---

## Project layout

```text
service/
  models.py       # Customer model
  routes.py       # Flask routes
  common/         # error_handlers, status, logging, CLI
tests/
  test_models.py
  test_routes.py
```

---

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
