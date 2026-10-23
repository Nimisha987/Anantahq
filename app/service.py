"""Business rules: creating, resolving and reporting on short links."""
import secrets
import string
from collections.abc import Callable
from datetime import datetime,timezone

from .errors import(
    AliasReserved,
    AliasTaken,
    CodeGenerationFailed,
    InvalidExpiry,
    LinkExpired,
    LinkNotFound,
)
from .models import Link
from .repository import DuplicateCodeError, LinkRepository
from .validation import is_reserved_alias

Clock = Callable[[],datetime]

CODE_ALPHABET = string.ascii_letters+string.digits
CODE_LENGTH = 7
MAX_GENERATION_ATTEMPTS = 5

def utc_now()->datetime:
    return datetime.now(timezone.utc)

def generate_code(length: int = CODE_LENGTH)->str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(length))


class LinkService:
    def __init__(
        self,
        repo: LinkRepository,
        clock:Clock = utc_now,
        code_generator: Callable[[],str] = generate_code,
    ):
        self._repo = repo
        self._clock = clock
        self._generate_code = code_generator
    def create_link(
            self, url: str, alias: str | None = None, expires_at: datetime | None = None
    ) -> Link:
        now = self._clock()
        if expires_at is not None and expires_at <= now:
            raise InvalidExpiry()

        if alias is not None:
            if is_reserved_alias(alias):
                raise AliasReserved(alias)

            link = Link(code=alias, original_url=url,created_at=now,expires_at=expires_at)
            try:
                self._repo.add(link)
            except DuplicateCodeError:
                raise AliasTaken(alias) from None
            return link

        for _ in range(MAX_GENERATION_ATTEMPTS):
            code = self._generate_code()
            if is_reserved_alias(code):
                continue
            link = Link(code=code, original_url=url,created_at=now, expires_at=expires_at)
            try:
                self._repo.add(link)
                return link
            except DuplicateCodeError:
                continue
        raise CodeGenerationFailed()

    def resolve(self,code:str)->Link:
        """Look up a link for redirection and record the click.
        Unknown -> LinkNotFound, expired -> LinkExpired (neither counts as a click).
        """

        link = self._get_or_raise(code)
        now = self._clock()
        if link.is_expired(now):
            raise LinkExpired(code,link.expires_at.isoformat())
        self._repo.record_click(code, now)

        return link

    def get_stats(self,code:str) ->Link:
        """Stats stay available after expiry; only unknown codes are an error."""
        return self._get_or_raise(code)

    def is_expired(self,link:Link)->bool:
        return link.is_expired(self._clock())


    def _get_or_raise(self,code:str) -> Link:
        link = self._repo.get(code)

        if link is None:
            raise LinkNotFound(code)
        return link
