from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    code: str | None = Field(default=None, max_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = Field(default=None, max_length=8, description="两步验证码（账号开启 2FA 后必填）")


class SendCodeRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(pattern=r"^(register|login|reset)$")


class CodeLoginRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=8)
    totp_code: str | None = Field(default=None, max_length=8, description="两步验证码（账号开启 2FA 后必填）")


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str = Field(min_length=6, max_length=8, description="邮箱验证码")
    new_password: str = Field(min_length=8, max_length=128)


class SessionItem(BaseModel):
    id: str
    device: str | None = None
    ip: str | None = None
    created_time: datetime
    expires_at: datetime
    revoked: bool


class LoginLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ip: str | None = None
    ip_location: str | None = None
    device: str | None = None
    user_agent: str | None = None
    method: str | None = None
    used_2fa: bool = False
    success: bool
    reason: str | None = None
    created_time: datetime
    is_new_device: bool = False


class LoginLogList(BaseModel):
    items: list[LoginLogItem]
    total: int


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


class OAuthProviderOut(BaseModel):
    provider: str
    name: str
    enabled: bool


class OAuthAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    provider_sub: str
    nickname: str | None = None
    avatar: str | None = None
    created_time: datetime


class OAuthExchangeRequest(BaseModel):
    code: str = Field(..., min_length=16, max_length=64)  # 一次性码（OTC）
    totp_code: str | None = Field(default=None, max_length=8, description="两步验证码（账号开启 2FA 后必填）")


class TwoFactorStatus(BaseModel):
    enabled: bool = False


class TwoFactorSetupRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=128)


class TwoFactorSetupOut(BaseModel):
    secret: str
    uri: str
    qr_data_uri: str


class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TwoFactorDisableRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=128)
    code: str = Field(min_length=6, max_length=8)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    created_time: datetime
    updated_time: datetime
    message_count: int = 0


class ConversationList(BaseModel):
    items: list[ConversationOut]
    total: int


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)


class AiChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    stream: bool = False
    reasoning: bool = False
    conversation_id: str | None = Field(default=None, max_length=36, description="所属会话；缺省自动新建会话")


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
    daily_quota: int | None = Field(default=None, ge=0, le=100000, description="普通用户每日 AI 调用上限（0=不限制）")


class AiConfigOut(BaseModel):
    api_key: str | None = None
    api_key_set: bool = False
    base_url: str
    model: str
    daily_quota: int = 10


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


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_time: datetime


class SystemSettingsUpdate(BaseModel):
    site_name: str | None = None
    site_description: str | None = None
    allow_register: bool | None = None
    maintenance_mode: bool | None = None
    default_ai_model: str | None = None
    upload_limit_mb: int | None = Field(default=None, ge=1, le=100)


class SystemSettingsOut(BaseModel):
    site_name: str
    site_description: str
    allow_register: bool
    maintenance_mode: bool
    default_ai_model: str
    upload_limit_mb: int


class AdminLoginLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    uid: str | None = None
    email: str | None = None
    ip: str | None = None
    ip_location: str | None = None
    device: str | None = None
    method: str | None = None
    used_2fa: bool = False
    success: bool
    reason: str | None = None
    created_time: datetime


class AdminLoginLogList(BaseModel):
    items: list[AdminLoginLogItem]
    total: int


class AuditLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_name: str | None = None
    action: str
    resource: str | None = None
    detail: str | None = None
    ip: str | None = None
    success: bool
    created_time: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogItem]
    total: int


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=128)


class NoticeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    is_published: bool
    created_time: datetime
    updated_time: datetime
    published_at: datetime | None = None


class NoticeList(BaseModel):
    items: list[NoticeOut]
    total: int


class NoticeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1)
    is_published: bool = False


class NoticeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = None
    is_published: bool | None = None


class MessageCreate(BaseModel):
    nickname: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=100)
    content: str = Field(..., min_length=1, max_length=500)
    captcha: str = Field(..., min_length=4, max_length=4)


