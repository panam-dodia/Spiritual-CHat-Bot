# Replace your backend/app/models.py with this corrected version
# This fixes the Relationship() cascade_delete issue

import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Add this enum for user roles
class UserRole(str, Enum):
    GROUP_ADMIN = "group_admin"
    GROUP_USER = "group_user"
    SUPER_ADMIN = "super_admin"


# Organization models - Fixed EmailStr issue
class OrganizationBase(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    website: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)  # Changed from EmailStr to str
    is_active: bool = True


class OrganizationCreate(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    website: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = Field(default=None, max_length=255)  # Keep EmailStr for validation


class OrganizationUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    website: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = Field(default=None, max_length=255)  # Keep EmailStr for validation


class Organization(OrganizationBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - Fixed: removed cascade_delete
    users: List["User"] = Relationship(back_populates="organization")
    spiritual_documents: List["SpiritualDocument"] = Relationship(back_populates="organization")


class OrganizationPublic(SQLModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    website: str | None = None
    contact_email: str | None = None  # This will be str in responses
    is_active: bool
    created_at: datetime


# Updated User models - Fixed EmailStr issue for database
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)  # This is fine for base/API models
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    
    # New fields for spiritual chatbot
    role: UserRole = Field(default=UserRole.GROUP_USER)
    organization_id: uuid.UUID | None = Field(default=None, foreign_key="organization.id")


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)
    organization_id: uuid.UUID | None = None  # Optional during registration


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model - Use str for email to avoid SQLAlchemy issues
class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)  # Changed from EmailStr to str
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = Field(default=UserRole.GROUP_USER)
    organization_id: uuid.UUID | None = Field(default=None, foreign_key="organization.id")
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships - Fixed: removed cascade_delete
    items: list["Item"] = Relationship(back_populates="owner")
    organization: Organization | None = Relationship(back_populates="users")
    uploaded_documents: List["SpiritualDocument"] = Relationship(back_populates="uploader")


# Properties to return via API, id is always required
class UserPublic(SQLModel):
    id: uuid.UUID
    email: str  # Will be validated as EmailStr in API but stored as str
    is_active: bool
    is_superuser: bool
    full_name: str | None = None
    role: UserRole
    organization_id: uuid.UUID | None = None
    created_at: datetime
    organization: OrganizationPublic | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Existing Item models (unchanged except for relationship)
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    
    # Relationships - Fixed: removed ondelete parameter
    owner: User | None = Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# New model for spiritual documents
class SpiritualDocumentBase(SQLModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    document_type: str = Field(max_length=100)  # "bible", "quran", "buddhist", etc.
    file_path: str | None = Field(default=None)
    chunk_count: int = Field(default=0)
    is_active: bool = True


class SpiritualDocumentCreate(SpiritualDocumentBase):
    organization_id: uuid.UUID


class SpiritualDocumentUpdate(SpiritualDocumentBase):
    name: str | None = Field(default=None, max_length=255)
    document_type: str | None = Field(default=None, max_length=100)


class SpiritualDocument(SpiritualDocumentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organization.id", nullable=False)
    uploaded_by: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    organization: Organization = Relationship(back_populates="spiritual_documents")
    uploader: User = Relationship(back_populates="uploaded_documents")


class SpiritualDocumentPublic(SpiritualDocumentBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    uploaded_by: uuid.UUID
    created_at: datetime


# Helper models for API responses
class OrganizationsPublic(SQLModel):
    data: list[OrganizationPublic]
    count: int


class SpiritualDocumentsPublic(SQLModel):
    data: list[SpiritualDocumentPublic]
    count: int


# Existing models (unchanged)
class Message(SQLModel):
    message: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)