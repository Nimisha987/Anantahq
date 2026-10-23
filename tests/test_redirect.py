def test_redirects_to_original_url(client,create):
    code = create("https://example.com/target?x=1").json()["code"]
    resp = client.get(f"/{code}")
    assert resp.status_code == 302
    assert resp.headers["location"] == "https://example.com/target?x=1"

def test_unknown_code_returns_404_with_message(client):
    resp = client.get("/doesnotexist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "link_not_found"
    assert "doesnotexist" in body["message"]


def test_link_works_before_expiry_and_gone_after(client,create,clock):
    code = create(expires_at = "2030-01-01T13:00:00Z").json()["code"]

    clock.advance(minutes = 59)
    assert client.get(f"/{code}").status_code == 302

    clock.advance(minutes = 1)
    resp = client.get(f"/{code}")
    assert resp.status_code == 410
    body = resp.json()
    assert body["error"] == "link_expired"
    assert "expired on 2030-01-01T13:00:00" in body["message"]

def test_alias_redirects(client,create):
    create("https://example.com/x",alias = "short")
    assert client.get("/short").headers["location"]=="https://example.com/x"


def test_redirect_is_not_cacheable(client,create):
    code = create().json()["code"]
    assert client.get(f"/{code}").headers["cache-control"] == "no-store"