class MessageSubmitOut(BaseModel):
    code: int = 0
    msg: str = "success"
    query_code: str


class MessageQueryIn(BaseModel):
    query_code: str = Field(..., min_length=4, max_length=20)
    email: str | None = Field(default=None, max_length=100)


class MessageQueryOut(BaseModel):
    code: int = 0
    data: dict


class MessageAdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    nickname: str | None = None
    email: str | None = None
    content: str
    query_code: str
    ip: str | None = None
    user_agent: str | None = None
    reply: str | None = None
    replied_at: datetime | None = None
    is_read: bool
    created_time: datetime


class MessageAdminList(BaseModel):
    items: list[MessageAdminOut]
    total: int
    stats: dict


class MessageReplyIn(BaseModel):
    reply: str = Field(..., min_length=1, max_length=2000)


class MessageConfigOut(BaseModel):
    daily_limit: int = 3
    captcha_ttl: int = 120
    query_rate: int = 5


class MessageConfigIn(BaseModel):
    daily_limit: int = Field(3, ge=1, le=100)
    captcha_ttl: int = Field(120, ge=30, le=3600)
    query_rate: int = Field(5, ge=1, le=60)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    token: str
    last_seen: datetime | None = None
    created_time: datetime
    last_payload: dict | None = None


class DeviceList(BaseModel):
    items: list[DeviceOut]
    total: int


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class DeviceUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class TelemetryIn(BaseModel):
    token: str = Field(..., min_length=1, max_length=64)
    data: dict = Field(default_factory=dict)


class TelemetryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    payload: dict
    created_time: datetime


class TelemetryList(BaseModel):
    items: list[TelemetryOut]
    total: int


class VisitLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    uid: str | None = None
    username: str | None = None
    ip: str | None = None
    ip_location: str | None = None
    device: str | None = None
    path: str
    method: str | None = None
    referer: str | None = None
    status_code: int | None = None
    created_time: datetime


class VisitStats(BaseModel):
    total_visits: int
    today_visits: int
    unique_ips: int
    today_unique_ips: int
    page_views: int


class VisitLogList(BaseModel):
    items: list[VisitLogItem]
    total: int
    stats: VisitStats



# ==================== 站内消息系统（IM） ====================

class ImUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: str
    username: str
    nickname: str | None = None
    avatar: str | None = None


class ImMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender_id: str
    kind: str
    content: str
    status: str
    created_time: datetime


class ImLastMessageOut(BaseModel):
    id: str
    sender_id: str
    kind: str
    content: str
    status: str
    created_time: datetime


class ImConversationOut(BaseModel):
    id: str
    other: ImUserOut
    last_message: ImLastMessageOut | None = None
    unread: int = 0
    other_last_read_at: datetime | None = None
    last_message_at: datetime | None = None
    created_time: datetime


class ImConversationList(BaseModel):
    items: list[ImConversationOut]
    total: int


class ImStartIn(BaseModel):
    user_id: str = Field(min_length=8, max_length=40)


class ImSendIn(BaseModel):
    kind: str = Field(default="text", pattern=r"^(text|image)$")
    content: str = Field(min_length=1, max_length=2000)


class ImMessageList(BaseModel):
    items: list[ImMessageOut]
    has_more: bool


class ImUnreadOut(BaseModel):
    total: int


class ImUserSearchOut(BaseModel):
    items: list[ImUserOut]


class ImDecodeTextIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class ImDecodeTextOut(BaseModel):
    matched: bool
    user: ImUserOut | None = None
    message_id: str | None = None
    ts: int | None = None
    note: str | None = None


class BotBroadcastIn(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    reason: str | None = Field(default=None, max_length=200)


class BotDmIn(BaseModel):
    user_id: str = Field(min_length=8, max_length=40)
    content: str = Field(min_length=1, max_length=2000)


class BotHistoryItem(BaseModel):
    id: str
    to: ImUserOut
    content: str
    kind: str
    created_time: datetime


class BotHistoryList(BaseModel):
    items: list[BotHistoryItem]
    total: int

