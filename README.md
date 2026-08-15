# ProseLens

ProseLens is a premium, locally run, and explainable AI admissions essay detector. Shifting away from black-box scores, ProseLens evaluates personal statements on statistical perplexity footprints, vocabulary rank distributions, and sentence pacing variance.

The user interface implements a stark, modern **Obsidian & Carbon theme** (inspired by Vercel and Linear) with high-contrast typography, watch-face metrics, and a unified single-sheet document canvas.

---

## 🛠️ Tech Stack & Architecture

- **Machine Learning**: Local pre-trained `gpt2` (124M parameters) via Hugging Face `transformers` and **PyTorch** (`torch`).
- **Statistical Pipeline**: Logistic Regression classifier fitted on admissions essay datasets via **scikit-learn** and **numpy** (saved in `backend/weights.json`).
- **Backend API**: **FastAPI** ASGI app hosted via **Uicorn** (`uvicorn`).
- **Frontend Dashboard**: **React 18** + **TypeScript** + **Vite**, styled using custom utility-free **Vanilla CSS**.
- **Bootstrap Automation**: Unified Python runner (`run.py`) to manage installations, asset compiling, model calibrations, and server startup.

---

## 🔬 Core Detection & Safeguard Algorithms

### 1. Vectorized Token Probability & Rank Extraction
Instead of scanning text sequentially in slow loops, ProseLens tokenizes input text and passes it to `gpt2` in vectorized tensor operations:
- **Ranks calculation**: Checks target token logprob against all vocabulary predictions:
  $$\text{Ranks} = \sum (\text{logits}_{\text{shift}} > \text{logits}_{\text{actual}})$$
- **GLTR Vocabulary Footprint**: Categorizes tokens into probability buckets (Top 10, Top 100, Top 1000, and low-frequency creative words). Machine-generated text contains almost zero words outside the Top 100.
- **Arbitrary Length Support**: Input sequences are chunked into 1024-token segments to fit GPT-2 context windows, avoiding position embedding IndexError exceptions.

### 2. Sentence Length Variance (Burstiness)
Humans write in irregular waves—mixing short punchy sentences with long, complex descriptions. Machines generate text with highly uniform, flat distributions. ProseLens tracks the standard deviation of sentence lengths:
$$\text{Burstiness} = \sigma_{\text{sentence lengths}}$$

### 3. ESL Bias Safeguard Heuristic
Traditional AI detectors display massive false-positive rates for non-native English (ESL) writers because they write with simpler, highly repetitive vocabularies (high Top-100 density, low lexical diversity). 

ProseLens resolves this by checking grammatical pacing. When `top100_fraction > 0.78` and `lexical_diversity < 0.65` but the text exhibits organic sentence length variance (`burstiness > 14.0` or `std_sentence_length > 6.0`), ProseLens identifies the ESL signature, dampens the AI probability, and alerts the reviewer to protect the applicant's authorship.

---

## 📁 Repository Structure

Project2/ ├── backend/ │ ├── main.py # FastAPI endpoints, asset hosting, and server routing │ ├── analyzer.py # Token perplexity, GLTR ranking, and offset mapping engine │ ├── classifier.py # Logistic Regression loader and ESL mitigation classifier │ ├── test_analyzer.py # Unit test suite for ML and statistical logic │ ├── requirements.txt # Python dependencies │ └── weights.json # Calibrated Logistic coefficients and scaler mean/std values ├── frontend/ │ ├── package.json # Node package manager configurations │ ├── vite.config.ts # Vite bundler configurations │ ├── tsconfig.json # TypeScript specifications │ ├── index.html # HTML root and Google Font loaders │ └── src/ │ ├── main.tsx # React mounting script │ ├── index.css # Dark carbon colors, grid spacing, and watch-face progress styles │ ├── App.tsx # ProseLens splash screen and single-canvas workspace router │ └── components/ │ ├── EssayInput.tsx # Document editor sheet textarea │ ├── OverviewScore.tsx # Score gauge donut ring and verdict panel │ ├── TextVisualizer.tsx # Document visualizer highlight container │ ├── TokenDetails.tsx # Inspector properties panel showing GLTR token chips │ └── DatasetReport.tsx # Coefficients bar chart and failure case report ├── data/ │ ├── dataset.json # Processed admissions essay corpus (Human, AI, Polished, ESL) │ └── dataset_metadata.md # Calibration results, LOOCV accuracy, and fail analysis ├── scripts/ │ └── prepare_dataset.py # Features extractor and Logistic model fitting script └── run.py # Single-command unified bootstrapper and launcher



---

## 🚀 Getting Started (How to Run)

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.8+** (with `pip` added to PATH)
- **Node.js** (with `npm` added to PATH)

### 2. The Simple Start Command
ProseLens includes a unified bootstrapper script that automates installations and builds. Simply run this command in the project root:

```bash
python run.py
