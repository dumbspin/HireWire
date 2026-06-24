import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorer import (
    compute_experience_score,
    compute_location_availability_score,
    compute_education_score,
    compute_career_score,
    compute_behavioral_multiplier,
    calculate_final_score
)

class TestScorer(unittest.TestCase):
    
    def test_experience_score(self):
        # Center = 7, sigma = 3
        # 7yrs should give 1.0
        self.assertAlmostEqual(compute_experience_score(7.0), 1.0, places=4)
        # 5yrs and 9yrs should give same value (around 0.80)
        self.assertAlmostEqual(compute_experience_score(5.0), compute_experience_score(9.0), places=4)
        # Check invalid input defaults to 0
        self.assertEqual(compute_experience_score("invalid"), compute_experience_score(0))

    def test_location_availability_score(self):
        # 1. Preferred city (Noida/Pune) and notice period <= 30
        profile = {'location': 'Pune, Maharashtra', 'country': 'India'}
        signals = {'notice_period_days': 15, 'willing_to_relocate': False}
        score = compute_location_availability_score(profile, signals)
        self.assertEqual(score, 1.0) # 0.5 * 1.0 + 0.5 * 1.0

        # 2. Global candidate unwilling to relocate, notice > 90
        profile_global = {'location': 'New York', 'country': 'USA'}
        signals_global = {'notice_period_days': 120, 'willing_to_relocate': False}
        score_global = compute_location_availability_score(profile_global, signals_global)
        self.assertEqual(score_global, 0.5 * 0.2 + 0.5 * 0.1) # 0.1 + 0.05 = 0.15

    def test_education_score(self):
        # Tier 1 Computer Science
        edu = [{'tier': 'tier_1', 'degree': 'B.Tech', 'field_of_study': 'Computer Science'}]
        score = compute_education_score(edu)
        self.assertEqual(score, 1.0)

        # Tier 3 History (Not CS/IT related)
        edu_non_relevant = [{'tier': 'tier_3', 'degree': 'B.A.', 'field_of_study': 'Ancient History'}]
        score_non_relevant = compute_education_score(edu_non_relevant)
        self.assertAlmostEqual(score_non_relevant, 0.4 * 0.6, places=4) # tier_3=0.4, relevance=0.6 -> 0.24

        # Empty education
        self.assertEqual(compute_education_score([]), 0.3)

    def test_career_score(self):
        # ML Engineer current title, descriptions have shipping keywords
        profile = {'current_title': 'Senior ML Engineer'}
        career = [
            {'title': 'ML Engineer', 'description': 'Deployed a real-time recommendations pipeline to production, optimizing latency.'}
        ]
        score = compute_career_score(profile, career)
        # title_score = 1.0
        # hits: 'production', 'deployed', 'latency', 'pipeline' -> 4 hits * 0.15 = 0.60
        # career_score = 0.5 * 1.0 + 0.5 * 0.60 = 0.80
        self.assertAlmostEqual(score, 0.80, places=4)

    def test_behavioral_multiplier(self):
        # High completeness, response, interview rates, open to work and github
        signals = {
            'profile_completeness_score': 100.0,
            'recruiter_response_rate': 1.0,
            'interview_completion_rate': 1.0,
            'open_to_work_flag': True,
            'github_activity_score': 100.0
        }
        mult = compute_behavioral_multiplier(signals)
        self.assertEqual(mult, 1.0) # GM=1.0, open_work=1.0, github=1.0 -> 1.0

        # Passive candidate, low response rate
        signals_low = {
            'profile_completeness_score': 80.0,
            'recruiter_response_rate': 0.1,
            'interview_completion_rate': 0.8,
            'open_to_work_flag': False,
            'github_activity_score': -1.0 # no github
        }
        mult_low = compute_behavioral_multiplier(signals_low)
        # GM = (0.8 * 0.1 * 0.8) ** (1/3) = (0.064) ** (1/3) = 0.40
        # open_to_work_bonus = 0.5
        # github_mult = 0.7
        # result = 0.40 * 0.5 * 0.7 = 0.14
        self.assertAlmostEqual(mult_low, 0.14, places=4)

if __name__ == '__main__':
    unittest.main()
