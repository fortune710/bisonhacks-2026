import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "AIzaSyDaLP2eQcb9Ut451_cWZJMRsXVRDIUXQiM" });

export interface SnapResource {
  name: string;
  address: string;
  distance?: string;
  url?: string;
  type: 'office' | 'grocery';
}

export interface EligibilityResult {
  isEligible: boolean;
  reason: string;
  estimatedBenefit?: string;
}

export const getSnapResources = async (zipcode: string, state: string) => {
  const model = "gemini-2.5-flash";

  const prompt = `Find the following resources near zipcode ${zipcode} in ${state}:
  1. The closest SNAP (Supplemental Nutrition Assistance Program) or Social Services office. Provide address and phone.
  2. 3 budget-friendly grocery stores (like Aldi, Walmart, or local discount markets) that accept SNAP/EBT.
  3. 3 local food pantries or food banks with their addresses and hours if available.
  
  IMPORTANT: For every address found, format it as a clickable Markdown link that opens in Google Maps using this format: [Address](https://www.google.com/maps/search/?api=1&query=URL_ENCODED_ADDRESS).
  
  Return the information in a clear Markdown format. 
  Please separate the sections with these exact markers:
  [SNAP_OFFICE]
  [GROCERY_STORES]
  [FOOD_PANTRIES]`;

  try {
    const response = await ai.models.generateContent({
      model: model,
      contents: prompt,
      config: {
        tools: [{ googleMaps: {} }],
      },
    });

    return {
      text: response.text,
      groundingChunks: response.candidates?.[0]?.groundingMetadata?.groundingChunks || []
    };
  } catch (error) {
    console.error("Error fetching SNAP resources:", error);
    throw error;
  }
};

export const checkEligibility = async (familySize: number, monthlyIncome: number, state: string) => {
  // Basic federal logic (simplified)
  // 2024 Federal Poverty Level (FPL) for 48 states:
  // 1: $1,215/mo (100%), SNAP limit is usually 130% gross income
  const fplBase = 15060 / 12; // 2024 FPL for 1 person
  const fplIncrement = 5380 / 12; // 2024 FPL increment per person

  const grossIncomeLimit = (fplBase + (familySize - 1) * fplIncrement) * 1.3;

  const isEligible = monthlyIncome <= grossIncomeLimit;

  return {
    isEligible,
    limit: grossIncomeLimit,
    reason: isEligible
      ? `Your income of $${monthlyIncome} is below the estimated gross income limit of $${Math.round(grossIncomeLimit)} for a family of ${familySize} in ${state}.`
      : `Your income of $${monthlyIncome} exceeds the estimated gross income limit of $${Math.round(grossIncomeLimit)} for a family of ${familySize} in ${state}.`
  };
};
