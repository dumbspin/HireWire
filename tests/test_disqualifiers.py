import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from disqualifiers import evaluate_disqualifiers

class TestDisqualifiers(unittest.TestCase):
    
    def test_honeypots(self):
        # 1. Company founding year mismatch
        # Krutrim was founded in 2023, started in 2018
        cand_honeypot_comp = {
            'candidate_id': 'CAND_9999991',
            'career_history': [
                {'company': 'Krutrim', 'start_date': '2018-05-02', 'duration_months': 36}
            ],
            'skills': [],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand_honeypot_comp)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.10)
        self.assertIn("Honeypot", reason)

        # 2. Expert skills with 0 duration
        cand_honeypot_skills = {
            'candidate_id': 'CAND_9999992',
            'career_history': [],
            'skills': [
                {'name': 'Python', 'proficiency': 'expert', 'duration_months': 0},
                {'name': 'SQL', 'proficiency': 'expert', 'duration_months': 0},
                {'name': 'Docker', 'proficiency': 'expert', 'duration_months': 0},
                {'name': 'Flask', 'proficiency': 'expert', 'duration_months': 0},
                {'name': 'Git', 'proficiency': 'expert', 'duration_months': 0}
            ],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand_honeypot_skills)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.10)
        self.assertIn("Honeypot", reason)

    def test_consulting_only(self):
        # All roles are at consulting companies (TCS, Infosys)
        cand = {
            'career_history': [
                {'company': 'TCS Pvt Ltd', 'title': 'Software Engineer'},
                {'company': 'Infosys Services', 'title': 'Systems Engineer'}
            ],
            'skills': [],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.15)
        self.assertIn("Consulting-only", reason)

    def test_no_recent_code(self):
        # Current role > 18 months, management title, descriptions have no coding keywords
        cand = {
            'career_history': [
                {
                    'title': 'Director of Product', 
                    'duration_months': 24, 
                    'description': 'Managed the roadmap, led standups, and worked with business team.'
                }
            ],
            'skills': [],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.20)
        self.assertIn("Pure management", reason)

    def test_title_chaser(self):
        # >= 4 companies in total, avg tenure < 15, no promotions/senior titles
        cand = {
            'career_history': [
                {'company': 'Comp A', 'title': 'Engineer', 'duration_months': 12},
                {'company': 'Comp B', 'title': 'Developer', 'duration_months': 10},
                {'company': 'Comp C', 'title': 'Programmer', 'duration_months': 11},
                {'company': 'Comp D', 'title': 'Full Stack', 'duration_months': 13}
            ],
            'skills': [],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.25)
        self.assertIn("Title chaser", reason)

    def test_llm_wrapper_only(self):
        # Total experience < 12 months, only wrapper skills, no foundational skills
        cand = {
            'career_history': [
                {'company': 'Comp A', 'title': 'AI Developer', 'duration_months': 8}
            ],
            'skills': [
                {'name': 'LangChain', 'proficiency': 'advanced', 'duration_months': 8},
                {'name': 'ChatGPT API', 'proficiency': 'expert', 'duration_months': 8}
            ],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.20)
        self.assertIn("wrapper", reason)

    def test_cv_only_researcher(self):
        # All roles are academic
        cand = {
            'career_history': [
                {'company': 'Stanford University', 'title': 'Research Assistant'},
                {'company': 'MIT Lab', 'title': 'Postdoc Fellow'}
            ],
            'skills': [],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.20)
        self.assertIn("Academic", reason)

    def test_cv_speech_robotics_only(self):
        # Top 3 skills are CV/speech/robotics, zero NLP/IR
        cand = {
            'career_history': [],
            'skills': [
                {'name': 'Computer Vision', 'proficiency': 'expert', 'endorsements': 100},
                {'name': 'OpenCV', 'proficiency': 'expert', 'endorsements': 90},
                {'name': 'ROS', 'proficiency': 'expert', 'endorsements': 80},
                {'name': 'React', 'proficiency': 'beginner', 'endorsements': 1}
            ],
            'redrob_signals': {}
        }
        is_disq, reason, cap = evaluate_disqualifiers(cand)
        self.assertTrue(is_disq)
        self.assertEqual(cap, 0.25)
        self.assertIn("CV/speech/robotics", reason)

if __name__ == '__main__':
    unittest.main()
