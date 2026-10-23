"""Persistence for links. The only module that knows about SQL."""
import sqlite3
from datetime import datetime

from .models import Link

class DuplicateCodeError(Exception):
    """Raised when inserting a link whose code already exists."""

def _to_db(dt: datetime | None)->str|None:
    return dt.isoformat() if dt else None
def _from_db(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
class LinkRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self,link:Link)->None:
        try:
            self._conn.execute(
                "INSERT INTO links (code,original_url,created_at,expires_at) VALUES (?,?,?,?)",
                (link.code, link.original_url,_to_db(link.created_at),_to_db(link.expires_at)),
            )
            self._conn.commit()

        except sqlite3.IntegrityError:
            self._conn.rollback()
            raise DuplicateCodeError(link.code) from None

    def get(self,code:str)->Link | None:
        row = self._conn.execute("SELECT * from links WHERE code = ?",(code,)).fetchone()
        if row is None:
            return None

        return Link(
            code = row["code"],
            original_url = row["original_url"],
            created_at = _from_db(row["created_at"]),
            expires_at= _from_db(row["expires_at"]),
            click_count= row["click_count"],
            last_clicked_at=_from_db(row["last_clicked_at"]),
        )
    def record_click(self,code:str,at:datetime)->None:
        self._conn.execute(
            "UPDATE links SET click_count = click_count+1,last_clicked_at = ? WHERE code = ?",
            (_to_db(at),code),
        )
        self._conn.commit()