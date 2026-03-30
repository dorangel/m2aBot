import pytest
from pages.login_page import LoginPage
from pages.rooms_page import CartPage


@pytest.fixture
def cart_page(page, test_user) -> CartPage:
    """Log in as the session test user and return a CartPage instance.

    ``test_user`` is a session-scoped fixture that creates a unique user
    via the API before the first test runs.
    """
    login = LoginPage(page)
    login.navigate()
    login.login(email=test_user["email"], password=test_user["password"])
    return CartPage(page)


@pytest.fixture
def cart_with_item(cart_page: CartPage):
    """Add a product to the cart before the test and clear it afterwards.

    Yields a tuple of (cart_page, product_name).
    """
    product_name = cart_page.add_first_available_product()
    cart_page.navigate_to_cart()
    yield cart_page, product_name
    # Best-effort cleanup — item may already be removed by the test
    if cart_page.is_item_in_cart(product_name):
        cart_page.remove_item(product_name)
