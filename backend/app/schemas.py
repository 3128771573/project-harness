from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    username: str
    email: EmailStr
    nickname: str | None
    avatar: str | None
    bio: str | None
    role: str | None = None
    created_time: datetime

    @field_validator("role", mode="before")
    @classmethod
    def role_to_name(cls, v):
        # SQLAlchemy 关系对象转角色名
        if v is not None and not isinstance(v, str):
            return getattr(v, "name", None)
        return v


class ProfileUpdate(BaseModel):
    nickname: str | None = Field(default=None, max_length=64)
    bio: str | None = Field(default=None, max_length=2000)
    avatar: str | None = Field(default=None, max_length=512)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class AiChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class AiChatResponse(BaseModel):
    answer: str
    model: str


class AiHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question: str
    answer: str
    model: str | None
    created_time: datetime


class AiHistoryList(BaseModel):
    items: list[AiHistoryItem]
    total: int


# --- Admin ---


class AdminStats(BaseModel):
    total_users: int
    today_new_users: int
    total_ai_calls: int
    today_ai_calls: int


class UserAdminOut(BaseModel):
    uid: str
    username: str
    email: EmailStr
    role: str | None = None
    is_active: bool
    created_time: datetime


class UserAdminList(BaseModel):
    items: list[UserAdminOut]
    total: int
    page: int
    page_size: int


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: str = Field(min_length=1, max_length=32)


class SystemStatus(BaseModel):
    cpu: dict
    memory: dict
    disk: dict
    network: dict
    system: dict
    temps: list[dict] = []
    collected_at: datetime


class AiConfigUpdate(BaseModel):
    api_key: str | None = Field(default=None, max_length=512, description="留空则不修改")
    base_url: str | None = Field(default=None, max_length=512)
    model: str | None = Field(default=None, max_length=128)
    clear_api_key: bool = Field(default=False, description="置 true 时清除 api_key（回退 mock）")


class AiConfigOut(BaseModel):
    api_key: str | None = None
    api_key_set: bool = False
    base_url: str
    model: str


class UserUsageItem(BaseModel):
    uid: str
    username: str
    email: EmailStr
    total_calls: int
    today_calls: int
    last_used: datetime | None = None


class UserUsageList(BaseModel):
    items: list[UserUsageItem]
    total: int
    total_calls: int


class RefreshTokenAdminOut(BaseModel):
    id: str
    uid: str
    username: str | None = None
    created_time: datetime
    expires_at: datetime
    revoked: bool
