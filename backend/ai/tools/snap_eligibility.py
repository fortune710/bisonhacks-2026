from pydantic import BaseModel, Field
from services.snap_eligibility import SnapEligibility

class SNAPEligibilityInput(BaseModel):
    state: str = Field(..., description="Two-letter state code (e.g., 'TX', 'CA')")
    household_size: int = Field(..., description="Number of people in the household")
    gross_monthly_income: float = Field(..., description="Total monthly income before taxes")
    is_elderly_or_disabled: bool = Field(False, description="Whether any household member is 60+ or disabled")
    medical_expenses: float = Field(0.0, description="Monthly medical expenses for elderly or disabled members")
    dependent_care_costs: float = Field(0.0, description="Monthly costs for childcare or adult dependent care")
    rent_or_mortgage: float = Field(0.0, description="Monthly rent or mortgage payment")

class SNAPEligibilityOutput(BaseModel):
    is_eligible: bool
    reasoning: str
    max_income_limit: float

def check_snap_eligibility(input_data: SNAPEligibilityInput) -> SNAPEligibilityOutput:
    """
    Determines SNAP eligibility based on household size, income, and deductions using the SnapEligibility service.
    """
    service = SnapEligibility(
        state=input_data.state,
        household_size=input_data.household_size,
        monthly_income=input_data.gross_monthly_income,
        has_elderly_or_disabled=input_data.is_elderly_or_disabled,
        medical_expenses=input_data.medical_expenses,
        dependent_care_costs=input_data.dependent_care_costs,
        rent_or_mortgage=input_data.rent_or_mortgage
    )
    
    result = service.evaluate()
    
    return SNAPEligibilityOutput(
        is_eligible=result["eligible"],
        reasoning=result["reason_summary"],
        max_income_limit=result["gross_test"]["limit"]
    )
