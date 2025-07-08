"""
TPA management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin, TokenData
from app.core.audit import audit_endpoint
from app.schemas.tpa import TPAOut, TPAUpdate
from app.crud.tpa import tpa_crud

router = APIRouter()

@router.get("/me", response_model=TPAOut)
@audit_endpoint(action="get_current_tpa", resource_type="tpa", severity="low")
async def get_current_tpa(
    current_user: TokenData = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get current user's TPA"""
    tpa = await tpa_crud.get(db, id=current_user.tpa_id)
    if not tpa:
        raise HTTPException(status_code=404, detail="TPA not found")
    
    return TPAOut.from_orm(tpa)