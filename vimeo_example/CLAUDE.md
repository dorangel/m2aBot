# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

m2aBot is a test automation project that accepts an instructions file (PDF, plain text, or URL) and generates the required tests. The current test suite covers a REST API and a web UI using two free public testing platforms.

## Setup & Commands

This project uses [uv](https://github.com/astral-sh/uv) for dependency management (Python 3.12).

```bash
# Install dependencies
uv sync

# Install Playwright browsers (required once after first install)
uv run playwright install

# Run all tests
uv run pytest

# Run only API tests
uv run pytest tests/api/

# Run only UI tests
uv run pytest tests/ui/

# Run a single test by name
uv run pytest -k "test_removed_item_is_no_longer_in_cart"

# Run UI tests in headed mode (visible browser)
uv run pytest tests/ui/ --headed
```

## Architecture

```
api/
  booking_client.py     # ObjectsClient — wraps restful-api.dev /objects CRUD
  user_client.py        # UserApiClient — registers new users on practicesoftwaretesting.com

pages/                  # Page Object Model (browser layer)
  login_page.py         # Sign-in page (accepts email/password as parameters)
  rooms_page.py         # CartPage — add products to cart, update qty, remove items

tests/
  data/
    factories.py        # make_object(), make_user_credentials()
  api/
    test_bookings.py    # API tests: create, get, update, delete object
  ui/
    conftest.py         # UI fixtures: cart_page (logged-in), cart_with_item
    test_rooms.py       # UI tests: add to cart, update quantity, remove from cart

conftest.py             # Root fixtures: objects_client, created_object, test_user
```

### Design patterns

- **Page Object Model** — all selectors live in `pages/`; tests call named methods only.
- **Data factories** — `tests/data/factories.py` centralises payload and credential construction.
- **Self-contained test users** — `test_user` (session-scoped) calls the API to register a unique user before any UI test runs. No shared or pre-seeded accounts are required.
- **Fixture-based setup/teardown** — `created_object` and `cart_with_item` create resources before each test and clean up in teardown, keeping tests isolated.
- **Session-scoped API client** — `objects_client` is instantiated once per test session.

### Targets

| Suite | URL | Auth |
|---|---|---|
| API objects | `https://api.restful-api.dev` | None required |
| User registration | `https://api.practicesoftwaretesting.com` | None (public registration) |
| Web UI | `https://practicesoftwaretesting.com` | Created per session via API |

### Known considerations

- **restful-api.dev**: IDs are strings (UUIDs). Pre-seeded objects (1–13) are read-only; tests only delete objects they create.
- **practicesoftwaretesting.com**: User accounts created via the API are regular customers — they have access to the storefront and cart but not the admin panel.
- The `cart_with_item` fixture navigates to the cart after adding the item; tests that need a clean cart state get one because each test gets a fresh browser context from pytest-playwright.
- `data-test` attributes are used throughout for stable selectors. If a selector breaks, check `CartPage` in `pages/rooms_page.py`.
