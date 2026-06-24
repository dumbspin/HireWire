import os
import re

try:
    import docx
except ImportError:
    docx = None


class JobDescriptionParser:
    def __init__(self, jd_path=None):
        self.jd_path = jd_path

        # === MUST-HAVE skills (derived from JD "Things you absolutely need") ===
        self.must_have_skills = [
            # Embeddings & retrieval
            'embeddings', 'sentence-transformers', 'bge', 'e5', 'openai embeddings',
            'dense retrieval', 'semantic search',
            # Vector DBs / hybrid search
            'vector database', 'pinecone', 'weaviate', 'qdrant', 'milvus',
            'faiss', 'elasticsearch', 'opensearch', 'pgvector',
            # Ranking evaluation
            'ndcg', 'mrr', 'map', 'learning to rank', 'ranking systems',
            'information retrieval', 'information retrieval systems',
            # Core Python / ML fundamentals
            'python',
            # Hybrid / RAG
            'rag', 'hybrid search', 'bm25', 'indexing algorithms',
        ]

        # === NICE-TO-HAVE (bonus, not required) ===
        self.nice_to_have_skills = [
            'lora', 'qlora', 'peft', 'fine-tuning llms', 'model adaptation',
            'learning to rank', 'xgboost', 'recommendation systems',
            'content matching', 'ranking systems',
            'distributed systems', 'mlops', 'kubeflow', 'mlflow',
            'open-source ml libraries', 'hugging face transformers',
            'haystack', 'langchain', 'llamaindex',
            'pytorch', 'deep learning', 'machine learning',
            'nlp', 'natural language processing', 'llms',
            'data pipelines', 'feature engineering',
        ]

        # === Location preferences ===
        # Pune, Noida, Delhi NCR are primary; Hyderabad/Mumbai/Bangalore also welcomed
        self.preferred_cities = [
            'noida', 'pune', 'delhi', 'ncr', 'new delhi',
            'hyderabad', 'mumbai', 'bengaluru', 'bangalore',
            'gurugram', 'gurgaon',
        ]

        # === Experience target (5-9 years, ideal 6-8) ===
        self.experience_range = {'min': 5, 'max': 9, 'ideal': 7}

        # === Notice period preference ===
        self.notice_preference = {'preferred_max': 30, 'hard_max': 90}

        if jd_path and os.path.exists(jd_path):
            self._parse_docx()

    def _parse_docx(self):
        """Try to enrich defaults from the actual docx content."""
        if not docx:
            return
        try:
            doc = docx.Document(self.jd_path)
            full_text = '\n'.join(p.text for p in doc.paragraphs).lower()

            # Extract experience range if stated explicitly
            m = re.search(r'experience required:\s*(\d+)[–\-](\d+)\s*years', full_text)
            if m:
                self.experience_range['min'] = int(m.group(1))
                self.experience_range['max'] = int(m.group(2))
        except Exception:
            pass  # fall back to hardcoded defaults

    def get_requirements(self):
        return {
            'must_have_skills': self.must_have_skills,
            'nice_to_have_skills': self.nice_to_have_skills,
            'preferred_cities': self.preferred_cities,
            'experience_range': self.experience_range,
            'notice_preference': self.notice_preference,
        }


if __name__ == '__main__':
    jd = r"d:\resume_ranker\[PUB] India_runs_data_and_ai_challenge\[PUB] India_runs_data_and_ai_challenge\India_runs_data_and_ai_challenge\job_description.docx"
    parser = JobDescriptionParser(jd)
    reqs = parser.get_requirements()
    print(f"Must-have skills ({len(reqs['must_have_skills'])}):", reqs['must_have_skills'])
    print(f"Nice-to-have skills ({len(reqs['nice_to_have_skills'])}):", reqs['nice_to_have_skills'])
    print("Experience range:", reqs['experience_range'])
