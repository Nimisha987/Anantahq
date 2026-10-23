import pytest

def test_create_link_returns_code_and_short_url(create):
    resp = create("https://example.com/a?b=c#d")
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["code"]) == 7
    assert body["short_url"] == f"http://testserver/{body['code']}"
    assert body['original_url'] == "https://example.com/a?b=c#d"
    assert body['expires_at'] is None

def test_generate_codes_are_unique(create):
    codes = {create().json()["code"] for _ in range(25)}
    assert len(codes)==25


def test_custom_alias_is_used(create):
    resp = create(alias = "my-link_1")
    assert resp.status_code == 201
    assert resp.json()["code"]=="my-link_1"

def test_aliases_are_case_sensitive(create):
    assert create(alias="Promo").status_code == 201
    assert create(alias="promo").status_code == 201


@pytest.mark.parametrize("alias", ["ab", "has space", "bad/slash", "emoji🙂ok", "x" * 33, ""])
def test_invalid_alias_is_rejected(create, alias):
    resp = create(alias=alias)
    assert resp.status_code == 422
    assert resp.json()["error"] == "validation_error"
    assert "Alias must be 3-32 characters" in resp.json()["message"]

def test_duplicate_alias_is_rejected_with_helpful_error(create):
    assert create(alias="promo").status_code == 201
    resp = create("https://other.example.org",alias= "promo")
    assert resp.status_code == 409
    body = resp.json()
    assert body["error"] == "alias_taken"
    assert "'promo' is already in use" in body["message"]
@pytest.mark.parametrize("alias", ["links","docs","DOCS","redoc"])
def test_reserved_alias_is_rejected(create,alias):
    resp = create(alias = alias)
    assert resp.status_code == 422
    assert resp.json()["error"] == "alias_reserved"


@pytest.mark.parametrize(
    "url",
    [
        "not a url",
        "example.com",
        "ftp://example.com/file",
        "javascript:alert(1)",
        "https://",
        "http:///path-only",
        "https://exa mple.com",
        "https://example.com:99999",
        "",
        "https://example.com/"+"a" * 2100,

    ],
)
def test_invalid_url_is_rejected(create,url):
    resp = create(url)
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "validation_error"
    assert body["details"][0]["field"]=="url"

def test_missing_url_is_rejected(client):
    resp = client.post("/links",json= {})
    assert resp.status_code == 422
    assert resp.json()["details"][0]["field"] == "url"

def test_expiry_in_the_past_is_rejected(create):
    resp = create(expires_at = "2020-01-01T00:00:00Z")
    assert resp.status_code == 422
    assert resp.json()["error"] == "invalid_expiry"


def test_expiry_without_timezone_is_treated_as_utc(create):
    resp = create(expires_at = "2030-06-01T00:00:00")
    assert resp.status_code == 201
    assert resp.json()["expires_at"].startswith("2030-06-01T00:00:00")