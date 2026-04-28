from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    PAYSTUB = "paystub"
    W2 = "w2"
    OFFER_LETTER = "offer_letter"
    EMPLOYMENT_VERIFICATION = "employment_verification"
    TAX_RETURN = "tax_return"
    UNKNOWN = "unknown"


class DocumentClassification(BaseModel):
    document_type: DocumentType
    employee_name: str | None = None
    employer_name: str | None = None
    confidence: float = 0.0


class PayDataExtraction(BaseModel):
    pay_period_start: str | None = None
    pay_period_end: str | None = None
    pay_frequency: str | None = None
    gross_pay_period: float | None = None
    gross_pay_ytd: float | None = None
    hourly_rate: float | None = None
    hours_worked: float | None = None
    annual_salary: float | None = None
    stated_annual_wages: float | None = None


class SalaryBreakdown(BaseModel):
    document_index: int
    document_type: str
    annual_salary: float | None = None
    confidence: float = 0.0
    methodology: str = ""


class SalaryCalculation(BaseModel):
    annual_salary: float | None = None
    confidence: float = 0.0
    methodology: str = ""
    employee_name: str | None = None
    employer_name: str | None = None
    breakdown: list[SalaryBreakdown] = Field(default_factory=list)
