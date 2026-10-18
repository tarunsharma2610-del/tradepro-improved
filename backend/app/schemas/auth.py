from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_code: str | None = Field(default=None, min_length=6, max_length=6)


class LoginResult(BaseModel):
    """What the login endpoint returns when MFA is required but no code was
    given yet — tokens are NOT issued in this case."""

    mfa_required: bool = False


class MfaEnrollResponse(BaseModel):
    otpauth_uri: str  # render as a QR code client-side
    secret: str  # shown once so the user can also type it in manually


class MfaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


class MfaStepUpRequest(BaseModel):
    """Fresh credentials required before a privileged safety reset."""
    password: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=6, max_length=6)


class MfaStepUpResponse(BaseModel):
    step_up_token: str
    expires_in: int = 300
