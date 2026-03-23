# Customers Service

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

## Overview

The Customers Service is a REST API that manages customer profiles for an e-commerce platform. It allows you to Create, Read, Update, Delete, and List customers stored in a PostgreSQL database.

## API Endpoints

### Root URL
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Returns service information |

**Response example:**
```json
{
  "name": "Customer REST API Service",
  "version": "1.0"
}
```

### Customers
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/customers` | Returns a list of all customers |

#### GET /customers
Returns all customers as a JSON array.

**Response example:**
```json
[
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "address": "123 Main St"
  }
]
```

**Response codes:**
- `200 OK` — always returned, even if no customers exist (returns empty array `[]`)

## Customer Model

A Customer has the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | auto | Unique identifier |
| first_name | string | yes | Customer's first name |
| last_name | string | yes | Customer's last name |
| address | string | no | Customer's address |

## Running the Service

### Prerequisites
- Docker Desktop
- VSCode with Dev Containers extension

### Setup
1. Clone the repository
2. Open in VSCode
3. Reopen in Dev Container when prompted
4. The service will be available at `http://localhost:8080`

### Running Tests
```bash
make test
```

### Running Lint
```bash
make lint
```

## Contents
```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to fix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.