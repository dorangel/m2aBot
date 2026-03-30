# m2aBot

This repo's goal is to accept an instructions file for testing — which can be a PDF, plain text file, or a URL link — and automatically generate the required tests based on those instructions.

---

## Test Suites

This project contains two test suites: one for a REST API and one for a browser UI.

---

### Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) then run:

```bash
uv sync
uv run playwright install
```

---

### Running the tests

Run everything with a single command:

```bash
uv run pytest
```

Or run each suite separately:

```bash
uv run pytest tests/api/     # API tests only
uv run pytest tests/ui/      # UI tests only
```

To watch the browser during UI tests:

```bash
uv run pytest tests/ui/ --headed
```

---

### Suite 1 — API tests (`tests/api/`)

**Target:** `https://api.restful-api.dev`

No login or credentials are needed. The API is fully public.

The tests perform CRUD operations on the `/objects` endpoint:

| Test class | What it verifies |
|---|---|
| `TestCreateObject` | POST creates an object and returns an ID |
| `TestGetObject` | GET retrieves the correct object by ID |
| `TestUpdateObject` | PUT changes fields and the change is persisted |
| `TestDeleteObject` | DELETE removes the object and it becomes inaccessible |

Each test cleans up after itself (created objects are deleted in teardown).

---

### Suite 2 — UI tests (`tests/ui/`)

**Target:** `https://practicesoftwaretesting.com`

**No manual login required.** Before the first UI test runs, the framework automatically registers a fresh user account via the site's API using a unique generated email. That account is then used to log into the site for all UI tests.

The tests cover the shopping cart lifecycle:

| Test class | What it verifies |
|---|---|
| `TestAddToCart` | Adding a product results in it appearing in the cart |
| `TestUpdateCartQuantity` | Changing the quantity in the cart is reflected correctly |
| `TestRemoveFromCart` | Removing an item means it no longer appears in the cart |

Each test gets its own browser context, so cart state is isolated between tests.

---

### How user creation works

The `test_user` fixture in `conftest.py` calls `POST https://api.practicesoftwaretesting.com/users/register` with a UUID-suffixed email (e.g. `testuser+a1b2c3d4@example.com`) and password `Test1234!` once per test session. The returned credentials are passed to every UI test that needs to log in.

---

### Known issues / decisions

- **restful-api.dev** pre-seeded objects (IDs 1–13) are read-only. Tests only operate on objects they create.
- **practicesoftwaretesting.com** registered users are regular customers — they can use the storefront and cart but not the admin panel.
- UI selectors use `data-test` attributes published by the site. If the site updates and a selector breaks, all selectors are centralised in `pages/rooms_page.py` (`CartPage`).
