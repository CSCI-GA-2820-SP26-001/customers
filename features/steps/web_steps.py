"""
Step definitions for Customer Service BDD tests
"""
import json
import requests
from behave import given, when, then


@given("the server is running")
def step_server_is_running(context):
    resp = requests.get(context.BASE_URL + "/health", timeout=10)
    assert resp.status_code == 200, f"Server not running — got {resp.status_code}"


@given('a customer exists with name "{name}", userid "{userid}", email "{email}"')
def step_create_customer_background(context, name, userid, email):
    payload = {"name": name, "userid": userid, "email": email}
    resp = requests.post(
        context.BASE_URL + "/customers",
        json=payload,
        headers=context.headers,
        timeout=10,
    )
    assert resp.status_code == 201, f"Failed to create customer: {resp.text}"
    context.customer = resp.json()
    context.created_customer_ids.append(context.customer["id"])


@when('I visit the "{endpoint}" endpoint')
def step_visit_endpoint(context, endpoint):
    context.resp = requests.get(
        f"{context.BASE_URL}/{endpoint}", timeout=10
    )


@when("I create a customer with the following data")
def step_create_customer(context):
    row = context.table[0]
    payload = {
        "name": row["name"],
        "userid": row["userid"],
        "email": row["email"],
    }
    context.resp = requests.post(
        context.BASE_URL + "/customers",
        json=payload,
        headers=context.headers,
        timeout=10,
    )
    if context.resp.status_code == 201:
        context.created_customer_ids.append(context.resp.json()["id"])


@when("I retrieve the customer by id")
def step_retrieve_customer(context):
    customer_id = context.customer["id"]
    context.resp = requests.get(
        f"{context.BASE_URL}/customers/{customer_id}", timeout=10
    )


@when("I request the list of customers")
def step_list_customers(context):
    context.resp = requests.get(context.BASE_URL + "/customers", timeout=10)


@when("I delete the customer by id")
def step_delete_customer(context):
    customer_id = context.customer["id"]
    context.resp = requests.delete(
        f"{context.BASE_URL}/customers/{customer_id}", timeout=10
    )
    if customer_id in context.created_customer_ids:
        context.created_customer_ids.remove(customer_id)


@then("the response status code should be {status_code:d}")
def step_check_status_code(context, status_code):
    assert context.resp.status_code == status_code, (
        f"Expected {status_code}, got {context.resp.status_code}: {context.resp.text}"
    )


@then('the response should contain "{text}"')
def step_response_contains(context, text):
    assert text in context.resp.text, (
        f"Expected '{text}' in response: {context.resp.text}"
    )


@then("the response should be a list")
def step_response_is_list(context):
    data = context.resp.json()
    assert isinstance(data, list), f"Expected a list, got: {type(data)}"
