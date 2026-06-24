"""
Redrob Intelligent Candidate Ranker — Streamlit Demo
Run: streamlit run demo/app.py
"""
import sys
import os
import json
import csv
import io

# Add parent to sys.path so local modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(
    page_title="Redrob Candidate Ranker",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* Hero header */
.hero-header {
    text-align: center;
    padding: 2rem 1rem 1rem;
}
.hero-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 300;
}

/* Card style */
.rank-card {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    backdrop-filter: blur(8px);
    transition: all 0.2s ease;
}
.rank-card:hover {
    background: rgba(255,255,255,0.12);
    border-color: rgba(167,139,250,0.5);
    transform: translateX(4px);
}
.rank-num {
    font-size: 1.4rem;
    font-weight: 800;
    color: #a78bfa;
    display: inline-block;
    width: 40px;
}
.cand-id { color: #60a5fa; font-weight: 600; font-size: 0.9rem; }
.score-badge {
    background: linear-gradient(90deg, #a78bfa, #60a5fa);
    color: white;
    padding: 2px 10px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
}
.reasoning-text { color: #cbd5e1; font-size: 0.85rem; margin-top: 0.3rem; }

/* Sidebar styling */
section[data-testid="stSidebar"] { background: rgba(15,12,41,0.9); }
section[data-testid="stSidebar"] label { color: #94a3b8 !important; }

/* Metric cards */
.metric-box {
    background: rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.1);
}
.metric-value { font-size: 2rem; font-weight: 800; color: #a78bfa; }
.metric-label { color: #94a3b8; font-size: 0.8rem; margin-top: 0.2rem; }

/* Upload zone */
.upload-zone {
    border: 2px dashed rgba(167,139,250,0.4);
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    color: #94a3b8;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🎯 Redrob Candidate Ranker</div>
    <div class="hero-subtitle">Intelligent Candidate Discovery & Ranking · Senior AI Engineer Role</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    mode = st.radio("Input Mode", ["Upload Candidates JSON", "Load Pre-computed submission.csv"])

    st.markdown("---")
    st.markdown("### 📋 Scoring Weights")
    w_skills     = st.slider("Skills Match",          0, 100, 35)
    w_career     = st.slider("Career Trajectory",      0, 100, 25)
    w_experience = st.slider("Experience Alignment",  0, 100, 15)
    w_location   = st.slider("Location/Availability", 0, 100, 10)
    w_education  = st.slider("Education",              0, 100,  5)

    st.markdown("---")
    st.markdown("### 🔍 Filters")
    min_score    = st.slider("Minimum Score", 0.0, 1.0, 0.0, 0.01)
    show_top_n   = st.slider("Show Top N", 10, 100, 50)

# ── Main Area ─────────────────────────────────────────────────────────────────
if mode == "Load Pre-computed submission.csv":
    default_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "submission.csv")

    csv_file = st.file_uploader("Upload submission.csv", type=["csv"]) if not os.path.exists(default_csv) else None

    results = []

    if csv_file:
        reader = csv.DictReader(io.StringIO(csv_file.getvalue().decode("utf-8")))
        results = list(reader)
    elif os.path.exists(default_csv):
        st.info(f"Auto-loading `submission.csv` from repo root.")
        with open(default_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            results = list(reader)

    if results:
        # Filter and cap
        results = [r for r in results if float(r["score"]) >= min_score]
        results = results[:show_top_n]

        # Metrics row
        scores = [float(r["score"]) for r in results]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="metric-box"><div class="metric-value">{len(results)}</div><div class="metric-label">Candidates Shown</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-box"><div class="metric-value">{max(scores):.3f}</div><div class="metric-label">Top Score</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-box"><div class="metric-value">{min(scores):.3f}</div><div class="metric-label">Min Score (shown)</div></div>', unsafe_allow_html=True)
        with col4:
            avg = sum(scores) / len(scores)
            st.markdown(f'<div class="metric-box"><div class="metric-value">{avg:.3f}</div><div class="metric-label">Avg Score</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🏆 Ranked Candidates")

        for r in results:
            rank = r["rank"]
            cid  = r["candidate_id"]
            score = float(r["score"])
            reasoning = r["reasoning"]

            # Colour gradient: green → amber → red
            hue = int(120 * score)
            bar_color = f"hsl({hue}, 80%, 55%)"

            st.markdown(f"""
            <div class="rank-card">
                <span class="rank-num">#{rank}</span>
                <span class="cand-id">{cid}</span>
                &nbsp;&nbsp;
                <span class="score-badge">{score:.4f}</span>
                <div class="reasoning-text">💬 {reasoning}</div>
            </div>
            """, unsafe_allow_html=True)

        # Download button
        csv_out = "candidate_id,rank,score,reasoning\n"
        for r in results:
            csv_out += f"{r['candidate_id']},{r['rank']},{r['score']},{r['reasoning']}\n"
        st.download_button("⬇️ Download Filtered CSV", csv_out, "filtered_results.csv", "text/csv")

    else:
        st.markdown("""
        <div class="upload-zone">
            <h3>📂 No results loaded</h3>
            <p>Run <code>rank.py</code> first to generate <code>submission.csv</code>, or upload a CSV file above.</p>
        </div>
        """, unsafe_allow_html=True)

else:  # Upload Candidates JSON mode
    st.markdown("### 📤 Upload Candidate Profiles (JSON array)")
    uploaded = st.file_uploader("Upload a JSON file with candidate profiles", type=["json"])

    if uploaded:
        try:
            candidates = json.loads(uploaded.getvalue().decode("utf-8"))
            if not isinstance(candidates, list):
                candidates = [candidates]

            st.success(f"Loaded {len(candidates)} candidate(s). Running scorer...")

            from jd_parser import JobDescriptionParser
            from feature_extractor import CandidateFeatureExtractor
            from disqualifiers import evaluate_disqualifiers
            from scorer import calculate_final_score

            jd_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "[PUB] India_runs_data_and_ai_challenge",
                "[PUB] India_runs_data_and_ai_challenge",
                "India_runs_data_and_ai_challenge",
                "job_description.docx"
            )
            parser = JobDescriptionParser(jd_path if os.path.exists(jd_path) else None)
            reqs = parser.get_requirements()

            # Optional: Load local SentenceTransformer model if available to compute skills similarity
            similarity_map = {}
            model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "all-MiniLM-L6-v2")
            if os.path.exists(model_dir):
                try:
                    from sentence_transformers import SentenceTransformer, util
                    model = SentenceTransformer(model_dir)
                    unique_skills = set()
                    for cand in candidates:
                        for s in cand.get('skills', []):
                            name = s.get('name')
                            if name:
                                unique_skills.add(name.lower().strip())
                    jd_skills = set(reqs.get('must_have_skills', []) + reqs.get('nice_to_have_skills', []))
                    if unique_skills and jd_skills:
                        unique_skills_list = list(unique_skills)
                        jd_skills_list = list(jd_skills)
                        cand_embeddings = model.encode(unique_skills_list, convert_to_tensor=True)
                        jd_embeddings = model.encode(jd_skills_list, convert_to_tensor=True)
                        cosine_scores = util.cos_sim(cand_embeddings, jd_embeddings).cpu().numpy()
                        for i, cand_s in enumerate(unique_skills_list):
                            for j, jd_s in enumerate(jd_skills_list):
                                similarity_map[(cand_s, jd_s)] = float(cosine_scores[i][j])
                except Exception as e:
                    st.warning(f"Failed to load sentence-transformers: {e}. Falling back to exact string match.")

            extractor = CandidateFeatureExtractor(reqs, similarity_map=similarity_map)

            results = []
            for cand in candidates:
                cid = cand.get("candidate_id", "UNKNOWN")
                features = extractor.extract_features(cand)
                is_disq, reason, cap = evaluate_disqualifiers(cand)
                score = calculate_final_score(
                    features["skills_score"], features["career_score"],
                    features["experience_score"], features["location_score"],
                    features["education_score"], features["behavioral_multiplier"]
                )
                if is_disq:
                    score = min(score, cap)
                results.append({
                    "candidate_id": cid,
                    "score": score,
                    "reason": reason,
                    "features": features,
                    "disqualified": is_disq,
                })

            results.sort(key=lambda x: (-x["score"], x["candidate_id"]))

            st.markdown("### 📊 Score Breakdown")
            for i, r in enumerate(results[:show_top_n], 1):
                with st.expander(f"#{i}  {r['candidate_id']}  —  Score: {r['score']:.4f}  {'🚫' if r['disqualified'] else '✅'}"):
                    cols = st.columns(5)
                    feat = r["features"]
                    cols[0].metric("Skills",     f"{feat['skills_score']:.2f}")
                    cols[1].metric("Career",     f"{feat['career_score']:.2f}")
                    cols[2].metric("Experience", f"{feat['experience_score']:.2f}")
                    cols[3].metric("Location",   f"{feat['location_score']:.2f}")
                    cols[4].metric("Education",  f"{feat['education_score']:.2f}")
                    st.caption(f"Behavioral multiplier: {feat['behavioral_multiplier']:.2f}")
                    if r["disqualified"]:
                        st.warning(f"⚠️ {r['reason']}")

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.markdown("""
        <div class="upload-zone">
            <h3>📂 Upload a JSON file</h3>
            <p>Upload a JSON array of candidate profiles to score them interactively.</p>
        </div>
        """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#475569;font-size:0.8rem;">Redrob Intelligent Candidate Ranker · Built for the India Runs Data & AI Challenge</div>',
    unsafe_allow_html=True
)
