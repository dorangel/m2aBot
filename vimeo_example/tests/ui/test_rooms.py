"""UI tests for practicesoftwaretesting.com — shopping cart management.

Target: https://practicesoftwaretesting.com
Credentials: created fresh via the API before the test session (see conftest.py).

Tests cover the core cart lifecycle: add → update quantity → remove.
"""

from pages.rooms_page import CartPage


class TestAddToCart:
    def test_product_appears_in_cart_after_adding(self, cart_page: CartPage):
        product_name = cart_page.add_first_available_product()
        cart_page.navigate_to_cart()

        assert cart_page.is_item_in_cart(product_name)

        # Cleanup
        cart_page.remove_item(product_name)


class TestUpdateCartQuantity:
    def test_quantity_is_updated_in_cart(self, cart_with_item):
        cart_page, product_name = cart_with_item

        cart_page.update_item_quantity(product_name, quantity=3)

        assert cart_page.get_item_quantity(product_name) == 3


class TestRemoveFromCart:
    def test_removed_item_is_no_longer_in_cart(self, cart_with_item):
        cart_page, product_name = cart_with_item

        cart_page.remove_item(product_name)

        assert not cart_page.is_item_in_cart(product_name)
