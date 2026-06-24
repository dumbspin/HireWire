import re

# Company founding years for honeypot check
COMPANY_FOUNDING_YEARS = {
    'Accenture': 1989, 'Adobe': 1982, 'Aganitha': 2017, 'Amazon': 1994, 'Apple': 1976,
    "BYJU'S": 2011, 'CRED': 2018, 'Capgemini': 1967, 'Cognizant': 1994, 'Dream11': 2008,
    'Flipkart': 2007, 'Freshworks': 2010, 'Genpact AI': 2023, 'Glance': 2019, 'Google': 1998,
    'HCL': 1976, 'Haptik': 2013, 'InMobi': 2007, 'Infosys': 1981, 'Krutrim': 2023,
    'LinkedIn': 2002, 'Locobuzz': 2015, 'Mad Street Den': 2013, 'Meesho': 2015, 'Meta': 2004,
    'Microsoft': 1975, 'Mindtree': 1999, 'Mphasis': 1998, 'Netflix': 1997, 'Niramai': 2016,
    'Nykaa': 2012, 'Observe.AI': 2017, 'Ola': 2010, 'Paytm': 2010, 'PharmEasy': 2015,
    'PhonePe': 2015, 'PolicyBazaar': 2008, 'Razorpay': 2014, 'Rephrase.ai': 2019,
    'Saarthi.ai': 2017, 'Salesforce': 1999, 'Sarvam AI': 2023, 'Swiggy': 2014, 'TCS': 1968,
    'Tech Mahindra': 1986, 'Uber': 2009, 'Unacademy': 2015, 'Vedantu': 2011, 'Verloop.io': 2015,
    'Wipro': 1945, 'Wysa': 2015, 'Yellow.ai': 2016, 'Zoho': 1996, 'Zomato': 2008, 'upGrad': 2015
}

CONSULTING_COMPANIES = [
    'tcs', 'infosys', 'wipro', 'accenture', 'cognizant', 'capgemini', 
    'hexaware', 'mphasis', 'tech mahindra', 'hcl', 'ibm global services', 'ibm'
]

MANAGEMENT_TITLES = ['vp', 'director', 'head', 'architect', 'manager', 'chief', 'pm', 'lead architect']
TECH_TITLE_KEYWORDS = ['ml', 'ai', 'engineer', 'developer', 'programmer', 'data scientist', 'nlp', 'vision', 'researcher', 'software', 'backend', 'frontend', 'full stack']
CODING_KEYWORDS = ['code', 'python', 'develop', 'implement', 'program', 'build', 'train', 'tune', 'write', 'engineer', 'debug', 'git', 'deploy', 'ship', 'pipeline', 'sql', 'spark', 'pytorch', 'tensorflow', 'scikit', 'ml', 'ai']

LLM_WRAPPERS = ['langchain', 'chatgpt', 'openai', 'llm wrapper', 'prompt engineering', 'anthropic', 'cohere', 'gpt', 'llamaindex']
FOUNDATIONAL_ML = ['numpy', 'pandas', 'scikit-learn', 'sklearn', 'pytorch', 'tensorflow', 'keras', 'sql', 'machine learning', 'deep learning', 'nlp', 'python', 'math', 'statistics', 'algorithms', 'regression', 'xgboost', 'scipy', 'spark']

ACADEMIC_KEYWORDS = ['university', 'college', 'iit', 'iiit', 'bits', 'nit', 'research lab', 'institute', 'academia', 'stanford', 'mit', 'oxford', 'cambridge', 'iisc']

CV_SPEECH_ROBOTICS = ['computer vision', 'opencv', 'image processing', 'object detection', 'speech recognition', 'text-to-speech', 'tts', 'ros', 'robotics', 'speech to text', 'audio processing', 'image classification', 'cnn', 'gans', 'yolo']
NLP_IR_SEARCH = ['nlp', 'natural language', 'text retrieval', 'information retrieval', 'search', 'embeddings', 'vector', 'rag', 'llm', 'transformer', 'bert', 'gpt']

def clean_company(name):
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\b(pvt\b|ltd\b|corp\b|corporation\b|inc\b|services\b|limited\b)', '', name)
    return name.strip()

