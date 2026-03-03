"""
Government schemes database.

Contains information about major Indian government schemes.
This can be stored in DynamoDB in production, but for now we use an embedded database.
"""

# Major Indian Government Schemes Database
SCHEMES_DATABASE = [
    {
        "name": "Pradhan Mantri Awas Yojana (PMAY)",
        "description": "Housing scheme for economically weaker sections, providing financial assistance for house construction or purchase.",
        "eligibility": [
            "Age 18+",
            "Annual income < ₹3 lakh (EWS) or ₹6 lakh (LIG)",
            "No pucca house in name of any family member",
            "Must not have availed any central/state housing scheme"
        ],
        "apply_steps": [
            "Visit PMAY website (pmaymis.gov.in)",
            "Register with Aadhaar number",
            "Fill application form with family details",
            "Upload required documents",
            "Submit application and note reference number",
            "Track application status online"
        ],
        "link": "https://pmaymis.gov.in/",
        "categories": ["housing", "financial_assistance"],
        "income_limit": 600000,
        "age_min": 18
    },
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "description": "Direct income support scheme for farmers, providing ₹6,000 per year in three installments.",
        "eligibility": [
            "Farmer with cultivable land",
            "Age 18+",
            "Landholding in own name",
            "Not a government employee or income tax payer"
        ],
        "apply_steps": [
            "Visit PM-KISAN portal (pmkisan.gov.in)",
            "Click 'Farmers Corner' → 'New Farmer Registration'",
            "Enter Aadhaar number and bank details",
            "Submit land records",
            "Complete registration",
            "Receive installments directly in bank account"
        ],
        "link": "https://pmkisan.gov.in/",
        "categories": ["farmer", "financial_assistance"],
        "occupation_match": ["Farmer"],
        "income_limit": None
    },
    {
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "description": "Health insurance scheme providing coverage of ₹5 lakh per family per year for secondary and tertiary care hospitalization.",
        "eligibility": [
            "Annual income < ₹5 lakh",
            "No existing health insurance",
            "Family size: up to 5 members",
            "Must be listed in SECC database"
        ],
        "apply_steps": [
            "Check eligibility on PM-JAY website",
            "Verify name in SECC database",
            "Visit nearest Common Service Centre (CSC)",
            "Submit Aadhaar and family details",
            "Receive Ayushman Bharat card",
            "Use card at empaneled hospitals"
        ],
        "link": "https://pmjay.gov.in/",
        "categories": ["health", "insurance"],
        "income_limit": 500000
    },
    {
        "name": "Pradhan Mantri Ujjwala Yojana (PMUY)",
        "description": "Free LPG connection scheme for women from below poverty line (BPL) households.",
        "eligibility": [
            "Woman above 18 years",
            "BPL household",
            "No existing LPG connection",
            "Valid BPL ration card"
        ],
        "apply_steps": [
            "Visit nearest LPG distributor",
            "Submit BPL ration card and Aadhaar",
            "Fill application form",
            "Pay security deposit (refundable)",
            "Receive LPG connection and cylinder",
            "Get first refill subsidy"
        ],
        "link": "https://www.pmuy.gov.in/",
        "categories": ["utilities", "women"],
        "income_limit": None,
        "age_min": 18
    },
    {
        "name": "Pradhan Mantri Shram Yogi Maan-Dhan (PM-SYM)",
        "description": "Pension scheme for unorganized sector workers providing ₹3,000 monthly pension after 60 years.",
        "eligibility": [
            "Age 18-40 years",
            "Unorganized sector worker",
            "Monthly income < ₹15,000",
            "Not covered under any other pension scheme"
        ],
        "apply_steps": [
            "Visit nearest Common Service Centre (CSC)",
            "Submit Aadhaar, bank account details",
            "Pay monthly contribution (₹55-200)",
            "Complete enrollment",
            "Receive pension after 60 years"
        ],
        "link": "https://maandhan.in/",
        "categories": ["pension", "unorganized_sector"],
        "income_limit": 15000,
        "age_min": 18,
        "age_max": 40
    },
    {
        "name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
        "description": "Maternity benefit scheme providing ₹5,000 in three installments to pregnant and lactating mothers.",
        "eligibility": [
            "Pregnant or lactating mother",
            "Age 19+",
            "First living child",
            "Not a government employee"
        ],
        "apply_steps": [
            "Visit Anganwadi Centre or Health Centre",
            "Submit Aadhaar, bank account details",
            "Complete MCP card registration",
            "Receive first installment after registration",
            "Receive second installment after 6 months",
            "Receive third installment after child birth"
        ],
        "link": "https://wcd.nic.in/schemes/pradhan-mantri-matru-vandana-yojana",
        "categories": ["maternity", "women"],
        "age_min": 19
    },
    {
        "name": "Pradhan Mantri Kisan Maan Dhan Yojana (PM-KMY)",
        "description": "Pension scheme for small and marginal farmers providing ₹3,000 monthly pension after 60 years.",
        "eligibility": [
            "Age 18-40 years",
            "Small or marginal farmer",
            "Landholding up to 2 hectares",
            "Not covered under any other pension scheme"
        ],
        "apply_steps": [
            "Visit nearest Common Service Centre (CSC)",
            "Submit Aadhaar, land records, bank details",
            "Pay monthly contribution",
            "Complete enrollment",
            "Receive pension after 60 years"
        ],
        "link": "https://maandhan.in/",
        "categories": ["pension", "farmer"],
        "occupation_match": ["Farmer"],
        "age_min": 18,
        "age_max": 40
    },
    {
        "name": "Pradhan Mantri Mudra Yojana (PMMY)",
        "description": "Micro finance scheme providing loans up to ₹10 lakh for small businesses and entrepreneurs.",
        "eligibility": [
            "Age 18+",
            "Non-farm income generating activity",
            "Micro, small, or medium enterprise",
            "Valid business plan"
        ],
        "apply_steps": [
            "Visit nearest bank or financial institution",
            "Submit business plan and documents",
            "Apply for MUDRA loan",
            "Get loan approval",
            "Receive loan disbursement",
            "Repay as per terms"
        ],
        "link": "https://www.mudra.org.in/",
        "categories": ["business", "loan"],
        "age_min": 18
    },
    {
        "name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "description": "Life insurance scheme providing ₹2 lakh coverage for death due to any cause at premium of ₹436 per year.",
        "eligibility": [
            "Age 18-50 years",
            "Bank account holder",
            "Aadhaar linked bank account",
            "Consent to auto-debit"
        ],
        "apply_steps": [
            "Visit your bank branch",
            "Fill enrollment form",
            "Provide Aadhaar and bank account details",
            "Give consent for auto-debit",
            "Premium auto-debited annually",
            "Coverage active immediately"
        ],
        "link": "https://www.jansuraksha.gov.in/",
        "categories": ["insurance", "life"],
        "age_min": 18,
        "age_max": 50
    },
    {
        "name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "description": "Accident insurance scheme providing ₹2 lakh coverage for accidental death/disability at premium of ₹20 per year.",
        "eligibility": [
            "Age 18-70 years",
            "Bank account holder",
            "Aadhaar linked bank account",
            "Consent to auto-debit"
        ],
        "apply_steps": [
            "Visit your bank branch",
            "Fill enrollment form",
            "Provide Aadhaar and bank account details",
            "Give consent for auto-debit",
            "Premium auto-debited annually",
            "Coverage active immediately"
        ],
        "link": "https://www.jansuraksha.gov.in/",
        "categories": ["insurance", "accident"],
        "age_min": 18,
        "age_max": 70
    },
    {
        "name": "Pradhan Mantri Gramin Awaas Yojana (PMGAY)",
        "description": "Rural housing scheme providing financial assistance for construction of pucca houses for rural poor.",
        "eligibility": [
            "Rural household",
            "Annual income < ₹3 lakh",
            "No pucca house",
            "Must be listed in SECC database"
        ],
        "apply_steps": [
            "Check SECC database listing",
            "Visit Gram Panchayat office",
            "Submit application with documents",
            "Get approval from District Collector",
            "Receive financial assistance",
            "Complete house construction"
        ],
        "link": "https://pmayg.nic.in/",
        "categories": ["housing", "rural"],
        "income_limit": 300000
    },
    {
        "name": "Pradhan Mantri Kisan Credit Card (PM-KCC)",
        "description": "Credit card scheme for farmers providing flexible credit for agricultural and allied activities.",
        "eligibility": [
            "Farmer with cultivable land",
            "Age 18+",
            "Land records",
            "Bank account"
        ],
        "apply_steps": [
            "Visit nearest bank branch",
            "Submit land records and Aadhaar",
            "Fill KCC application form",
            "Get credit limit approval",
            "Receive KCC card",
            "Use for agricultural expenses"
        ],
        "link": "https://www.pmkisan.gov.in/",
        "categories": ["credit", "farmer"],
        "occupation_match": ["Farmer"],
        "age_min": 18
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "description": "Crop insurance scheme providing financial support to farmers in case of crop loss due to natural calamities.",
        "eligibility": [
            "Farmer with cultivable land",
            "Crop cultivation",
            "Bank account",
            "Aadhaar linked"
        ],
        "apply_steps": [
            "Visit nearest bank or insurance company",
            "Submit land records and crop details",
            "Pay premium (subsidized)",
            "Complete enrollment",
            "Get insurance certificate",
            "Claim compensation if crop loss occurs"
        ],
        "link": "https://pmfby.gov.in/",
        "categories": ["insurance", "farmer", "crop"],
        "occupation_match": ["Farmer"]
    },
    {
        "name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "description": "Financial inclusion scheme providing zero-balance bank accounts, debit cards, and overdraft facilities.",
        "eligibility": [
            "Age 10+",
            "No existing bank account (preferred)",
            "Aadhaar number",
            "Any Indian citizen"
        ],
        "apply_steps": [
            "Visit any bank branch",
            "Submit Aadhaar and address proof",
            "Fill account opening form",
            "Get zero-balance account",
            "Receive RuPay debit card",
            "Get overdraft facility after 6 months"
        ],
        "link": "https://pmjdy.gov.in/",
        "categories": ["banking", "financial_inclusion"],
        "age_min": 10
    },
    {
        "name": "Pradhan Mantri Vaya Vandana Yojana (PMVVY)",
        "description": "Pension scheme for senior citizens (60+) providing guaranteed returns and monthly pension.",
        "eligibility": [
            "Age 60+",
            "Indian citizen",
            "Investment capacity",
            "Not covered under other pension schemes"
        ],
        "apply_steps": [
            "Visit LIC branch or agent",
            "Submit age proof and Aadhaar",
            "Invest minimum ₹1.5 lakh",
            "Choose pension amount",
            "Receive monthly pension",
            "Get maturity amount after 10 years"
        ],
        "link": "https://www.licindia.in/",
        "categories": ["pension", "senior_citizen"],
        "age_min": 60
    },
    {
        "name": "Pradhan Mantri Shram Yogi Maan-Dhan (PM-SYM)",
        "description": "Pension scheme for unorganized sector workers providing ₹3,000 monthly pension after 60 years.",
        "eligibility": [
            "Age 18-40 years",
            "Unorganized sector worker",
            "Monthly income < ₹15,000",
            "Not covered under any other pension scheme"
        ],
        "apply_steps": [
            "Visit nearest Common Service Centre (CSC)",
            "Submit Aadhaar, bank account details",
            "Pay monthly contribution (₹55-200)",
            "Complete enrollment",
            "Receive pension after 60 years"
        ],
        "link": "https://maandhan.in/",
        "categories": ["pension", "unorganized_sector"],
        "income_limit": 15000,
        "age_min": 18,
        "age_max": 40
    },
    {
        "name": "Pradhan Mantri Awas Yojana - Urban (PMAY-U)",
        "description": "Urban housing scheme providing financial assistance for house construction, purchase, or enhancement.",
        "eligibility": [
            "Urban household",
            "Annual income < ₹18 lakh",
            "No pucca house",
            "Must not have availed any housing scheme"
        ],
        "apply_steps": [
            "Visit PMAY website",
            "Register with Aadhaar",
            "Fill application form",
            "Upload documents",
            "Get approval",
            "Receive financial assistance"
        ],
        "link": "https://pmaymis.gov.in/",
        "categories": ["housing", "urban"],
        "income_limit": 1800000
    }
]


def get_schemes_by_category(category: str) -> list:
    """Get schemes by category."""
    return [s for s in SCHEMES_DATABASE if category in s.get("categories", [])]


def get_schemes_by_occupation(occupation: str) -> list:
    """Get schemes matching occupation."""
    matching = []
    for scheme in SCHEMES_DATABASE:
        if "occupation_match" in scheme:
            if occupation in scheme["occupation_match"]:
                matching.append(scheme)
    return matching


def filter_schemes_by_profile(age: int, income: float, occupation: str) -> list:
    """
    Filter schemes based on basic profile criteria.
    
    Args:
        age: User age
        income: Annual income
        occupation: Occupation
        
    Returns:
        List of potentially matching schemes
    """
    matching = []
    
    for scheme in SCHEMES_DATABASE:
        # Check age limits
        if "age_min" in scheme and age < scheme["age_min"]:
            continue
        if "age_max" in scheme and age > scheme["age_max"]:
            continue
        
        # Check income limits
        if "income_limit" in scheme and scheme["income_limit"]:
            if income > scheme["income_limit"]:
                continue
        
        # Check occupation match
        if "occupation_match" in scheme:
            if occupation not in scheme["occupation_match"]:
                continue
        
        matching.append(scheme)
    
    return matching
