def test_stats_for_new_link_has_zero_clicks(client,create):
    code = create().json()["code"]

    resp = client.get(f"/links/{code}/stats")
    assert resp.status_code == 200
    body = resp.json()

    assert body["total_clicks"]==0
    assert body["last_clicked_at"] is None
    assert body["is_expired"] is False

def test_clicks_are_counted_and_last_click_recorded(client,create,clock):
    code = create().json()["code"]
    for _ in range(3):
        client.get(f"/{code}")
        clock.advance(minutes = 5)

    body = client.get(f"/links/{code}/stats").json()

    assert body["total_clicks"]==3
    assert body["last_clicked_at"].startswith("2030-01-01T12:10:00")


def test_clicks_are_tracked_per_link(client,create):
    a= create(alias = "link-a").json()["code"]
    b= create(alias="link-b").json()["code"]
    client.get(f"/{a}")
    client.get(f"/{a}")
    client.get(f"/{b}")
    assert client.get(f"/links/{a}/stats").json()["total_clicks"] == 2
    assert client.get(f"/links/{b}/stats").json()["total_clicks"]==1

def test_stats_unknown_code_returns_404(client):
    resp = client.get("/links/nope/stats")
    assert resp.status_code == 404
    assert resp.json()["error"]=="link_not_found"

def test_expired_visits_are_not_counted_but_stats_remain_available(client,create,clock):
    code = create(expires_at = "2030-01-01T12:30:00Z").json()["code"]
    client.get(f"/{code}")
    clock.advance(hours = 1)
    assert client.get(f"/{code}").status_code == 410

    body = client.get(f"/links/{code}/stats").json()
    assert body["total_clicks"] == 1
    assert body["is_expired"] is True

def test_failed_lookups_do_not_create_stats(client):
    client.get("/ghost")
    assert client.get("/links/ghost/stats").status_code == 404