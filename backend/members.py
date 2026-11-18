
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db
from auth import get_current_user, require_roles


router = APIRouter(
    prefix="/members",
    tags=["Members"]
)


# =====================================
# REGISTER MEMBER
# Librarian and Admin only
# =====================================

@router.post(
    "/",
    response_model=schemas.MemberResponse,
    status_code=201
)
def create_member(
    request: schemas.MemberCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin", "librarian")
    )
):

    existing_member = db.query(models.Member).filter(
        models.Member.email == str(request.email)
    ).first()

    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="Email already registered."
        )

    new_member = models.Member(
        name=request.name,
        email=str(request.email),
        phone=request.phone
    )

    try:
        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        return new_member

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to register member."
        )


# =====================================
# GET ALL MEMBERS
# Librarian and Admin only
# =====================================

@router.get(
    "/",
    response_model=list[schemas.MemberResponse]
)
def get_members(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin", "librarian")
    )
):

    return db.query(models.Member).all()


# =====================================
# GET MEMBER BY ID
# Student: Own details only
# Librarian/Admin: Any member
# =====================================

@router.get(
    "/{member_id}",
    response_model=schemas.MemberResponse
)
def get_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Student can access only their own membership
    if current_user.role == "student":

        if current_user.member_id is None:
            raise HTTPException(
                status_code=403,
                detail="Your account is not linked to a library membership."
            )

        if current_user.member_id != member_id:
            raise HTTPException(
                status_code=403,
                detail="You can view only your own membership details."
            )

    elif current_user.role not in ["admin", "librarian"]:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission."
        )

    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    return member


# =====================================
# UPDATE MEMBER
# Librarian and Admin only
# =====================================

@router.put(
    "/{member_id}",
    response_model=schemas.MemberResponse
)
def update_member(
    member_id: int,
    request: schemas.MemberUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin", "librarian")
    )
):

    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    data = request.model_dump(exclude_unset=True)

    if "email" in data and data["email"] is not None:

        email = str(data["email"])

        existing = db.query(models.Member).filter(
            models.Member.email == email,
            models.Member.id != member_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered."
            )

        # Keep linked login account email synchronized
        linked_user = db.query(models.User).filter(
            models.User.member_id == member_id
        ).first()

        if linked_user:
            duplicate_user = db.query(models.User).filter(
                models.User.email == email,
                models.User.id != linked_user.id
            ).first()

            if duplicate_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already belongs to another user account."
                )

            linked_user.email = email

        member.email = email

    for field in ["name", "phone"]:
        if field in data and data[field] is not None:
            setattr(member, field, data[field])

    try:
        db.commit()
        db.refresh(member)

        return member

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update member."
        )


# =====================================
# DELETE MEMBER
# Admin only
# =====================================

@router.delete("/{member_id}")
def delete_member(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        require_roles("admin")
    )
):

    member = db.query(models.Member).filter(
        models.Member.id == member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member not found."
        )

    history = db.query(models.BorrowRecord).filter(
        models.BorrowRecord.member_id == member_id
    ).first()

    if history:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a member with borrowing history."
        )

    # Remove linked login account first
    linked_user = db.query(models.User).filter(
        models.User.member_id == member_id
    ).first()

    try:
        if linked_user:
            db.delete(linked_user)

        db.delete(member)
        db.commit()

        return {
            "message": "Member deleted successfully."
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete member."
        )
