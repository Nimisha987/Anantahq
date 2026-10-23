"""Domain model."""
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Link:
    code:str
    original_url: str
    created_at:datetime
    expires_at: datetime | None=None
    click_count: int = 0
    last_clicked_at: datetime | None = None


    def is_expired(self, now: datetime) -> bool:
        """A link is expired from the moment `expires_at` is reached."""
        return self.expires_at is not None and now >=self.expires_at