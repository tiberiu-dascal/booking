import os
import sys
import time
from datetime import date, timedelta

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

LOGIN_URL = "https://sportinclujnapoca.ro/login"
RESERVATIONS_URL = (
    "https://sportinclujnapoca.ro/reservations/table-tennis"
    "?preferredSportComplex=la-terenuri-base"
)
SLOT = os.environ.get("SLOT", "19:00")
POST_CONFIRM_WAIT = int(os.environ.get("POST_CONFIRM_WAIT", "15"))


def target_date():
    today = date.today()
    weekday = int(os.environ.get("WEEKDAY", "2"))  # 0=Monday, 2=Wednesday
    weeks = int(os.environ.get("WEEKS_AHEAD", "2"))
    day = today - timedelta(days=today.weekday()) + timedelta(days=weekday)
    return day + timedelta(weeks=weeks)


def make_driver():
    opts = webdriver.ChromeOptions()
    opts.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    opts.add_experimental_option("detach", True)  # keep browser open for confirmation
    return webdriver.Chrome(options=opts)


def login(driver, wait):
    driver.get(LOGIN_URL)
    wait.until(EC.visibility_of_element_located((By.NAME, "email"))).send_keys(
        os.environ["SPORT_EMAIL"]
    )
    driver.find_element(By.NAME, "password").send_keys(os.environ["SPORT_PASSWORD"])
    submit = driver.find_element(By.CSS_SELECTOR, "button[type=submit]")
    driver.execute_script("arguments[0].click()", submit)  # cookie banner may overlap
    wait.until(lambda d: "/login" not in d.current_url)


def go_to_date(driver, wait, target):
    """Page forward week by week until the target day button is enabled, then click it."""
    cookie = driver.find_elements(By.ID, "rcc-confirm-button")
    if cookie:
        driver.execute_script("arguments[0].click()", cookie[0])
    week_header = "//h6[contains(., ' - ')][string-length(normalize-space()) > 20]"
    day_xpath = (
        f"//button[.//h6[normalize-space()='{target.day}']]"
        "[not(@disabled)]"
    )
    wait.until(EC.presence_of_element_located((By.XPATH, week_header)))
    monday = lambda d: d - timedelta(days=d.weekday())
    weeks = (monday(target) - monday(date.today())).days // 7
    for _ in range(weeks):
        header = driver.find_element(By.XPATH, week_header)
        nxt = header.find_element(By.XPATH, "../following-sibling::div//button")
        old = header.text
        driver.execute_script("arguments[0].click()", nxt)
        wait.until(
            lambda d: d.find_element(By.XPATH, week_header).text != old
        )
    day = wait.until(EC.presence_of_element_located((By.XPATH, day_xpath)))
    driver.execute_script("arguments[0].click()", day)


def main():
    driver = make_driver()
    wait = WebDriverWait(driver, 20)
    login(driver, wait)
    driver.get(RESERVATIONS_URL)
    target = target_date()
    print("Target date:", target)
    go_to_date(driver, wait, target)
    slot_xpath = f"//span[normalize-space()='{SLOT}']"
    span = wait.until(EC.presence_of_element_located((By.XPATH, slot_xpath)))
    btns = span.find_elements(By.XPATH, "./ancestor::div[@role='button'][1]")
    if not btns:  # disabled slots are rendered without role="button"
        sys.exit(f"{SLOT} is disabled on {target}.")
    btn = btns[0]
    driver.execute_script("arguments[0].click()", btn)
    submit = driver.find_element(By.CSS_SELECTOR, "form button[type=submit]")
    try:
        wait.until(lambda d: submit.is_enabled())
    except TimeoutException:
        sys.exit(f"Selected {SLOT} on {target}, but 'Rezervă' stayed disabled (court needed?).")
    driver.execute_script("arguments[0].click()", submit)
    boxes = wait.until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, "label input[type=checkbox]")) >= 3
        and d.find_elements(By.CSS_SELECTOR, "label input[type=checkbox]")
    )
    for box in boxes:
        if not box.is_selected():
            driver.execute_script("arguments[0].click()", box)
    confirm = driver.find_element(By.XPATH, "//button[normalize-space()='Confirmă rezervarea']")
    wait.until(lambda d: confirm.is_enabled())
    driver.execute_script("arguments[0].click()", confirm)
    time.sleep(POST_CONFIRM_WAIT)  # let the reservation finish before anything else touches the account
    print(f"Booked {SLOT} on {target}: checked {len(boxes)} boxes and confirmed.")


if __name__ == "__main__":
    main()
