import math

def compute_experience_score(years_of_experience):
    """
    Gaussian penalty centered at 7 years, sigma = 3.
    Gives: 7yrs=1.0, 5yrs=0.87, 9yrs=0.87, 3yrs=0.57, 12yrs=0.69
    """
    try:
        yoe = float(years_of_experience)
    except (ValueError, TypeError):
        yoe = 0.0
    return math.exp(-0.5 * ((yoe - 7.0) / 3.0) ** 2)

def compute_location_availability_score(profile, signals):
    """
    Combines location and notice period score (each 50% of this component).
    """
    location = profile.get('location', '').lower()
    country = profile.get('country', '').lower()
    willing_relocate = profile.get('willing_to_relocate', False) or signals.get('willing_to_relocate', False)
    
    # Noida, Pune, Delhi NCR, Mumbai, Hyderabad, Bengaluru
    preferred_cities = ['noida', 'pune', 'delhi', 'ncr', 'mumbai', 'hyderabad', 'bengaluru', 'bangalore']
    
    # 1. Location score
    location_score = 0.5 # default for India other cities
    if any(city in location for city in preferred_cities):
        location_score = 1.0
    elif country == 'india':
        if willing_relocate:
            location_score = 0.8
        else:
            location_score = 0.5
    else:
        # Global candidates
        if willing_relocate:
            location_score = 0.4
        else:
            location_score = 0.2
            
    # 2. Notice period score
    notice_days = signals.get('notice_period_days', 90)
    if notice_days <= 30:
        notice_score = 1.0
    elif notice_days <= 60:
        notice_score = 0.7
    elif notice_days <= 90:
        notice_score = 0.4
    else:
        notice_score = 0.1
        
    return 0.5 * location_score + 0.5 * notice_score

def compute_education_score(education_list):
    """
    Maps school tier and relevance of field of study.
    """
    if not education_list:
        return 0.3 # default score
        
    tier_scores = {
        'tier_1': 1.0,
        'tier_2': 0.7,
        'tier_3': 0.4,
        'tier_4': 0.2,
        'unknown': 0.3
    }
    
    relevance_keywords = ['computer', 'data', 'machine learning', 'artificial', 'software', 'information', 'statistics', 'math', 'electrical', 'electronics']
    
    max_edu_score = 0.0
    for edu in education_list:
        tier = edu.get('tier', 'unknown')
        t_score = tier_scores.get(tier, 0.3)
        
        field = edu.get('field_of_study', '').lower()
        degree = edu.get('degree', '').lower()
        
        # Check relevance
        is_relevant = any(kw in field for kw in relevance_keywords) or any(kw in degree for kw in relevance_keywords)
        relevance_mult = 1.0 if is_relevant else 0.6
        
        edu_score = t_score * relevance_mult
        if edu_score > max_edu_score:
            max_edu_score = edu_score
            
    return max_edu_score

def compute_career_score(profile, career_history):
    """
    Combines current title relevance (50%) and production evidence keywords (50%).
    """
    # 1. Title score
    current_title = profile.get('current_title', '').lower()
    if not current_title and career_history:
        current_title = career_history[0].get('title', '').lower()
        
    title_score = 0.1
    if any(kw in current_title for kw in ['ml engineer', 'ai engineer', 'machine learning', 'data scientist', 'nlp engineer', 'research engineer', 'computer vision', 'search engineer']):
        title_score = 1.0
    elif any(kw in current_title for kw in ['software engineer', 'backend engineer', 'data engineer', 'full stack', 'developer', 'programmer']):
        title_score = 0.7
    elif any(kw in current_title for kw in ['product manager', 'business analyst', 'devops', 'qa', 'scrum', 'project manager']):
        title_score = 0.4
        
    # 2. Production keywords hits
    prod_keywords = ['production', 'deployed', 'ship', 'users', 'latency', 'a/b', 'inference', 'scale', 'scaling', 'pipeline', 'optimize', 'aws', 'gcp', 'cloud']
    hits = set()
    for role in career_history:
        desc = role.get('description', '').lower()
        for kw in prod_keywords:
            if kw in desc:
                hits.add(kw)
                
    production_signal = min(1.0, len(hits) * 0.15)
    
    return 0.5 * title_score + 0.5 * production_signal

def compute_behavioral_multiplier(signals):
    """
    Geometric mean of profile completeness, response rate, and interview completion.
    Modified by open to work flag and github activity score.
    """
    profile_completeness = signals.get('profile_completeness_score', 50.0)
    recruiter_response_rate = signals.get('recruiter_response_rate', 0.5)
    interview_completion_rate = signals.get('interview_completion_rate', 0.5)
    open_to_work = signals.get('open_to_work_flag', False)
    github_score = signals.get('github_activity_score', -1.0)
    
    # Prevent divide/geometric-mean zero drop out
    completeness_norm = max(0.01, profile_completeness / 100.0)
    response_norm = max(0.01, recruiter_response_rate)
    interview_norm = max(0.01, interview_completion_rate)
    
    geom_mean = (completeness_norm * response_norm * interview_norm) ** (1.0 / 3.0)
    
    open_to_work_bonus = 1.0 if open_to_work else 0.5
    
    github_norm = max(0.0, github_score) / 100.0 if github_score >= 0 else 0.0
    github_mult = 0.7 + 0.3 * github_norm
    
    behavioural_score = geom_mean * open_to_work_bonus * github_mult
    return min(1.0, behavioural_score)

def calculate_final_score(skills_score, career_score, experience_score, location_score, education_score, behavioral_multiplier):
    """
    Scores blending formula.
    """
    raw_score = 0.35 * skills_score + 0.25 * career_score + 0.15 * experience_score + 0.10 * location_score + 0.05 * education_score
    final_score = raw_score * (0.85 + 0.15 * behavioral_multiplier)
    return round(final_score, 4)
