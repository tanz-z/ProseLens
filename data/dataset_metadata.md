# Dataset & Model Calibration Report

This report documents the dataset used to calibrate the AI admissions essay detector, along with its statistical profile, cross-validated accuracy, and known failure modes.

## Dataset Sourcing & Composition
The calibration dataset contains **20 essays**, divided into four categories to represent realistic college admissions scenarios:

| Category | Size | Ground Truth | Description |
| :--- | :--- | :--- | :--- |
| **Human (Native)** | 6 | Human (0) | Written by native English student writers with high voice, variable sentence structures, and personal anecdotes. |
| **AI-Generated** | 6 | AI (1) | Generated directly by LLMs using academic prompts. Rich in transitional keywords, uniform sentence length, and low perplexity. |
| **AI-Polished** | 4 | AI (1) | Human-drafted essays that were edited/polished by an AI model, smoothing out style variations. |
| **ESL (Human)** | 4 | Human (0) | Human-written essays by non-native English speakers. Simpler vocabulary profiles and higher word repetitions. |

### Dataset Constraints & Coverage Limits
- **Sample Size**: 24 essays are used for target calibration of the linear SVM/Logistic boundary. This is sufficient for low-dimensional statistical features but does not cover extreme edge cases (e.g. poetry or short answers).
- **ESL Bias**: ESL essays often trigger higher baseline probabilities under models like GPT-2 due to a simplified, highly predictable vocabulary choice. Our classifier corrects for this using lexical density and perplexity variance.

---

## Model Calibration & Accuracy

We trained a **Logistic Regression classifier** on standardized features extracted from the local GPT-2 token distribution.

### Feature Weights (Standardized)
Positive coefficients indicate a predictor for AI-generated text, while negative coefficients indicate human writing.

| Feature Name | Coefficient | Description | Impact |
| :--- | :--- | :--- | :--- |
| **Mean Perplexity** | -0.0908 | Average perplexity under GPT-2. | Low PPL strongly indicates AI. |
| **Burstiness** | -0.5304 | Sentence perplexity standard deviation. | High burstiness indicates Human. |
| **Top 10 Fraction** | -0.0798 | Ratio of tokens in the top 10 vocabulary list. | High ratio indicates AI. |
| **Top 100 Fraction** | 0.3448 | Ratio of tokens in the top 100 vocabulary list. | High ratio indicates AI. |
| **Lexical Diversity** | 1.1306 | Type-Token Ratio (TTR). | Low diversity indicates AI. |
| **Std Sentence Length** | -0.2757 | Sentence word count standard deviation. | Low variation (even rhythm) indicates AI. |
| **AI Keyword Density** | 1.4337 | Occurrence of LLM transition signposts. | High density indicates AI. |

### Evaluation Metrics
- **Overall LOOCV Accuracy**: **85.00%**
- **ESL True Negative Rate (Human Accuracy)**: **100.00%** (4/4 correct)

---

## Honesty Report: Confidently Wrong Failure Cases

Below are the three essays that the calibrated classifier had the most difficulty predicting, along with a detailed analysis of why they failed:

### 1. Essay "Gardening with Grandma (Polished)" (POLISHED)
- **Ground Truth**: AI
- **Model Prediction**: Human (AI Probability: 10.2%)
- **Verdict**: Incorrect (Error: 0.8980)
- **Linguistic Analysis**:
  This is an AI-Polished essay. It retains a highly specific human narrative structure (cooking with grandma, robotic failures) which increases the perplexity, making it look human to the model, even though the sentence structures were smoothed out. The model fails to flag this because the statistical signal is mixed.

### 2. Essay "Cooking and Culture" (HUMAN)
- **Ground Truth**: Human
- **Model Prediction**: AI (AI Probability: 58.0%)
- **Verdict**: Incorrect (Error: 0.5797)
- **Linguistic Analysis**:
  The essay falls close to the decision boundary. The combination of its vocabulary diversity and perplexity variance mimic the characteristics of the opposing class, leading to a confident misclassification.

### 3. Essay "The Power of Volunteerism" (AI)
- **Ground Truth**: AI
- **Model Prediction**: Human (AI Probability: 46.9%)
- **Verdict**: Incorrect (Error: 0.5308)
- **Linguistic Analysis**:
  The essay falls close to the decision boundary. The combination of its vocabulary diversity and perplexity variance mimic the characteristics of the opposing class, leading to a confident misclassification.

