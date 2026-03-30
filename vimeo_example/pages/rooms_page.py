from playwright.sync_api import Page, Locator, expect


class CartPage:
    """Shopping cart page for practicesoftwaretesting.com.

    Covers two pages in the user journey:
      - Product listing  (https://practicesoftwaretesting.com/)  — for adding items
      - Cart / checkout  (https://practicesoftwaretesting.com/checkout) — for managing items

    Implements the Page Object Model pattern — all selectors are centralised here.
    """

    PRODUCTS_URL = "https://practicesoftwaretesting.com/"
    CART_URL = "https://practicesoftwaretesting.com/checkout"

    def __init__(self, page: Page):
        self.page = page

    # ------------------------------------------------------------------
    # Adding items
    # ------------------------------------------------------------------

    def add_product_to_cart(self, product_name: str) -> None:
        """Navigate to the product listing, find the product by name, and add it to cart."""
        self.page.goto(self.PRODUCTS_URL)
        expect(self.page.locator("[data-test='product']").first).to_be_visible(
            timeout=10_000
        )

        product_card = self.page.locator("[data-test='product']").filter(
            has_text=product_name
        )
        product_card.click()

        self.page.locator("[data-test='add-to-cart']").click()
        # Wait for the cart badge to update (confirms item was added)
        expect(self.page.locator("[data-test='cart-quantity']")).not_to_have_text(
            "0", timeout=5_000
        )

    def add_first_available_product(self) -> str:
        """Add the first product in the listing to the cart. Returns its name."""
        self.page.goto(self.PRODUCTS_URL)
        first = self.page.locator("[data-test='product']").first
        expect(first).to_be_visible(timeout=10_000)

        name = first.locator("[data-test='product-name']").text_content().strip()
        first.click()
        self.page.locator("[data-test='add-to-cart']").click()
        expect(self.page.locator("[data-test='cart-quantity']")).not_to_have_text(
            "0", timeout=5_000
        )
        return name

    # ------------------------------------------------------------------
    # Cart management
    # ------------------------------------------------------------------

    def navigate_to_cart(self) -> None:
        self.page.goto(self.CART_URL)
        expect(self.page.locator("[data-test='cart-item']").first).to_be_visible(
            timeout=10_000
        )

    def update_item_quantity(self, product_name: str, quantity: int) -> None:
        """Set the quantity field for a specific cart item."""
        row = self._cart_row(product_name)
        qty_input = row.locator("[data-test='product-quantity']")
        qty_input.fill(str(quantity))
        qty_input.press("Tab")  # trigger the change event

    def remove_item(self, product_name: str) -> None:
        """Remove a specific item from the cart."""
        self._cart_row(product_name).locator("[data-test='product-remove']").click()
        expect(self._cart_row(product_name)).not_to_be_visible(timeout=5_000)

    # ------------------------------------------------------------------
    # Assertion helpers
    # ------------------------------------------------------------------

    def is_item_in_cart(self, product_name: str) -> bool:
        return self._cart_row(product_name).is_visible()

    def get_item_quantity(self, product_name: str) -> int:
        return int(
            self._cart_row(product_name)
            .locator("[data-test='product-quantity']")
            .input_value()
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cart_row(self, product_name: str) -> Locator:
        return (
            self.page.locator("[data-test='cart-item']")
            .filter(has_text=product_name)
            .first
        )
