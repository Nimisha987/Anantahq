# URL Shortener

A small URL-shortener service built with **FastAPI** and **SQLite**.

- Create short links with an optional custom alias and optional expiry
- Redirect (`302`), with clear `404` (unknown) and `410` (expired) responses
- Per-link click counting and a stats endpoint
- URL and alias validation with helpful, consistently-shaped errors

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn app.main:create_app --factory --reload
```

The API is now on http://127.0.0.1:8000 and interactive docs are at http://127.0.0.1:8000/docs.

Configuration (environment variables, all optional):

| Variable | Default | Purpose |
|---|---|---|
| `SHORTENER_DB_PATH` | `shortener.db` | SQLite file location (created automatically) |
| `SHORTENER_BASE_URL` | request's own base URL | Public base used in the returned `short_url`, e.g. `https://sho.rt` |

## Run the tests

```bash
pytest
```

The tests use a temporary database per test and a fake clock, so expiry is tested without sleeping.

## Endpoints

| Method | Path | Description | Success |
|---|---|---|---|
| `POST` | `/links` | Create a short link | `201` |
| `GET` | `/{code}` | Redirect to the original URL (counts a click) | `302` |
| `GET` | `/links/{code}/stats` | Total clicks and last clicked time | `200` |

### `POST /links`

| Field | Required | Notes |
|---|---|---|
| `url` | yes | Absolute `http`/`https` URL with a host, max 2048 chars |
| `alias` | no | 3-32 chars: letters, digits, `-`, `_`. Case-sensitive. A 7-char random code is generated if omitted |
| `expires_at` | no | ISO-8601 datetime in the future. No UTC offset = UTC |

### Errors

Every error uses the same JSON shape:

```json
{ "error": "alias_taken", "message": "The alias 'demo' is already in use. Please choose a different alias." }
```

| Status | `error` | When |
|---|---|---|
| `404` | `link_not_found` | Unknown code (redirect or stats) |
| `409` | `alias_taken` | Alias already exists |
| `410` | `link_expired` | Link is past its expiry (redirect) |
| `422` | `validation_error` | Bad URL / alias / body. Includes a `details` list of `{field, message}` |
| `422` | `alias_reserved` | Alias collides with an app route (`links`, `docs`, `redoc`, ...) |
| `422` | `invalid_expiry` | `expires_at` is not in the future |

## Example requests

Create a link with a generated code:

```bash
curl -X POST http://127.0.0.1:8000/links \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/some/very/long/path?x=1"}'
```
```json
{"code":"aZ3kP9q","short_url":"http://127.0.0.1:8000/aZ3kP9q","original_url":"https://example.com/some/very/long/path?x=1","created_at":"2026-10-23T05:51:57.994595Z","expires_at":null}
```

Create a link with a custom alias and expiry:

```bash
curl -X POST http://127.0.0.1:8000/links \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/launch", "alias": "launch", "expires_at": "2031-01-01T00:00:00Z"}'
```

Follow a link (`-i` shows the `302` and `Location` header; use `-L` to follow it):

```bash
curl -i http://127.0.0.1:8000/launch
```

Get stats:

```bash
curl http://127.0.0.1:8000/links/launch/stats
```
```json
{"code":"launch","original_url":"https://example.com/launch","total_clicks":1,"last_clicked_at":"2026-10-23T05:51:58.007087Z","created_at":"2026-10-23T05:51:57.994595Z","expires_at":"2031-01-01T00:00:00Z","is_expired":false}
```

Duplicate alias (`409`):

```bash
curl -X POST http://127.0.0.1:8000/links -H 'Content-Type: application/json' \
  -d '{"url": "https://other.example.com", "alias": "launch"}'
# {"error":"alias_taken","message":"The alias 'launch' is already in use. Please choose a different alias."}
```

Invalid URL (`422`):

```bash
curl -X POST http://127.0.0.1:8000/links -H 'Content-Type: application/json' -d '{"url": "ftp://x"}'
# {"error":"validation_error","message":"Invalid request. url: URL must start with http:// or https://.","details":[...]}
```

## Design notes

```
app/
  main.py        app factory (wiring, settings, injectable clock)
  api.py         routes, dependencies, error rendering   <- HTTP only
  schemas.py     request/response models
  service.py     business rules (aliases, expiry, click recording)
  repository.py  all SQL                                  <- persistence only
  database.py    connection + schema
  validation.py  URL / alias validation (pure functions)
  errors.py      domain exceptions -> status + error code
  models.py      Link dataclass
```

- **Redirect is `302`, not `301`**, with `Cache-Control: no-store`, so browsers can't cache it and bypass click counting.
- **Expiry boundary:** a link is expired once `now >= expires_at`. Expired and unknown visits are *not* counted as clicks. Stats stay readable for expired links (`is_expired: true`).
- **Clicks are counted atomically** (`SET click_count = click_count + 1`), so concurrent visits are not lost.
- **Alias uniqueness is enforced by the database** (primary key), so two simultaneous requests can't both claim an alias; generated codes retry on collision.
- **Reserved aliases** (`links`, `docs`, ...) are rejected so they can't shadow application routes.
- **Time is injected** (`create_app(clock=...)`), which keeps expiry tests deterministic.
- SQLite keeps setup zero-effort; only `repository.py` and `database.py` would change for Postgres.
