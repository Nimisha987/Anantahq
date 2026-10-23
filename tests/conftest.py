from datetime import datetime , timedelta , timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

class FakeClock:
    """Controllable clock so expiry can be tested without sleeping."""
    def __init__(self):
        self.current = datetime(2030,1,1,12,0,tzinfo=timezone.utc)

    def __call__(self)->datetime:
        return self.current

    def advance(self,**kwargs)->None:
        self.current += timedelta(**kwargs)


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def client(tmp_path,clock):
    app = create_app(Settings(db_path=str(tmp_path/"test.db")),clock=clock)
    return TestClient(app,follow_redirects=False)

@pytest.fixture
def create(client):
    def _create(url="https://example.com/some/long/path",**extra):
        return client.post("/links",json={"url": url,**extra})
    return _create