def evaluate_disqualifiers(candidate):
    """
    Evaluates a candidate's profile against the 6 hard disqualifier rules and honeypots.
    Returns: (is_disqualified, reason, score_cap)
    """
    profile = candidate.get('profile', {})
    career = candidate.get('career_history', [])
    skills = candidate.get('skills', [])
    
    # 0. Honeypot check (Highest severity, Cap = 0.10)
    # Check 0.1: Company founding date mismatch (gap >= 1 year to avoid slight synthetic variations)
    for role in career:
        comp = role.get('company', '')
        start_date = role.get('start_date')
        if comp in COMPANY_FOUNDING_YEARS and start_date:
            try:
                start_year = int(start_date.split('-')[0])
                founding_year = COMPANY_FOUNDING_YEARS[comp]
                if start_year < founding_year - 1:
                    return True, f"Honeypot: Started at {comp} in {start_year} but founded in {founding_year}", 0.10
            except:
                pass
                
    # Check 0.2: Expert/advanced skills with 0 duration_months (5 or more skills)
    expert_zero_dur = sum(1 for s in skills if s.get('proficiency') in ['expert'] and s.get('duration_months', 0) == 0)
    if expert_zero_dur >= 5:
        return True, f"Honeypot: Expert in {expert_zero_dur} skills with 0 duration", 0.10

    # 1. Consulting-Only Career (Cap = 0.15)
    if career:
        all_consulting = True
        for role in career:
            comp_clean = clean_company(role.get('company', ''))
            is_consulting = False
            for c in CONSULTING_COMPANIES:
                if c in comp_clean:
                    is_consulting = True
                    break
            if not is_consulting:
                all_consulting = False
                break
        if all_consulting:
            return True, "Disqualified: Consulting-only career", 0.15

    # 2. No Recent Production Code (Cap = 0.20)
    if career:
        most_recent = career[0]
        title_lower = most_recent.get('title', '').lower()
        duration = most_recent.get('duration_months', 0)
        desc_lower = most_recent.get('description', '').lower()
        
        # Check if duration > 18 months and title matches management keywords strictly
        has_mgmt_title = False
        for kw in MANAGEMENT_TITLES:
            if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
                has_mgmt_title = True
                break
                
        # Must not contain engineering keywords (which would make it a technical lead / developer)
        has_tech_title = False
        for kw in TECH_TITLE_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', title_lower):
                has_tech_title = True
                break
                
        if duration > 18 and has_mgmt_title and not has_tech_title:
            # Check if description has zero coding keywords
            has_coding = False
            for kw in CODING_KEYWORDS:
                if re.search(r'\b' + re.escape(kw) + r'\b', desc_lower):
                    has_coding = True
                    break
            if not has_coding:
                return True, "Disqualified: Pure management/architect role > 18 months without coding", 0.20

    # 3. Title Chaser Pattern (Cap = 0.25)
    if len(career) >= 4:
        # Check average tenure
        total_months = sum(role.get('duration_months', 0) for role in career)
        avg_tenure = total_months / len(career)
        
        # Check if they switched frequently without progression
        # progression = title contains lead, senior, head, principal, manager
        progression_found = False
        for role in career:
            role_title = role.get('title', '').lower()
            if any(prog in role_title for prog in ['senior', 'lead', 'manager', 'head', 'principal', 'staff', 'vp', 'director']):
                progression_found = True
                break
                
        if avg_tenure < 15 and not progression_found:
            return True, "Disqualified: Title chaser (frequent switches without promotion)", 0.25

    # 4. Under-12-Month LLM-Wrapper Only (Cap = 0.20)
    # Check total AI/ML experience. In skills, check if they have wrapper skills and NO foundational skills
    has_wrapper = False
    has_foundational = False
    
    skill_names_lower = [s.get('name', '').lower() for s in skills]
    for s_name in skill_names_lower:
        if any(w in s_name for w in LLM_WRAPPERS):
            has_wrapper = True
        if any(f in s_name for f in FOUNDATIONAL_ML):
            has_foundational = True
            
    # Check total ML duration from skills
    total_ml_duration = 0
    for s in skills:
        s_name = s.get('name', '').lower()
        if any(w in s_name for w in LLM_WRAPPERS) or any(f in s_name for f in ['machine learning', 'deep learning', 'nlp', 'computer vision', 'vector database']):
            total_ml_duration = max(total_ml_duration, s.get('duration_months', 0))
            
    if has_wrapper and not has_foundational and total_ml_duration < 12:
        return True, "Disqualified: LangChain/OpenAI wrapper expert < 12 months with no foundational ML", 0.20

    # 5. CV-Only Researcher (Cap = 0.20)
    if career:
        all_academic = True
        for role in career:
            comp_lower = role.get('company', '').lower()
            is_academic = False
            for kw in ACADEMIC_KEYWORDS:
                if kw in comp_lower:
                    is_academic = True
                    break
            if not is_academic:
                all_academic = False
                break
        if all_academic:
            return True, "Disqualified: Academic/research-only background", 0.20

    # 6. Primary CV/Speech/Robotics, No NLP (Cap = 0.25)
    if skills:
        # Sort skills by endorsements descending
        sorted_skills = sorted(skills, key=lambda x: x.get('endorsements', 0), reverse=True)
        top_3_skills = [s.get('name', '').lower() for s in sorted_skills[:3]]
        
        # Check if top 3 are exclusively CV/Speech/Robotics
        top_3_exclusively_cv_sr = True
        for s_name in top_3_skills:
            is_cv_sr = False
            for item in CV_SPEECH_ROBOTICS:
                if item in s_name:
                    is_cv_sr = True
                    break
            if not is_cv_sr:
                top_3_exclusively_cv_sr = False
                break
                
        # Check if they have zero NLP/IR/search skills
        has_nlp_ir = False
        for s in skills:
            s_name = s.get('name', '').lower()
            for item in NLP_IR_SEARCH:
                if item in s_name:
                    has_nlp_ir = True
                    break
            if has_nlp_ir:
                break
                
        if top_3_exclusively_cv_sr and not has_nlp_ir:
            return True, "Disqualified: Primary CV/speech/robotics with zero NLP/IR background", 0.25

    return False, "Suitable", 1.0

if __name__ == '__main__':
    # Quick sanity checks
    print("Disqualifiers module loaded successfully.")
