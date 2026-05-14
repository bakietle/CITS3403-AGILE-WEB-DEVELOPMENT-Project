"""Selenium WebDriver system tests for the Movie Star app.

Covers core user flows end-to-end in a real browser:
    1. Home page loads with site branding
    2. Movie detail page renders content
    3. Search for 'Inception' returns the movie
    4. Nonsense search returns no real movies
    5. Login with seeded demo user works
    6. Logout returns the user to a guest navbar state
    7. Signup with a unique email creates and logs in a new user
    8. Logged-in user adds a movie to their watchlist via AJAX
       (verifies the button text updates without a page reload)

The test class starts the Flask dev server in a subprocess once in
setUpClass, then tears it down in tearDownClass. Each test gets a
fresh headless Chrome via setUp/tearDown.

Usage:
    # 1. Make sure data is seeded (one-time setup):
    flask seed-db

    # 2. Run the tests:
    python -m unittest tests.test_selenium

To watch the browser while tests run (useful for debugging), comment
out the `--headless=new` line in setUp().

Notes:
    - Tests use the dev database, NOT in-memory. Tests that write
      data (signup, watchlist) use unique values or are tolerant of
      pre-existing state so re-runs stay green.
    - Selenium 4.6+ auto-downloads ChromeDriver via SeleniumManager;
      no separate driver install needed. Chrome itself must be
      installed on the machine.
"""
import multiprocessing
import time
import unittest
import uuid

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "http://127.0.0.1:5000"


def _run_server():
    """Run the Flask dev server in a subprocess.

    Imported lazily so multiprocessing's spawn start method (default
    on macOS in Python 3.8+) doesn't re-run app init in the parent.
    """
    from app import app
    app.run(use_reloader=False, port=5000)


