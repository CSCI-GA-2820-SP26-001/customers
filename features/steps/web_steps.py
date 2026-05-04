"""
BDD step definitions: drive the manager admin UI at /admin with Selenium.
"""
# pylint: disable=missing-function-docstring,function-redefined

import json

from behave import given, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

ELLIPSIS = "\u2026"


def _scoped_userid(context, raw):
    suf = getattr(context, "bdd_user_suffix", "") or ""
    return f"{raw}_{suf}" if suf else raw


def _scoped_email(context, raw):
    suf = getattr(context, "bdd_user_suffix", "") or ""
    if not suf or "@" not in raw:
        return raw
    local, _, domain = raw.partition("@")
    return f"{local}+{suf}@{domain}"


def _wait_admin_request_done(driver, timeout=20):
    """Wait until status line is non-empty and not in a loading state."""

    def done(drv):
        try:
            msg = drv.find_element(By.ID, "admin-status").text
        except Exception:  # pylint: disable=broad-except
            return False
        if not msg.strip():
            return False
        if ELLIPSIS in msg or msg.endswith("..."):
            return False
        return True

    WebDriverWait(driver, timeout).until(done)


def _open_admin(context):
    d = context.driver
    base = context.BASE_URL.rstrip("/")
    want = f"{base}/admin"
    try:
        cur = d.current_url.split("#")[0].rstrip("/")
    except Exception:  # pylint: disable=broad-except
        cur = ""
    want_norm = want.rstrip("/")
    if cur == want_norm or (cur.startswith(base) and cur.endswith("/admin")):
        d.refresh()
        WebDriverWait(d, 60).until(
            EC.presence_of_element_located((By.ID, "admin-page"))
        )
        return
    d.set_page_load_timeout(90)
    d.get(want)
    WebDriverWait(d, 60).until(
        EC.presence_of_element_located((By.ID, "admin-page"))
    )


def _fill_input(driver, el_id, text):
    el = driver.find_element(By.ID, el_id)
    driver.execute_script("arguments[0].value = '';", el)
    el.click()
    el.send_keys(text)


def _select_operation(driver, value):
    sel = Select(driver.find_element(By.ID, "admin-operation"))
    sel.select_by_value(value)


def _click_send(driver):
    driver.find_element(By.ID, "btn-execute").click()


def _admin_result_text(driver):
    return driver.find_element(By.ID, "admin-result").text.strip()


def _parse_admin_json(driver):
    raw = _admin_result_text(driver)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


