"""Unit tests for rules that are awkward to trigger through HTTP."""
import pytest
from app.database import connect, init_db
from app.errors import CodeGenerationFailed
from app.repository import LinkRepository
from app.service import LinkService

@pytest.fixture
def repo(tmp_path):
    path = str(tmp_path / "svc.db")
    init_db(path)
    return LinkRepository(connect(path))



def test_generation_retries_on_collision(repo):
    codes = iter(["taken00","taken00","fresh01"])
    service = LinkService(repo,code_generator = lambda:next(codes))
    service.create_link("https://a.example",alias = "taken00")

    link = service.create_link("https://b.example")
    assert link.code == "fresh01"

def test_generation_gives_up_after_repeated_collisions(repo):
    service =LinkService(repo,code_generator = lambda:"samecode")
    service.create_link("https://a.example",alias = "samecode")
    with pytest.raises(CodeGenerationFailed):
        service.create_link("https://b.example")
