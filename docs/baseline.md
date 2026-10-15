# Baseline Analysis: Existing Chatbot Project

Audit update, 2026-10-13: this describes the preserved upstream source. Its original manifest is archived in `docs/requirements-baseline.txt`; the supported runtime now uses the pinned shared-foundation dependencies in `requirements.txt`. The legacy Streamlit/GooglePalm path is unverified and its CSV location does not match the current layout. See `docs/known_gaps.md` before attempting to run it.

## 1. Project Overview & Functionality
The existing project is a Question-and-Answer customer support bot built for an e-learning platform ("Nullclass"). It answers learner inquiries regarding courses, bootcamps, prerequisites, and payment options by querying an FAQ knowledge base created from a CSV dataset.

## 2. Entry Points
- UI Entry Point: `src/main.py`
  - Built with Streamlit (`streamlit run src/main.py`).
  - Provides a single-page interface with a button to "Create Knowledgebase" and a text input for asking questions.
- Logic Entry Point: `src/langchain_helper.py`
  - `create_vector_db()`: Loads `dataset.csv` using `CSVLoader` (keyed on `prompt`), creates a vector index using `HuggingFaceInstructEmbeddings("hkunlp/instructor-large")`, and saves the index locally to `faiss_index`.
  - `get_qa_chain()`: Loads the local FAISS index, initializes `GooglePalm` LLM with temperature 0.1, creates a retriever with `score_threshold=0.7`, and returns a `RetrievalQA` chain.

## 3. Dataset
- File: `dataset/dataset.csv`
- Schema: `prompt,response`
- Content: Predefined question-answer pairs regarding Nullclass courses, bootcamps, refund policy, Mac compatibility, etc.

## 4. Dependencies
Defined in `requirements.txt`:
- `langchain==0.0.339`
- `python-dotenv==1.0.0`
- `streamlit==1.22.0`
- `tiktoken==0.4.0`
- `faiss-cpu==1.7.4`
- `protobuf~=3.19.0`
- `sentence-transformer== 2.2.2`

## 5. How to Run Baseline Bot
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env`:
   ```bash
   GOOGLE_API_KEY="your_api_key_here"
   ```
3. Run Streamlit app:
   ```bash
   streamlit run src/main.py
   ```

## 6. Gaps & Extension Points
1. **API & Orchestration**: Currently restricted to Streamlit UI. We will extend in place with `app/chatbot.py` orchestrator exposing a modern FastAPI API.
2. **Security & RBAC**: No access control, prompt-injection defense, or PII masking exists.
3. **Time & Clock**: Hardcoded or implicit time; lacks any `Clock` interface or time travel for testing.
4. **Metadata & Temporal Retrieval (Task 4)**: The baseline FAISS index has no document metadata (effective dates, expiry dates, access levels, versioning, conflict resolution, or document families).
5. **Factual Grounding & Verification (Task 4)**: Baseline outputs LLM responses without citation checking, claim verification, or hallucination rejection.
6. **Observability**: Missing structured audit logging and performance metrics.
