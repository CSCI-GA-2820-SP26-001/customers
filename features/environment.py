"""
BDD environment: Selenium WebDriver (no Python HTTP client in steps).
"""
import os
import uuid

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def _chrome_options():
    opts = Options()
    opts.set_capability("pageLoadStrategy", "eager")
    if os.environ.get("HEADLESS", "1").lower() not in ("0", "false", "no"):
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--remote-allow-origins=*")
    opts.add_argument("--disable-features=TranslateUI")
    opts.add_argument("--disable-renderer-backgrounding")

    chromium = os.environ.get("CHROMIUM_BIN")
    if chromium:
        opts.binary_location = chromium
    return opts


def _start_browser(context):
    opts = _chrome_options()
    chromedriver = os.environ.get("CHROMEDRIVER_PATH")
    if chromedriver:
        from selenium.webdriver.chrome.service import Service  # pylint: disable=import-outside-toplevel

        service = Service(chromedriver)
        context.driver = webdriver.Chrome(service=service, options=opts)
    else:
        context.driver = webdriver.Chrome(options=opts)
    context.driver.implicitly_wait(2)
    context.driver.set_page_load_timeout(90)
    context.driver.set_script_timeout(180)
    context.driver.get(f"{context.BASE_URL}/admin")
    WebDriverWait(context.driver, 60).until(
        EC.presence_of_element_located((By.ID, "admin-page"))
    )


def _restart_browser(context):
    try:
        context.driver.quit()
    except Exception:  # pylint: disable=broad-except
        pass
    _start_browser(context)


def before_all(context):
    context.BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")
    _start_browser(context)


def after_all(context):
    driver = getattr(context, "driver", None)
    if driver:
        driver.quit()


def before_scenario(context, scenario):
    context.created_customer_ids = []
    context.last_http_status = None
    context.health_response_text = None
    context.bdd_user_suffix = uuid.uuid4().hex[:10]
    try:
        _browser_delete_all_customers(context)
    except WebDriverException:
        _restart_browser(context)
        try:
            _browser_delete_all_customers(context)
        except WebDriverException:
            pass


def _browser_delete_all_customers(context):
    driver = context.driver
    base = context.BASE_URL.rstrip("/")
    driver.set_page_load_timeout(90)
    driver.set_script_timeout(180)
    driver.get(f"{base}/admin")
    WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.ID, "admin-page"))
    )
    ok = driver.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        const base = arguments[0];
        (async () => {
          try {
            const r = await fetch(base + '/customers', {
              headers: { Accept: 'application/json' }
            });
            if (!r.ok) { done(false); return; }
            const rows = await r.json();
            if (!Array.isArray(rows)) { done(false); return; }
            for (const c of rows) {
              try {
                await fetch(base + '/customers/' + c.id, { method: 'DELETE' });
              } catch (e2) {}
            }
            done(true);
          } catch (e) {
            done(false);
          }
        })();
        """,
        base,
    )
    return bool(ok)


def _cleanup_created_customers(context):
    """DELETE created rows using same-origin fetch from /admin (browser context)."""
    driver = context.driver
    base = context.BASE_URL.rstrip("/")
    ids = list(getattr(context, "created_customer_ids", []))
    if not ids:
        return
    try:
        driver.set_page_load_timeout(90)
        driver.get(f"{base}/admin")
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.ID, "admin-page"))
        )
    except WebDriverException:
        return
    except Exception:  # pylint: disable=broad-except
        return
    for cid in ids:
        try:
            driver.execute_async_script(
                """
                const done = arguments[arguments.length - 1];
                const url = arguments[0];
                fetch(url, { method: 'DELETE' })
                  .then(() => done(true))
                  .catch(() => done(false));
                """,
                f"{base}/customers/{cid}",
            )
        except Exception:  # pylint: disable=broad-except
            pass


def after_scenario(context, scenario):
    try:
        _cleanup_created_customers(context)
    except WebDriverException:
        pass
