import os
import sys
import argparse
import json
import gzip
import csv
from tqdm import tqdm

# Import local modules
from jd_parser import JobDescriptionParser
from feature_extractor import CandidateFeatureExtractor
from disqualifiers import evaluate_disqualifiers
from scorer import calculate_final_score

def parse_args():
    parser = argparse.ArgumentParser(description="Intelligent Candidate Discovery & Ranking")
    parser.add_argument("--candidates", type=str, default=None,
                        help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--jd", type=str, default="job_description.docx",
                        help="Path to job description docx")
    parser.add_argument("--out", type=str, default="submission.csv",
                        help="Path to output submission CSV")
    parser.add_argument("--model-path", type=str, default=None,
                        help="Path to local sentence-transformers model")
    return parser.parse_args()

def open_candidates_file(path):
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')
    return open(path, 'r', encoding='utf-8')

def find_candidates_file(cwd):
    # Locate candidate files in standard folders
    possible_paths = [
        os.path.join(cwd, "candidates.jsonl"),
        os.path.join(cwd, "candidates.jsonl.gz"),
        os.path.join(cwd, "[PUB] India_runs_data_and_ai_challenge", "[PUB] India_runs_data_and_ai_challenge", "India_runs_data_and_ai_challenge", "candidates.jsonl"),
        os.path.join(cwd, "[PUB] India_runs_data_and_ai_challenge", "[PUB] India_runs_data_and_ai_challenge", "India_runs_data_and_ai_challenge", "candidates.jsonl.gz")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def find_jd_file(cwd):
    possible_paths = [
        os.path.join(cwd, "job_description.docx"),
        os.path.join(cwd, "[PUB] India_runs_data_and_ai_challenge", "[PUB] India_runs_data_and_ai_challenge", "India_runs_data_and_ai_challenge", "job_description.docx"),
        os.path.join(cwd, "AI_Candidate_Ranker_PRD.docx") # backup
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None

def build_similarity_map(model, unique_skills, jd_skills):
    """
    Computes cosine similarity between unique candidate skills and JD skills.
    Runs in under 1 second since unique skills is small (133).
    """
    if not model or not unique_skills or not jd_skills:
        return {}
        
    print(f"Pre-computing similarity map for {len(unique_skills)} unique skills against {len(jd_skills)} JD skills...")
    
    unique_skills_list = list(unique_skills)
    jd_skills_list = list(jd_skills)
    
    cand_embeddings = model.encode(unique_skills_list, convert_to_tensor=True)
    jd_embeddings = model.encode(jd_skills_list, convert_to_tensor=True)
    
    from sentence_transformers import util
    cosine_scores = util.cos_sim(cand_embeddings, jd_embeddings).cpu().numpy()
    
    similarity_map = {}
    for i, cand_s in enumerate(unique_skills_list):
        for j, jd_s in enumerate(jd_skills_list):
            similarity_map[(cand_s, jd_s)] = float(cosine_scores[i][j])
            
    return similarity_map

def generate_reasoning(cand, features, is_disqualified, reason, final_score, must_have_skills, similarity_map):
    profile = cand.get('profile', {})
    signals = cand.get('redrob_signals', {})
    
    title = profile.get('current_title', 'Engineer')
    yoe = profile.get('years_of_experience', 0.0)
    
    # Identify which must-have skills matched
    matched_must_haves = []
    for ms in must_have_skills:
        for s in cand.get('skills', []):
            name_lower = s.get('name', '').lower().strip()
            if name_lower == ms or similarity_map.get((name_lower, ms), 0.0) >= 0.70:
                matched_must_haves.append(s.get('name'))
                break
                
    matched_must_haves = sorted(list(set(matched_must_haves)))
    n_matched = len(matched_must_haves)
    skills_summary = ", ".join(matched_must_haves[:3])
    
    resp_rate = signals.get('recruiter_response_rate', 0.0)
    notice = signals.get('notice_period_days', 90)
    open_to_work = "active" if signals.get('open_to_work_flag') else "passive"
    location = profile.get('location', 'India')
    
    if is_disqualified:
        reasoning = f"{title} ({yoe} yrs). Filtered: {reason}."
    else:
        reasoning = f"{title} ({yoe:.1f} yrs) in {location}; matches {n_matched} core AI skills ({skills_summary}); notice {notice}d; resp_rate {resp_rate:.0%}; {open_to_work}."
        
    # Strictly enforce length <= 200 characters
    if len(reasoning) > 200:
        reasoning = reasoning[:197] + "..."
    return reasoning

def main():
    args = parse_args()
    cwd = os.getcwd()
    
    # 1. Resolve file paths
    candidates_path = args.candidates or find_candidates_file(cwd)
    if not candidates_path:
        print("Error: Could not find candidates file. Please specify via --candidates.")
        sys.exit(1)
        
    jd_path = args.jd or find_jd_file(cwd)
    if not jd_path:
        print("Error: Could not find job description file. Please specify via --jd.")
        sys.exit(1)
        
    print(f"Candidates file: {candidates_path}")
    print(f"Job Description: {jd_path}")
    print(f"Output path: {args.out}")
    
    # 2. Parse Job Description
    print("Parsing Job Description...")
    jd_parser = JobDescriptionParser(jd_path)
    reqs = jd_parser.get_requirements()
    must_have_skills = reqs['must_have_skills']
    nice_to_have_skills = reqs['nice_to_have_skills']
    jd_skills = set(must_have_skills + nice_to_have_skills)
    
    # 3. Load Sentence Transformer Model
    model = None
    similarity_map = {}
    
    # Determine model path
    model_dir = args.model_path or os.path.join(cwd, "models", "all-MiniLM-L6-v2")
    
    # Try importing sentence_transformers
    try:
        from sentence_transformers import SentenceTransformer
        if os.path.exists(model_dir):
            print(f"Loading local SentenceTransformer model from {model_dir}...")
            model = SentenceTransformer(model_dir)
        else:
            print("Local model directory not found. Downloading model dynamically...")
            model = SentenceTransformer('all-MiniLM-L6-v2')
            # Save for future offline usage
            os.makedirs(os.path.dirname(model_dir), exist_ok=True)
            model.save(model_dir)
            print(f"Saved model to {model_dir}")
    except Exception as e:
        print(f"Warning: SentenceTransformer loading failed: {e}. Falling back to exact string match only.")
        
    # 4. Pass 1: Extract unique skills in candidates file to precompute similarities
    if model:
        unique_skills = set()
        print("Pass 1: Scanning candidates to gather unique skills...")
        with open_candidates_file(candidates_path) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    cand = json.loads(line)
                    for s in cand.get('skills', []):
                        name = s.get('name')
                        if name:
                            unique_skills.add(name.lower().strip())
                except:
                    pass
        print(f"Found {len(unique_skills)} unique skills in candidate pool.")
        
        # Build similarity map
        similarity_map = build_similarity_map(model, unique_skills, jd_skills)
        
    # 5. Initialize Feature Extractor
    extractor = CandidateFeatureExtractor(reqs, similarity_map)
    
    # 6. Pass 2: Score candidates line by line
    scored_candidates = []
    print("Pass 2: Scoring candidates...")
    
    # Count total lines for progress bar if possible
    total_lines = 100000 # default
    
    with open_candidates_file(candidates_path) as f:
        for line in tqdm(f, total=total_lines, desc="Scoring"):
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
            except Exception as e:
                # Log error and skip corrupt line
                continue
                
            cid = cand.get('candidate_id')
            if not cid:
                continue
                
            # Extract features
            features = extractor.extract_features(cand)
            
            # Check hard disqualifiers
            is_disqualified, reason, score_cap = evaluate_disqualifiers(cand)
            
            # Compute final score
            final_score = calculate_final_score(
                features['skills_score'],
                features['career_score'],
                features['experience_score'],
                features['location_score'],
                features['education_score'],
                features['behavioral_multiplier']
            )
            
            # Apply disqualification cap
            if is_disqualified:
                final_score = min(final_score, score_cap)
                
            # Round to 4 decimal places
            final_score = round(final_score, 4)
            
            # Generate reasoning string
            reasoning = generate_reasoning(
                cand, features, is_disqualified, reason, final_score, 
                must_have_skills, similarity_map
            )
            
            # Memory optimization: store only minimal data
            scored_candidates.append((cid, final_score, reasoning))
            
    # 7. Sort candidates descending by score, tie-break by candidate_id ascending
    print("Sorting and ranking candidates...")
    scored_candidates.sort(key=lambda x: (-x[1], x[0]))
    
    # 8. Output Top 100
    top_100 = scored_candidates[:100]
    
    print(f"Writing top 100 candidates to {args.out}...")
    with open(args.out, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
        for rank, (cid, score, reasoning) in enumerate(top_100, 1):
            # Ensure score formatting matches exactly 4 decimal places (e.g. 0.9850)
            score_formatted = f"{score:.4f}"
            writer.writerow([cid, rank, score_formatted, reasoning])
            
    print(f"Successfully ranked {len(scored_candidates)} candidates. Top-1 is {top_100[0][0]} with score {top_100[0][1]}.")

if __name__ == '__main__':
    main()
