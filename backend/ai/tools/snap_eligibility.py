from pydantic import BaseModel, Field

class SNAPEligibilityInput(BaseModel):
    household_size: int = Field(..., description="Number of people in the household")
    gross_monthly_income: float = Field(..., description="Total monthly income before taxes")
    is_elderly_or_disabled: bool = Field(False, description="Whether any household member is 60+ or disabled")

class SNAPEligibilityOutput(BaseModel):
    is_eligible: bool
    reasoning: str
    max_income_limit: float

def check_snap_eligibility(input_data: SNAPEligibilityInput) -> SNAPEligibilityOutput:
    """
    Determines SNAP eligibility based on household size and income.
    Source: Typical 2024-2025 Federal SNAP guidelines (130% FPL for gross income).
    """
    # Gross monthly income limits (130% of Poverty Level) for 2024-2025
    income_limits = {
        1: 1580,
        2: 2137,
        3: 2694,
        4: 3250,
        5: 3807,
        6: 4364,
        7: 4921,
        8: 5478
    }
    
    limit = income_limits.get(input_data.household_size, 5478 + (input_data.household_size - 8) * 557)
    
    # If elderly or disabled, the gross income test might not apply or be different, 
    # but for this tool we'll keep it simple and notify the user.
    is_eligible = input_data.gross_monthly_income <= limit
    
    reasoning = (
        f"Based on a household size of {input_data.household_size}, the gross monthly income limit is ${limit}. "
        f"Your income of ${input_data.gross_monthly_income} is {'within' if is_eligible else 'above'} this limit."
    )
    
    if input_data.is_elderly_or_disabled and not is_eligible:
        reasoning += " However, since you have elderly or disabled members, you may still qualify via the net income test. Please contact your local SNAP office."

    return SNAPEligibilityOutput(
        is_eligible=is_eligible,
        reasoning=reasoning,
        max_income_limit=limit
    )
