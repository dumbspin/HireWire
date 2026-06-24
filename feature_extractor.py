import os
import numpy as np

# We import sentence_transformers dynamically inside the extractor to allow rank.py to pass the loaded model
class CandidateFeatureExtractor:
    def __init__(self, requirements, similarity_map=None):
        """
        requirements: dict containing must_have_skills, nice_to_have_skills, etc.
        similarity_map: dict mapping (cand_skill_lower, jd_skill_lower) -> similarity_float
        """
        self.must_have_skills = requirements.get('must_have_skills', [])
        self.nice_to_have_skills = requirements.get('nice_to_have_skills', [])
        self.similarity_map = similarity_map or {}
        
        # Skill proficiency weights
        self.proficiency_weights = {
            'beginner': 0.25,
            'intermediate': 0.5,
            'advanced': 0.8,
            'expert': 1.0
        }

    def compute_skill_trust(self, skill):
        """
        skill_trust = proficiency_weight * min(1, endorsements/20) * min(1, duration_months/24)
        """
        prof = skill.get('proficiency', 'beginner')
        weight = self.proficiency_weights.get(prof.lower(), 0.25)
        
        endorsements = skill.get('endorsements', 0)
        duration = skill.get('duration_months', 0)
        
        endorsement_factor = min(1.0, endorsements / 20.0)
        duration_factor = min(1.0, duration / 24.0)
        
        return weight * endorsement_factor * duration_factor

    def get_assessment_multiplier(self, skill_name, assessment_scores):
        """
        If a skill_assessment_score exists, apply: score/100 * 0.3 + 0.7.
        Else: 1.0 (no penalty)
        Wait! The PRD says: "zero assessment penalises by 30%".
        Wait! Let's check: does it mean if the candidate *has* assessments in their signals, but not for this specific skill? Or if the platform verified assessment is zero?
        In the signals definition: "dict of skill_name -> score 0-100. Assessments completed on Redrob platform."
        If the candidate has completed assessments on the platform, and for a must-have skill there is no assessment, does it penalize it by 30%?
        The PRD says: "If a skill_assessment_score exists in redrob_signals for that skill, apply a trust multiplier: assessment_score/100 * 0.3 + 0.7 (so high assessment boosts, zero assessment penalises by 30%)".
        Let's implement:
        Check if there is a match in candidate's assessment_scores (keys are things like 'NLP', 'Image Classification').
        Let's clean the key and find the best match.
        If a match is found:
            score = assessment_scores[match_key]
            return (score / 100.0) * 0.3 + 0.7
        else:
            return 1.0 # default
        """
        s_name_lower = skill_name.lower().strip()
        for k, val in assessment_scores.items():
            k_lower = k.lower().strip()
            # Direct match or substring match
            if k_lower == s_name_lower or k_lower in s_name_lower or s_name_lower in k_lower:
                return (val / 100.0) * 0.3 + 0.7
        return 1.0

    def compute_skills_match_score(self, candidate_skills, assessment_scores):
        """
        Calculates the skills matching score [0.0 - 1.0] for the candidate.
        """
        if not candidate_skills:
            return 0.0
            
        # Clean candidate skills
        cand_skills_dict = {}
        for s in candidate_skills:
            s_name = s.get('name', '')
            if s_name:
                cand_skills_dict[s_name.lower().strip()] = s

        # 1. Must-have skills score
        must_have_scores = []
        for must_skill in self.must_have_skills:
            best_score = 0.0
            for cand_skill_lower, s_obj in cand_skills_dict.items():
                # Get similarity (1.0 if exact match, else from similarity map)
                sim = 0.0
                if cand_skill_lower == must_skill:
                    sim = 1.0
                else:
                    sim = self.similarity_map.get((cand_skill_lower, must_skill), 0.0)
                
                if sim >= 0.70: # match threshold
                    trust = self.compute_skill_trust(s_obj)
                    mult = self.get_assessment_multiplier(s_obj.get('name', ''), assessment_scores)
                    score = sim * trust * mult
                    if score > best_score:
                        best_score = score
            must_have_scores.append(best_score)
            
        must_have_skills_score = sum(must_have_scores) / len(self.must_have_skills) if self.must_have_skills else 0.0
        
        # 2. Nice-to-have bonus
        nice_matched_count = 0
        for nice_skill in self.nice_to_have_skills:
            nice_found = False
            for cand_skill_lower in cand_skills_dict.keys():
                sim = 0.0
                if cand_skill_lower == nice_skill:
                    sim = 1.0
                else:
                    sim = self.similarity_map.get((cand_skill_lower, nice_skill), 0.0)
                
                if sim >= 0.70:
                    nice_found = True
                    break
            if nice_found:
                nice_matched_count += 1
                
        nice_to_have_bonus = min(0.1, 0.025 * nice_matched_count)
        
        # Final combined skills score
        return min(1.0, must_have_skills_score + nice_to_have_bonus)

    def extract_features(self, candidate):
        """
        Extracts all scoring features for a candidate.
        """
        profile = candidate.get('profile', {})
        career = candidate.get('career_history', [])
        skills = candidate.get('skills', [])
        signals = candidate.get('redrob_signals', {})
        education = candidate.get('education', [])
        
        # Import scorer functions locally
        from scorer import (
            compute_experience_score,
            compute_location_availability_score,
            compute_education_score,
            compute_career_score,
            compute_behavioral_multiplier
        )
        
        skills_score = self.compute_skills_match_score(skills, signals.get('skill_assessment_scores', {}))
        career_score = compute_career_score(profile, career)
        experience_score = compute_experience_score(profile.get('years_of_experience', 0.0))
        location_score = compute_location_availability_score(profile, signals)
        education_score = compute_education_score(education)
        behavioral_multiplier = compute_behavioral_multiplier(signals)
        
        return {
            'skills_score': skills_score,
            'career_score': career_score,
            'experience_score': experience_score,
            'location_score': location_score,
            'education_score': education_score,
            'behavioral_multiplier': behavioral_multiplier
        }
