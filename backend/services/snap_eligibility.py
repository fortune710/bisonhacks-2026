from dataclasses import dataclass, asdict

FPL_NET_LIMIT = {
    1: 1305, 2: 1763, 3: 2221, 4: 2680,
    5: 3138, 6: 3596, 7: 4055, 8: 4513
}

FPL_GROSS_BASE = {
    1: 1696, 2: 2292, 3: 2888, 4: 3483,
    5: 4079, 6: 4675, 7: 5271, 8: 5867
}

GROSS_INCREMENT = 596
NET_INCREMENT = 459


@dataclass
class SnapEligibility:
    state: str
    household_size: int
    monthly_income: float
    has_elderly_or_disabled: bool
    medical_expenses: float
    dependent_care_costs: float
    rent_or_mortgage: float

    STATE_GROSS_LIMIT_PCTS = {
        "AL": 130, "AK": 200, "AZ": 185, "AR": 130,
        "CA": 200, "CO": 200, "CT": 200, "DE": 200,
        "DC": 200, "FL": 200, "GA": 130, "HI": 200,
        "ID": 130, "IL": 165, "IN": 130, "IA": 160,
        "KS": 130, "KY": 200, "LA": 200, "ME": 200,
        "MD": 200, "MA": 200, "MI": 200, "MN": 200,
        "MS": 130, "MO": 200, "MT": 200, "NE": 165,
        "NV": 200, "NH": 200, "NJ": 185, "NM": 200,
        "NY": 200, "NC": 200, "ND": 200, "OH": 130,
        "OK": 130, "OR": 200, "PA": 200, "RI": 185,
        "SC": 130, "SD": 130, "TN": 130, "TX": 165,
        "UT": 130, "VT": 185, "VA": 200, "WA": 200,
        "WV": 200, "WI": 200, "WY": 130
    }

    def get_fpl_limits(self):
        size = min(self.household_size, 8)
        gross_base = FPL_GROSS_BASE[size]
        net_limit = FPL_NET_LIMIT[size]

        if self.household_size > 8:
            extra = self.household_size - 8
            gross_base += extra * GROSS_INCREMENT
            net_limit += extra * NET_INCREMENT

        return gross_base, net_limit

    def compute_gross_limit(self):
        base_gross, _ = self.get_fpl_limits()
        pct = self.STATE_GROSS_LIMIT_PCTS.get(self.state.upper(), 130)
        return base_gross * (pct / 130)

    def compute_net_income(self):
        standard_deduction = 209 if self.household_size <= 3 else 257
        medical_deduction = (
            max(0, self.medical_expenses - 35)
            if self.has_elderly_or_disabled
            else 0
        )

        adjusted_income = (
            self.monthly_income
            - standard_deduction
            - self.dependent_care_costs
            - medical_deduction
        )

        shelter_deduction = max(
            0,
            self.rent_or_mortgage - 0.5 * adjusted_income
        )

        net_income = max(adjusted_income - shelter_deduction, 0)

        return {
            "net_income": net_income,
            "standard_deduction": standard_deduction,
            "medical_deduction": medical_deduction,
            "dependent_care_deduction": self.dependent_care_costs,
            "shelter_deduction": shelter_deduction
        }

    def evaluate(self):
        gross_limit = self.compute_gross_limit()
        _, net_limit = self.get_fpl_limits()

        gross_required = not self.has_elderly_or_disabled
        gross_passed = (
            True if not gross_required
            else self.monthly_income <= gross_limit
        )

        net_data = self.compute_net_income()
        net_passed = net_data["net_income"] <= net_limit

        eligible = gross_passed and net_passed

        if eligible:
            summary = "Household passed required income tests."
        elif not gross_passed:
            summary = "Household exceeds gross income limit."
        else:
            summary = "Household exceeds net income limit after deductions."

        return {
            "eligible": eligible,
            "gross_test": {
                "required": gross_required,
                "limit": round(gross_limit, 2),
                "actual": self.monthly_income,
                "passed": gross_passed
            },
            "net_test": {
                "limit": net_limit,
                "actual": round(net_data["net_income"], 2),
                "passed": net_passed
            },
            "deductions": {
                "standard": net_data["standard_deduction"],
                "dependent_care": net_data["dependent_care_deduction"],
                "medical": net_data["medical_deduction"],
                "shelter": round(net_data["shelter_deduction"], 2)
            },
            "reason_summary": summary
        }