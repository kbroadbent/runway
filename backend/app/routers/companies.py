from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Company
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyRead

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    return db.query(Company).all()


@router.post("", response_model=CompanyRead, status_code=201)
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    company = Company(**data.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyRead)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyRead)
def update_company(company_id: int, data: CompanyUpdate, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(company, key, value)
    db.commit()
    db.refresh(company)
    return company
