# Replace your backend/app/api/routes/organizations.py with this final fixed version
# This removes the conflicting Depends() annotations

import uuid
from typing import Any
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    Organization, 
    OrganizationCreate, 
    OrganizationUpdate, 
    OrganizationPublic,
    OrganizationsPublic,
    User,
    UserRole,
    Message,
    UsersPublic
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


def check_group_admin_permission(current_user: User) -> None:
    """Helper function to check if user has group admin permissions"""
    if current_user.role not in [UserRole.GROUP_ADMIN, UserRole.SUPER_ADMIN] and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Group Admin role required."
        )


def check_superuser_permission(current_user: User) -> None:
    """Helper function to check if user is superuser"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions. Superuser role required."
        )


@router.get("/", response_model=OrganizationsPublic)
def read_organizations(
    session: SessionDep, 
    current_user: CurrentUser,
    skip: int = 0, 
    limit: int = 100
) -> Any:
    """
    Retrieve organizations. Super admins see all, users see only their own.
    """
    if current_user.is_superuser or current_user.role == UserRole.SUPER_ADMIN:
        # Super admins can see all organizations
        count_statement = select(func.count()).select_from(Organization)
        count = session.exec(count_statement).one()
        
        statement = select(Organization).offset(skip).limit(limit)
        organizations = session.exec(statement).all()
    else:
        # Regular users can only see their own organization
        if not current_user.organization_id:
            return OrganizationsPublic(data=[], count=0)
        
        organization = session.get(Organization, current_user.organization_id)
        organizations = [organization] if organization else []
        count = len(organizations)
    
    return OrganizationsPublic(data=organizations, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_organization(
    *, 
    session: SessionDep, 
    organization_in: OrganizationCreate,
    current_user: CurrentUser
) -> Any:
    """
    Create new organization. Only super admins can create organizations.
    """
    check_superuser_permission(current_user)
    
    organization = Organization.model_validate(organization_in)
    session.add(organization)
    session.commit()
    session.refresh(organization)
    return organization


@router.get("/{organization_id}", response_model=OrganizationPublic)
def read_organization(
    organization_id: uuid.UUID, 
    session: SessionDep, 
    current_user: CurrentUser
) -> Any:
    """
    Get a specific organization by id.
    """
    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    if (current_user.organization_id != organization_id and 
        not current_user.is_superuser and 
        current_user.role != UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view this organization"
        )
    
    return organization


@router.patch("/{organization_id}", response_model=OrganizationPublic)
def update_organization(
    *,
    session: SessionDep,
    organization_id: uuid.UUID,
    organization_in: OrganizationUpdate,
    current_user: CurrentUser
) -> Any:
    """
    Update organization. Group admins can update their own org, super admins can update any.
    """
    check_group_admin_permission(current_user)
    
    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Check permissions
    if (current_user.organization_id != organization_id and 
        not current_user.is_superuser and 
        current_user.role != UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to update this organization"
        )
    
    organization_data = organization_in.model_dump(exclude_unset=True)
    organization.sqlmodel_update(organization_data)
    session.add(organization)
    session.commit()
    session.refresh(organization)
    return organization


@router.delete("/{organization_id}")
def delete_organization(
    organization_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Message:
    """
    Delete organization. Only super admins can delete organizations.
    """
    check_superuser_permission(current_user)
    
    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    session.delete(organization)
    session.commit()
    return Message(message="Organization deleted successfully")


@router.get("/{organization_id}/users", response_model=UsersPublic)
def get_organization_users(
    organization_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all users in an organization. Group admins can see their org users.
    """
    check_group_admin_permission(current_user)
    
    # Check permissions
    if (current_user.organization_id != organization_id and 
        not current_user.is_superuser and 
        current_user.role != UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to view organization users"
        )
    
    statement = select(User).where(User.organization_id == organization_id).offset(skip).limit(limit)
    users = session.exec(statement).all()
    
    count_statement = select(func.count()).select_from(User).where(User.organization_id == organization_id)
    count = session.exec(count_statement).one()
    
    return UsersPublic(data=users, count=count)


@router.post("/{organization_id}/join")
def join_organization(
    organization_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Message:
    """
    Allow user to join an organization.
    """
    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not organization.is_active:
        raise HTTPException(status_code=400, detail="Organization is not active")
    
    current_user.organization_id = organization_id
    session.add(current_user)
    session.commit()
    
    return Message(message=f"Successfully joined {organization.name}")


@router.post("/{organization_id}/promote/{user_id}")
def promote_user_to_admin(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser
) -> Message:
    """
    Promote user to group admin within the organization.
    """
    check_group_admin_permission(current_user)
    
    # Check permissions - only group admins or super admins can promote
    if (current_user.organization_id != organization_id and 
        not current_user.is_superuser and 
        current_user.role != UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to promote users in this organization"
        )
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.organization_id != organization_id:
        raise HTTPException(
            status_code=400, 
            detail="User is not a member of this organization"
        )
    
    user.role = UserRole.GROUP_ADMIN
    session.add(user)
    session.commit()
    
    return Message(message=f"User {user.email} promoted to Group Admin")