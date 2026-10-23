"""Domain exceptions . Each carries a stable machine-readable `error` code,
an HTTP status and a human-readable message; the API layer renders them
all in one consistent JSON shape.
"""

class AppError(Exception):
    status_code = 400
    error = "bad_request"

    def __init__(self,message:str):
        super().__init__(message)
        self.message = message

class LinkNotFound(AppError):
    status_code = 404
    error = "link_not_found"

    def __init__(self,code: str):
        super().__init__(f"No short link exists with code '{code}'.")

class LinkExpired(AppError):
    status_code = 410
    error = "link_expired"

    def __init__(self,code:str,expired_at:str):
        super().__init__(f"The short link '{code}' expired on {expired_at} and is no longer available.")

class AliasTaken(AppError):
    status_code = 409
    error = "alias_taken"
    def __init__(self, alias:str):
        super().__init__(f"The alias '{alias}' is already in use. Please choose a different alias.")
class AliasReserved(AppError):
    status_code = 422
    error = "alias_reserved"

    def __init__(self, alias: str):
        super().__init__(f"The alias '{alias}' is reserved and cannot be used. Please choose a different alias.")
class InvalidExpiry(AppError):
    status_code = 422
    error = "invalid_expiry"

    def __init__(self):
        super().__init__("expires_at must be a time in the future.")


class CodeGenerationFailed(AppError):
    status_code = 503
    error = "code_generation_failed"

    def __init__(self):
        super().__init__("Could not generate a unique short code. Please try again.")