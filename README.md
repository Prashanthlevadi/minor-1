# 🚨 AI Contradiction Detector

> **Automated Factual, Legal & Policy Contradiction Audit Engine** powered by Python 3.11+, PyMuPDF, Pydantic, LLMs (Gemini/OpenAI), and Streamlit.

---

## 📌 Project Overview & Roadmap

The **AI Contradiction Detector** analyzes two text-based documents or PDFs, extracts structured factual claims (using Pydantic validation), aligns corresponding statements, and detects logical, numerical, temporal, or policy contradictions with high precision and visual severity grading.

### 5-Step Project Pipeline:
1. **UNDERSTAND**: Define problem statement, claim types, and contradiction criteria.
2. **DESIGN**: Modular package architecture (`src/`), Pydantic models (`Claim`, `ClaimPair`, `ContradictionResult`), and Streamlit UI mockup.
3. **BUILD**: Robust text cleaning, PyMuPDF PDF parsing, semantic matching, and dual LLM/Heuristic analysis engine.
4. **TEST**: Comprehensive automated test cases in `tests/test_cases.json` run with `pytest`.
5. **DEPLOY**: Interactive Streamlit web interface with visual Plotly metrics and multi-format report exports (JSON, MD, HTML).

---

## 🛠️ Technology Stack

| Component | Tool | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.11+ | Core NLP and AI logic development |
| **Interface** | Streamlit + Custom CSS | Fast, interactive modern Web UI |
| **PDF Parsing** | PyMuPDF (`fitz`) | Reliable text extraction from PDF documents |
| **LLM Integration** | Google Gemini API / OpenAI API | Structured claim extraction and contradiction analysis |
| **Validation** | Pydantic v2 | Schema validation for claims and contradiction outputs |
| **Data Viz** | Plotly | Dynamic donut charts and category breakdown graphs |
| **Configuration** | `python-dotenv` | API key isolation and environment configuration |
| **Testing** | `pytest` | Automated verification suite |

---

## 📁 Project Structure

```
ai-contradiction-detector/
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Project Python dependencies
├── .env                        # Environment variables (ignored by Git)
├── .env.example                # Example API key template
├── .gitignore                  # Git exclusion rules
├── README.md                   # Project documentation & build guide
├── src/                        # Core modular source package
│   ├── __init__.py
│   ├── pdf_reader.py           # PyMuPDF PDF reader & text file loader
│   ├── cleaner.py              # Text cleaning & sentence segmentation
│   ├── claims.py               # Pydantic structured claim extractor
│   ├── matcher.py              # Semantic claim pairing & alignment engine
│   ├── comparator.py           # Contradiction analyzer & severity grader
│   └── report.py               # Multi-format report builder (JSON/MD/HTML)
├── data/
│   └── samples/                # Sample test document pairs
│       ├── sample_contract_v1.txt
│       ├── sample_contract_v2.txt
│       ├── sample_policy_2023.txt
│       └── sample_policy_2024.txt
└── tests/
    ├── __init__.py
    ├── test_cases.json         # Benchmark contradiction test cases
    └── test_contradiction.py   # Automated pytest unit test suite
```

---

## 🚀 Quick Start & Installation

### 1. Activate Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure API Key
Create a `.env` file or set environment variables:
```env
GEMINI_API_KEY=your_gemini_api_key_here
# or
OPENAI_API_KEY=your_openai_api_key_here
```
> *Note: If no API key is supplied, the application automatically uses its high-precision **Offline Rule-Based NLP Engine**.*

### 4. Run Web Application
```bash
streamlit run app.py
```

### 5. Run Automated Unit Tests
```bash
python -m pytest tests/test_contradiction.py
```

---

## 🧪 Pass Conditions Check

| Check | Pass Condition | Status |
| :--- | :--- | :--- |
| **Environment** | Virtual environment activates and dependencies install clean | ✅ PASSED |
| **UI** | Streamlit page opens with modern dashboard | ✅ PASSED |
| **Input** | Two files (PDF/TXT) or text blocks can be supplied | ✅ PASSED |
| **Extraction** | Text and Pydantic claims visible for both sources | ✅ PASSED |
| **Safety** | API keys stored in `.env` and ignored by Git | ✅ PASSED |

---

## 📜 License
MIT License - Built for AI Contradiction Audit Projects.
