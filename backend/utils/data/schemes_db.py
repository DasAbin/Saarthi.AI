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
        "occupation_match": ["Farmer", "Agriculture"],
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
        "occupation_match": ["Unorganized Worker", "Laborer", "Street Vendor", "Domestic Worker"],
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
        "occupation_match": ["Farmer", "Agriculture"],
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
        "occupation_match": ["Business Owner", "Self Employed", "Entrepreneur"],
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
        "occupation_match": ["Farmer", "Agriculture"],
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
        "occupation_match": ["Farmer", "Agriculture"]
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
    },
    {
        "name": "Pradhan Mantri Kaushal Vikas Yojana (PMKVY)",
        "description": "Skill development initiative scheme to provide industry-relevant skill training to Indian youth to help them secure a better livelihood.",
        "eligibility": [
            "Indian youth of working age",
            "Unemployed youth or school/college dropouts",
            "Valid identity proof (Aadhaar/Voter ID)",
            "Bank account"
        ],
        "apply_steps": [
            "Visit PMKVY official website or nearest Skill India center",
            "Identify the training course you want to pursue",
            "Register on the Skill India portal",
            "Submit required documents and enroll in the course",
            "Complete training and get certified",
            "Avail placement assistance provided by the center"
        ],
        "link": "https://www.pmkvyofficial.org/",
        "categories": ["education", "youth", "employment"],
        "occupation_match": ["Student", "Unemployed"]
    },
    {
        "name": "Beti Bachao Beti Padhao",
        "description": "Campaign to celebrate the girl child and enable her education, aiming to address the declining Child Sex Ratio (CSR).",
        "eligibility": [
            "A family with a girl child, directly benefiting from awareness campaigns and linked schemes like Sukanya Samriddhi",
            "Implementation across districts with low CSR",
            "Educational and child welfare benefits targeted at girls"
        ],
        "apply_steps": [
            "Information and awareness scheme (no direct application for funds under this name alone)",
            "Participate through linked initiatives at local Anganwadi/Health centers",
            "Avail linked benefits like Sukanya Samriddhi Yojana for the girl child"
        ],
        "link": "https://wcd.nic.in/bbbp-schemes",
        "categories": ["women", "girl_child", "education"]
    },
    {
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "description": "A savings scheme targeted at the parents of girl children, offering high interest rates and tax benefits to build a fund for her future education and marriage.",
        "eligibility": [
            "Parents or legal guardians of a girl child",
            "Girl child must be below 10 years of age",
            "Maximum 2 accounts per family (one for each girl child)"
        ],
        "apply_steps": [
            "Visit any authorized bank branch or post office",
            "Fill the SSY account opening form (Form-1)",
            "Provide girl child's birth certificate",
            "Provide guardian's identity and address proof",
            "Make an initial deposit (minimum ₹250)",
            "Account is opened and passbook is issued"
        ],
        "link": "https://www.india.gov.in/sukanya-samriddhi-yojna",
        "categories": ["girl_child", "savings", "tax_benefit", "investment"],
        "age_max": 10
    },
    {
        "name": "National Scholarship Portal (NSP)",
        "description": "One-stop portal for all government scholarships ranging from pre-matric to post-matric and higher education.",
        "eligibility": [
            "Students pursuing recognized courses",
            "Certain scholarships target specific categories (SC/ST/OBC/Minorities/EWS)",
            "Minimum marks requirement varying by scheme",
            "Varying income limits depending on the specific scholarship"
        ],
        "apply_steps": [
            "Visit the National Scholarship Portal (scholarships.gov.in)",
            "Click on 'New Registration' and read guidelines",
            "Register with Aadhaar and bank details to get an Application ID",
            "Login and fill the specific scholarship form",
            "Upload necessary documents (income certificate, caste certificate, marksheet)",
            "Submit and track application status online"
        ],
        "link": "https://scholarships.gov.in/",
        "categories": ["education", "student", "scholarship"],
        "occupation_match": ["Student"]
    },
    {
        "name": "Atal Pension Yojana (APY)",
        "description": "A pension scheme focused on the unorganized sector workers, providing a guaranteed minimum pension of ₹1,000 to ₹5,000 per month after 60 years of age.",
        "eligibility": [
            "Indian citizen",
            "Age between 18 and 40 years",
            "Must have a savings bank account",
            "Not an income tax payer"
        ],
        "apply_steps": [
            "Visit the bank or post office where you have an account",
            "Fill the APY registration form",
            "Provide Aadhaar and mobile number",
            "Ensure sufficient balance for the first auto-debit contribution",
            "Pension starts upon reaching age 60"
        ],
        "link": "https://www.npscra.nsdl.co.in/scheme-details.php",
        "categories": ["pension", "unorganized_sector", "retirement"],
        "occupation_match": ["Unorganized Worker", "Laborer", "Self Employed"],
        "age_min": 18,
        "age_max": 40
    },
    {
        "name": "PM CARES for Children",
        "description": "Scheme to support children who lost both parents or surviving parent to COVID-19, providing education, health insurance, and a ₹10 lakh corpus at age 23.",
        "eligibility": [
            "Children who lost both parents, surviving parent, or legal guardian/adoptive parents to COVID-19",
            "Incident occurred between 11.03.2020 and 28.02.2022",
            "Child was under 18 years of age at the time of the parent's death"
        ],
        "apply_steps": [
            "Visit pmcaresforchildren.in portal",
            "Registration can be done by citizens, relatives, or district officers",
            "Fill child details and upload parents' death certificates",
            "Submit for District Magistrate approval",
            "Benefits are processed through nodal agencies and linked accounts"
        ],
        "link": "https://pmcaresforchildren.in/",
        "categories": ["children", "welfare", "health", "education"],
        "age_max": 18
    },
    {
        "name": "Stand Up India",
        "description": "Scheme facilitating bank loans between ₹10 lakh and ₹1 Crore to at least one SC/ST borrower and one woman borrower per bank branch for setting up a greenfield enterprise.",
        "eligibility": [
            "SC/ST and/or women entrepreneurs",
            "Age 18+",
            "Enterprises in manufacturing, services, agri-allied activities, or trading sector",
            "Not in default to any bank or financial institution"
        ],
        "apply_steps": [
            "Visit valid commercial bank branch or Stand Up India portal (standupmitra.in)",
            "Apply for the loan directly or through Lead District Manager",
            "Submit project report for the greenfield enterprise",
            "Provide identity proofs and category certificates (SC/ST/Woman)",
            "Get loan sanctioned for machinery/working capital"
        ],
        "link": "https://www.standupmitra.in/",
        "categories": ["business", "loan", "women", "sc_st", "entrepreneur"],
        "occupation_match": ["Business Owner", "Self Employed", "Entrepreneur"],
        "age_min": 18
    },
    {
        "name": "Common Service Centre (CSC) Scheme / Digital India",
        "description": "Network of access points across rural India for delivery of essential public utility services, social welfare schemes, healthcare, and digital literacy.",
        "eligibility": [
            "Any citizen can avail services at a CSC",
            "To become a Village Level Entrepreneur (VLE) running a CSC, one must be aged 18+, have passed 10th-level exams, and possess basic digital skills"
        ],
        "apply_steps": [
            "To avail services: Visit the nearest CSC",
            "To open a CSC (VLE): Visit register.csc.gov.in",
            "Register with Aadhaar and required infrastructure details",
            "Take the TEC (Telecentre Entrepreneur Course) Certificate",
            "Submit application online for approval"
        ],
        "link": "https://csc.gov.in/",
        "categories": ["digital_services", "rural", "employment"],
        "age_min": 18
    },
    {
        "name": "Swachh Bharat Mission (Grameen)",
        "description": "Scheme to achieve universal sanitation coverage, aiming to make villages Open Defecation Free (ODF) and improve solid/liquid waste management. Provides incentives to BPL/eligible APL households for constructing toilets.",
        "eligibility": [
            "BPL households",
            "Specified APL households (SC/ST, physically handicapped, landless laborers, marginalized workers, female-headed households)",
            "A household that does not currently have an individual household latrine"
        ],
        "apply_steps": [
            "Visit the Swachh Bharat Mission portal (sbm.gov.in) or local Gram Panchayat",
            "Register as a citizen and submit application for IHHL (Individual Household Latrine)",
            "Provide Aadhaar and bank details",
            "Application is physically verified by block officers",
            "Construct toilet and upload geotagged photos",
            "Receive incentive (₹12,000) directly to bank account"
        ],
        "link": "https://sbm.gov.in/",
        "categories": ["sanitation", "rural", "infrastructure", "health"],
        "income_limit": None
    },
    {
        "name": "Ayushman Bharat Digital Mission (ABDM)",
        "description": "Initiative to develop a national digital health ecosystem. Allows citizens to create an Ayushman Bharat Health Account (ABHA) number for storing and accessing digital health records.",
        "eligibility": [
            "Any Indian citizen",
            "Aadhaar card or mobile number required for registration"
        ],
        "apply_steps": [
            "Visit the ABHA portal (abha.abdm.gov.in) or download the ABHA app",
            "Click on 'Create ABHA Number'",
            "Use Aadhaar or Driving License for verification",
            "Authenticate via OTP",
            "Set up ABHA address (similar to an email ID) and secure health records",
            "Share ABHA ID with registered doctors/hospitals for seamless record keeping"
        ],
        "link": "https://abha.abdm.gov.in/",
        "categories": ["health", "digital_health", "infrastructure"]
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
    Schemes that don't match the hard age/income criteria are filtered out.
    Schemes with an occupation_match that aligns with the user get a priority BOOST.
    
    Args:
        age: User age
        income: Annual income
        occupation: Occupation
        
    Returns:
        List of potentially matching schemes, sorted by relevance score
    """
    matching_with_scores = []
    
    for scheme in SCHEMES_DATABASE:
        # Hard Filter: Age limits
        if "age_min" in scheme and age < scheme["age_min"]:
            continue
        if "age_max" in scheme and age > scheme["age_max"]:
            continue
        
        # Hard Filter: Income limits
        if "income_limit" in scheme and scheme["income_limit"] is not None:
            if income > scheme["income_limit"]:
                continue
        
        # Ranking Score
        score = 0
        
        # Boost: Occupation match (Not a hard filter!)
        if "occupation_match" in scheme and occupation:
            # Simple substring matching or exact match to boost appropriately
            for match_term in scheme["occupation_match"]:
                if match_term.lower() in occupation.lower() or occupation.lower() in match_term.lower():
                    score += 10
                    break
                    
        matching_with_scores.append((score, scheme))
    
    # Sort descending by score
    matching_with_scores.sort(key=lambda x: x[0], reverse=True)
    
    return [item[1] for item in matching_with_scores]
