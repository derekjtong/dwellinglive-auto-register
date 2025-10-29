import os
import sys
import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load credentials from .env file
load_dotenv()

EMAIL = os.getenv("DWELLINGLIVE_EMAIL")
PASSWORD = os.getenv("DWELLINGLIVE_PASSWORD")
BASE_URL = os.getenv("DWELLINGLIVE_BASE_URL", "https://community.dwellinglive.com/")

if not EMAIL or not PASSWORD:
    print("❌ Please set DWELLINGLIVE_EMAIL and DWELLINGLIVE_PASSWORD in your .env file.")
    sys.exit(1)

# Guest configuration
GUEST_NAME = "Food Delivery"
now = datetime.datetime.now()
start_date = now.strftime("%m/%d/%Y")
end_date = (now + datetime.timedelta(days=1)).strftime("%m/%d/%Y")

def safe_click(page, selector):
    """Click element if it exists."""
    try:
        page.locator(selector).first.click(timeout=3000)
        return True
    except Exception:
        return False

with sync_playwright() as p:
    # browser = p.chromium.launch(headless=True)
    browser = p.chromium.launch(headless=False, slow_mo=200)

    context = browser.new_context()
    page = context.new_page()

    print("Opening DwellingLive...")
    page.goto(BASE_URL, wait_until="domcontentloaded")

    # --- LOGIN ---
    print("Logging in...")
    page.fill('input[name="txtUserName"]', EMAIL)
    page.fill('input[name="txtPassword"]', PASSWORD)
    page.click('input[name="btnLogin"]')

    # Wait for redirect to dashboard after login
    try:
        page.wait_for_url("**/homesite/dashboard.aspx", timeout=15000)
        print("Logged in successfully, dashboard loaded.")
    except Exception as e:
        print("Dashboard did not load automatically. Waiting a bit longer...")
        page.wait_for_timeout(5000)
    
    # --- GO TO GUEST LIST PAGE ---
    guest_page_url = "https://community.dwellinglive.com/visitormanagement/guestlist.aspx"
    print(f"➡️ Navigating to guest list page: {guest_page_url}")
    page.goto(guest_page_url, wait_until="domcontentloaded")

    # --- ADD GUEST ---
    print("Creating guest pass...")
    if not safe_click(page, 'button:has-text("Add Guest")'):
        safe_click(page, 'a:has-text("Add Guest")')

    # --- ADD GUEST DETAILS ---
    print("Selecting pass type and filling company...")
    
    # Select "Service" from dropdown
    page.select_option('select[name="ctl00$Body$ddlPassType"]', label="Service")
    
    # Fill company name
    page.fill('input[name="ctl00$Body$CompanyTextBox"]', "Food Delivery")

    print("Pass type 'Service' selected and company 'Food Delivery' entered.")
    page.wait_for_timeout(2000)  # wait 2s for postback


    # Save / Create button
    print("Saving guest...")
    page.click('a#Body_btnSaveGuest')
    page.wait_for_timeout(4000)

    # --- CONFIRMATION ---
    if page.locator(f"text={GUEST_NAME}").first.is_visible():
        print(f"Guest pass for '{GUEST_NAME}' created successfully!")
    else:
        print("Could not confirm creation — please verify manually.")

    context.close()
    browser.close()