@given("the server is running")
def step_server_is_running(context):
    d = context.driver
    base = context.BASE_URL.rstrip("/")
    ok = d.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        const u = arguments[0];
        fetch(u)
          .then((r) => r.text().then((t) =>
            done((r.status === 200 && t.includes("OK")) ? 1 : 0)
          ))
          .catch(() => done(0));
        """,
        f"{base}/health",
    )
    assert int(ok) == 1, "service not reachable or /health did not return OK"


@given('a customer exists with name "{name}", userid "{userid}", email "{email}"')
def step_create_customer_background(context, name, userid, email):
    _open_admin(context)
    d = context.driver
    _select_operation(d, "create")
    _fill_input(d, "customer-name", name)
    _fill_input(d, "customer-userid", _scoped_userid(context, userid))
    _fill_input(d, "customer-email", _scoped_email(context, email))
    _click_send(d)
    _wait_admin_request_done(d)
    body = _parse_admin_json(d)
    assert body and body.get("id"), f"create failed: {_admin_result_text(d)}"
    context.customer = body
    context.created_customer_ids.append(int(body["id"]))


@when('I visit the "{endpoint}" endpoint')
def step_visit_endpoint(context, endpoint):
    d = context.driver
    ep = endpoint.strip().lower()
    base = context.BASE_URL.rstrip("/")
    if ep == "health":
        payload = d.execute_async_script(
            """
            const done = arguments[arguments.length - 1];
            const u = arguments[0];
            fetch(u)
              .then((r) => r.text().then((t) =>
                done(JSON.stringify({ status: r.status, body: t }))
              ))
              .catch(() => done(JSON.stringify({ status: 0, body: "" })));
            """,
            f"{base}/health",
        )
        data = json.loads(payload)
        context.last_http_status = int(data["status"])
        context.health_response_text = data.get("body", "")
        return
    d.set_page_load_timeout(90)
    d.get(f"{context.BASE_URL}/{endpoint}")
    context.last_http_status = None


@when("I create a customer with the following data")
def step_create_customer(context):
    row = context.table[0]
    _open_admin(context)
    d = context.driver
    _select_operation(d, "create")
    _fill_input(d, "customer-name", row["name"])
    _fill_input(d, "customer-userid", _scoped_userid(context, row["userid"]))
    _fill_input(d, "customer-email", _scoped_email(context, row["email"]))
    _click_send(d)
    _wait_admin_request_done(d)
    body = _parse_admin_json(d)
    if body and body.get("id"):
        context.created_customer_ids.append(int(body["id"]))


@when("I retrieve the customer by id")
def step_retrieve_customer(context):
    _open_admin(context)
    d = context.driver
    _select_operation(d, "read")
    cid = str(context.customer["id"])
    _fill_input(d, "customer-id", cid)
    _click_send(d)
    _wait_admin_request_done(d)


@when("I request the list of customers")
def step_list_customers(context):
    _open_admin(context)
    d = context.driver
    _select_operation(d, "list")
    _click_send(d)
    _wait_admin_request_done(d)


@when("I delete the customer by id")
def step_delete_customer(context):
    _open_admin(context)
    d = context.driver
    _select_operation(d, "delete")
    cid = str(context.customer["id"])
    _fill_input(d, "customer-id", cid)
    _click_send(d)
    _wait_admin_request_done(d)
    cid_int = int(context.customer["id"])
    if cid_int in context.created_customer_ids:
        context.created_customer_ids.remove(cid_int)


@when("I update the customer with the following data")
def step_update_customer(context):
    row = context.table[0]
    _open_admin(context)
    d = context.driver
    _select_operation(d, "update")
    _fill_input(d, "customer-id", str(context.customer["id"]))
    _fill_input(d, "customer-name", row["name"])
    _fill_input(d, "customer-userid", _scoped_userid(context, row["userid"]))
    _fill_input(d, "customer-email", _scoped_email(context, row["email"]))
    _click_send(d)
    _wait_admin_request_done(d)


@when('I query customers by name "{name}"')
def step_query_customers_by_name(context, name):
    _open_admin(context)
    d = context.driver
    _select_operation(d, "query")
    _fill_input(d, "query-name", name)
    _click_send(d)
    _wait_admin_request_done(d)


@when("I activate the customer by id")
def step_activate_customer(context):
    _open_admin(context)
    d = context.driver
    _select_operation(d, "activate")
    _fill_input(d, "customer-id", str(context.customer["id"]))
    _click_send(d)
    _wait_admin_request_done(d)


@then("the response status code should be {status_code:d}")
def step_check_status_code(context, status_code):
    if getattr(context, "last_http_status", None) is not None:
        assert context.last_http_status == status_code, (
            f"expected HTTP {status_code}, got {context.last_http_status}"
        )
        return
    raw = context.driver.find_element(By.ID, "admin-page").get_attribute(
        "data-last-http-status"
    )
    assert raw == str(status_code), f"expected HTTP {status_code}, got {raw!r}"


@then('the response should contain "{text}"')
def step_response_contains(context, text):
    ht = getattr(context, "health_response_text", None)
    if ht is not None:
        assert text in ht, f"expected substring {text!r} in health body"
        return
    if "/admin" in context.driver.current_url:
        body = _admin_result_text(context.driver)
    else:
        body = context.driver.page_source
    assert text in body, f"expected substring {text!r} in {body[:500]}"


@then("the response should be a list")
def step_response_is_list(context):
    data = _parse_admin_json(context.driver)
    assert isinstance(data, list), f"Expected JSON list in admin result, got {data!r}"
