from playwright.sync_api import Page, expect


class LoginPage:
    """Sign-in page for practicesoftwaretesting.com.

    URL: https://practicesoftwaretesting.com/auth/login
    """

    URL = "https://practicesoftwaretesting.com/auth/login"

    def __init__(self, page: Page):
        self.page = page
        self.email_input = page.locator("[data-test='email']")
        self.password_input = page.locator("[data-test='password']")
        self.login_button = page.locator("[data-test='login-submit']")

    def navigate(self) -> None:
        self.page.goto(self.URL)
        expect(self.email_input).to_be_visible()

    def login(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.login_button.click()
        # Wait for the auth token to be stored and the page to update.
        # We look for the nav element that only appears for logged-in users.
        expect(self.page.locator("[data-test='nav-menu']")).to_be_visible(
            timeout=15_000
        )
