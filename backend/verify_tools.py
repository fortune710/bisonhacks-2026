import asyncio
from ai.tools.snap_eligibility import SNAPEligibilityInput, check_snap_eligibility
from ai.tools.snap_rag import SNAPRAGInput, search_snap_info
from ai.tools.food_locator import FoodLocatorInput, find_food_resources

async def verify_snap_eligibility():
    print("\n--- Verifying SNAP Eligibility Tool ---")
    data = SNAPEligibilityInput(household_size=2, gross_monthly_income=1500, is_elderly_or_disabled=False)
    result = check_snap_eligibility(data)
    print(f"Input: Household Size 2, Income $1500")
    print(f"Eligible: {result.is_eligible}")
    print(f"Reasoning: {result.reasoning}")

async def verify_snap_rag():
    print("\n--- Verifying SNAP RAG Tool ---")
    data = SNAPRAGInput(question="How do I apply for SNAP in Texas?")
    result = search_snap_info(data)
    print(f"Question: {data.question}")
    print(f"Answer Summary: {result.answer[:100]}...")
    print(f"Sources: {result.sources}")

async def verify_food_locator():
    print("\n--- Verifying Food Locator Tool ---")
    data = FoodLocatorInput(zip_code="20706")
    result = await find_food_resources(data)
    print(f"Location: {data.zip_code}")
    print(f"Found {len(result.resources)} resources.")
    for resource in result.resources:
        print(f"Resource: {resource.name} - {resource.address}\n")

async def main():
    await verify_snap_eligibility()
    await verify_snap_rag()
    await verify_food_locator()

if __name__ == "__main__":
    asyncio.run(main())