class MovieStarSeleniumTests(unittest.TestCase):
    """End-to-end browser tests covering core user flows."""

    @classmethod
    def setUpClass(cls):
        """Start the Flask server in a subprocess once for all tests."""
        cls.server_process = multiprocessing.Process(target=_run_server)
        cls.server_process.start()
        time.sleep(2)  # let Flask bind to the port

    @classmethod
    def tearDownClass(cls):
        """Stop the server after the suite finishes."""
        cls.server_process.terminate()
        cls.server_process.join()

    def setUp(self):
        """Start a fresh headless Chrome for each test."""
        options = Options()
        # Comment the next line out to watch the browser while tests run.
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(3)
        self.wait = WebDriverWait(self.driver, 5)

    def tearDown(self):
        """Quit the browser after each test."""
        self.driver.quit()

    # ── Helpers ──────────────────────────────────────────────────

    def _login(self, email="alex@example.com", password="password123"):
        """Log in via /auth. The login form is the active panel by default."""
        self.driver.get(f"{BASE_URL}/auth")
        # auth.html has two forms (login + signup) inside separate
        # panels. The login form lives in #panel-login, which is the
        # active panel by default.
        login_panel = self.driver.find_element(By.ID, "panel-login")
        login_panel.find_element(By.NAME, "email").send_keys(email)
        pw = login_panel.find_element(By.NAME, "password")
        pw.send_keys(password)
        pw.submit()
        self.wait.until(
            lambda d: "/auth" not in d.current_url and "/login" not in d.current_url
        )

    # ── Tests ────────────────────────────────────────────────────

    def test_01_home_page_loads(self):
        """The home page returns content and references the site name."""
        self.driver.get(BASE_URL)
        title_plus_body = (
            self.driver.title + " " +
            self.driver.find_element(By.TAG_NAME, "body").text
        ).lower()
        self.assertIn(
            "movie",
            title_plus_body,
            "Home page should reference 'Movie' somewhere.",
        )

    def test_02_movie_detail_page_loads(self):
        """Visiting /movie/1 returns a detail page with substantive content."""
        self.driver.get(f"{BASE_URL}/movie/1")
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertGreater(
            len(body_text),
            100,
            "Movie detail page should have substantive content.",
        )

    def test_03_search_finds_inception(self):
        """Searching for 'Inception' returns Inception in the results."""
        self.driver.get(f"{BASE_URL}/search?q=Inception")
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertIn(
            "Inception",
            body_text,
            "Search for 'Inception' should include Inception in results.",
        )

    def test_04_search_finds_nothing_for_nonsense(self):
        """Searching for a UUID returns no real movie results."""
        nonsense = uuid.uuid4().hex
        self.driver.get(f"{BASE_URL}/search?q={nonsense}")
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        self.assertNotIn(
            "Inception", body_text,
            "Nonsense search should not return Inception.",
        )
        self.assertNotIn(
            "Parasite", body_text,
            "Nonsense search should not return Parasite.",
        )

    def test_05_login_with_demo_user(self):
        """Logging in as a seeded user succeeds and changes the navbar."""
        self._login()
        # After login, we should no longer be on /auth
        self.assertNotIn("/auth", self.driver.current_url)
        # The nav should now show a logout or profile link
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        self.assertTrue(
            "logout" in body_text or "log out" in body_text or "profile" in body_text,
            "After login the nav should show Logout or Profile.",
        )

    def test_06_logout_returns_to_guest_state(self):
        """Logging in, then logging out, returns the user to a guest navbar."""
        self._login()
        # Find any element with 'logout' / 'log out' text and click it.
        # XPath translate() does a manual case-insensitive match.
        try:
            logout_el = self.driver.find_element(
                By.XPATH,
                "//*[self::a or self::button]"
                "[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), 'logout') or "
                "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
                "'abcdefghijklmnopqrstuvwxyz'), 'log out')]",
            )
            logout_el.click()
        except Exception:
            # Fallback: logout might be a form, not a link.
            try:
                form = self.driver.find_element(
                    By.CSS_SELECTOR, 'form[action*="logout"]'
                )
                form.submit()
            except Exception:
                self.fail(
                    "Couldn't find a logout link or form. Logout "
                    "button needs a 'Logout' text label or form "
                    "with action containing 'logout'."
                )
        time.sleep(1)  # let the redirect settle
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        self.assertTrue(
            "sign in" in body_text or "login" in body_text or
            "log in" in body_text or "sign up" in body_text,
            "After logout the page should show sign-in or sign-up links.",
        )

    def test_07_signup_creates_new_user(self):
        """Signing up with a unique email creates an account and logs in.

        auth.html puts the signup form inside #panel-signup, which is
        hidden by default. We click the 'Sign Up' tab first to switch
        panels, then fill the form. Note: the confirm field is named
        `confirm_password` (not `confirm`).
        """
        unique = uuid.uuid4().hex[:8]
        new_username = f"sel_{unique}"
        new_email = f"selenium-{unique}@example.com"

        self.driver.get(f"{BASE_URL}/auth")

        # Click the 'Sign Up' tab to reveal the signup panel
        signup_tab = self.driver.find_element(
            By.CSS_SELECTOR, '[data-target="signup"]'
        )
        signup_tab.click()
        time.sleep(0.5)  # let the tab toggle settle

        panel = self.driver.find_element(By.ID, "panel-signup")
        panel.find_element(By.NAME, "username").send_keys(new_username)
        panel.find_element(By.NAME, "email").send_keys(new_email)
        panel.find_element(By.NAME, "password").send_keys("password123")
        confirm = panel.find_element(By.NAME, "confirm_password")
        confirm.send_keys("password123")
        confirm.submit()

        # Successful signup redirects away from /auth and /signup
        self.wait.until(
            lambda d: "/auth" not in d.current_url and "/signup" not in d.current_url
        )
        body_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
        self.assertTrue(
            "logout" in body_text or "log out" in body_text or "profile" in body_text,
            "After signup the user should be logged in.",
        )

    def test_08_add_to_watchlist_via_ajax(self):
        """Logged-in user clicks 'Add to Watchlist'; AJAX updates the
        button text in place WITHOUT reloading the page.

        movie_page.js binds the watchlist click handler to
        `.movie-cta[data-movie-id]`. On a successful response the JS
        rewrites the button's textContent to either 'Added to Watchlist'
        or 'Already on Watchlist'. Both states are acceptable success
        states for this test, which keeps it idempotent across re-runs.

        We assert the URL did NOT change — that's how we prove this is
        an AJAX interaction, not a redirect.
        """
        self._login()
        self.driver.get(f"{BASE_URL}/movie/1")

        # The watchlist button is identifiable by the same selector
        # the JS itself uses, so this is robust against most markup
        # changes that don't affect the JS.
        button = self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".movie-cta[data-movie-id]")
        ))
        initial_text = button.text.strip()
        url_before_click = self.driver.current_url

        # Scroll the button to the centre of the viewport so the click
        # isn't intercepted by a fixed navbar or other overlay.
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        button.click()

        # Wait for the AJAX call to complete — JS rewrites the button
        # text on success.
        self.wait.until(lambda d: button.text.strip() != initial_text)

        # Critical assertion: AJAX means no navigation occurred.
        self.assertEqual(
            self.driver.current_url,
            url_before_click,
            "URL changed after watchlist click — this should be an AJAX "
            "call, not a redirect or form submission.",
        )

        # Both success states are acceptable.
        final_text = button.text.strip().lower()
        self.assertTrue(
            "added" in final_text or "already" in final_text or "watchlist" in final_text,
            f"Button text after click should indicate a watchlist "
            f"status, got: {button.text!r}",
        )


if __name__ == "__main__":
    unittest.main()
