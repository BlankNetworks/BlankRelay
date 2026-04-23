from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


def normalize_blank_id(value: str) -> str:
    return value.strip().lower()

class PresenceHeartbeatRequest(BaseModel):
    blankID: str
    deviceID: str

    @field_validator("blankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)


class PresenceDeviceOut(BaseModel):
    deviceID: str
    isOnline: bool
    lastSeenAt: str | None = None


class PresenceResponse(BaseModel):
    success: bool
    blankID: str
    isOnline: bool
    lastSeenAt: str | None = None
    devices: list[PresenceDeviceOut]


class UserProfileResponse(BaseModel):
    success: bool
    blankID: str
    displayName: str
    profilePhotoURL: str | None = None
    profileThumbURL: str | None = None
    profilePhotoVersion: str | None = None


class ProfilePhotoUploadResponse(BaseModel):
    success: bool
    blankID: str
    profilePhotoURL: str
    message: str


class DeviceLinkRequestCreate(BaseModel):
    blankID: str
    primaryDeviceID: str


class DeviceLinkRequestResponse(BaseModel):
    success: bool
    blankID: str
    linkCode: str
    expiresAt: str


class DeviceLinkCompleteRequest(BaseModel):
    blankID: str
    linkCode: str
    deviceID: str
    deviceLabel: str | None = None
    identityKeyBase64: str
    identitySigningPublicKeyBase64: str


class DeviceLinkCompleteResponse(BaseModel):
    success: bool
    blankID: str
    deviceID: str
    message: str


class UserDeviceOut(BaseModel):
    blankID: str
    deviceID: str
    deviceLabel: str | None = None
    identityKeyBase64: str
    identitySigningPublicKeyBase64: str
    isPrimary: bool
    isActive: bool


class UserDevicesResponse(BaseModel):
    success: bool
    blankID: str
    devices: list[UserDeviceOut]


class IDCheckResponse(BaseModel):
    blankID: str
    available: bool


class RegisterRequest(BaseModel):
    blankID: str = Field(min_length=3, max_length=32)
    displayName: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=3, max_length=255)

    identityKeyBase64: str
    identitySigningPublicKeyBase64: str
    ownershipSignatureBase64: str
    nonce: str = Field(min_length=1, max_length=128)

    @field_validator("blankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)


class RegisterResponse(BaseModel):
    success: bool
    blankID: str
    emailAddress: str
    message: str


class LoginRequest(BaseModel):
    blankID: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=255)

    @field_validator("blankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)


class LoginResponse(BaseModel):
    success: bool
    blankID: str
    message: str


class DeleteUserResponse(BaseModel):
    success: bool
    blankID: str
    message: str


class SignedPrekey(BaseModel):
    id: str
    keyID: int
    publicKeyBase64: str
    signatureBase64: str
    createdAt: datetime


class OneTimePrekeyIn(BaseModel):
    id: str
    keyID: int
    publicKeyBase64: str
    createdAt: datetime
    isUsed: bool = False


class OneTimePrekeyOut(BaseModel):
    id: str
    keyID: int
    publicKeyBase64: str
    createdAt: datetime
    isUsed: bool


class PrekeyBundleUploadRequest(BaseModel):
    blankID: str
    deviceID: str
    identityKeyBase64: str
    identitySigningPublicKeyBase64: str
    ownershipSignatureBase64: str
    signedPrekey: SignedPrekey
    oneTimePrekeys: list[OneTimePrekeyIn]
    generatedAt: datetime

    @field_validator("blankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)


class PrekeyBundleUploadResponse(BaseModel):
    success: bool
    blankID: str
    deviceID: str
    message: str


class PrekeyBundleResponseBundle(BaseModel):
    blankID: str
    deviceID: str
    identityKeyBase64: str
    identitySigningPublicKeyBase64: str
    ownershipSignatureBase64: str
    signedPrekey: dict
    oneTimePrekeys: list[dict]
    generatedAt: datetime


class PrekeyBundleFetchResponse(BaseModel):
    success: bool
    blankID: str
    bundle: PrekeyBundleResponseBundle
    message: str


class PrekeyBundleUploadResponse(BaseModel):
    success: bool
    blankID: str
    deviceID: str
    message: str


class PrekeyBundleFetchResponse(BaseModel):
    success: bool
    blankID: str
    bundle: PrekeyBundleResponseBundle
    message: str


class EnvelopePayload(BaseModel):
    id: str
    type: str
    senderBlankID: str = Field(min_length=3, max_length=32)
    senderDeviceID: str = Field(min_length=1, max_length=128)
    recipientBlankID: str = Field(min_length=3, max_length=32)
    recipientDeviceID: Optional[str] = None
    conversationID: str
    timestamp: datetime
    ratchetHeaderType: Optional[str] = None
    ratchetHeaderBase64: Optional[str] = None
    nonceBase64: Optional[str] = None
    ciphertextBase64: str
    protocolVersion: int = 1

    @field_validator("senderBlankID", "recipientBlankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)


class EnvelopeSendRequest(BaseModel):
    envelope: EnvelopePayload


class EnvelopeSendResponse(BaseModel):
    success: bool
    envelopeID: str
    message: str


class EnvelopeBatchSendRequest(BaseModel):
    envelopes: List[EnvelopePayload]


class EnvelopeBatchSendResponse(BaseModel):
    success: bool
    envelopeIDs: List[str]
    processedCount: int
    message: str


class EnvelopeResponseItem(BaseModel):
    id: str
    type: str
    senderBlankID: str
    senderDeviceID: str
    recipientBlankID: str
    recipientDeviceID: Optional[str]
    conversationID: str
    timestamp: datetime
    ratchetHeaderType: Optional[str]
    ratchetHeaderBase64: Optional[str]
    nonceBase64: Optional[str]
    ciphertextBase64: str
    protocolVersion: int


class EnvelopePollResponse(BaseModel):
    success: bool
    recipientBlankID: str
    envelopes: List[EnvelopeResponseItem]


class ReceiptRequest(BaseModel):
    envelopeIDs: List[str]
    recipientBlankID: str
    recipientDeviceID: str

    @field_validator("recipientBlankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)



class ReceiptResponse(BaseModel):
    success: bool
    processedCount: int
    message: str
