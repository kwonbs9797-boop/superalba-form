"""Open the Streamlit app in a headless browser so Community Cloud never puts it to sleep.

If the app is already asleep, click the "Yes, get this app back up!" button.
Run by .github/workflows/keep-awake.yml every few hours.
"""
import os
import sys

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

URL = os.environ.get("APP_URL", "https://superalba-form.streamlit.app/")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(8_000)
    wake = page.get_by_role("button", name="Yes, get this app back up!")
    if wake.count():
        print("App was asleep: waking it up")
        wake.first.click()
        page.wait_for_timeout(60_000)
    else:
        print("App is awake")
    # Confirm the app itself rendered (it lives in an iframe on *.streamlit.app)
    ok = False
    for frame in page.frames:
        try:
            if frame.get_by_text("제출하기").count():
                ok = True
                break
        except PWTimeout:
            pass
    print("Form rendered:", ok)
    browser.close()
    sys.exit(0 if ok else 1)
