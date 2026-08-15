import os
import json
import math
import numpy as np

class EssayClassifier:
    def __init__(self, weights_path="backend/weights.json"):
        self.weights_path = weights_path
        self.mean = None
        self.std = None
        self.coef = None
        self.intercept = None
        self.feature_names = None
        
        # Load weights if they exist, otherwise we will calibrate them
        self.load_weights()

    def load_weights(self):
        if os.path.exists(self.weights_path):
            try:
                with open(self.weights_path, "r") as f:
                    w = json.load(f)
                self.mean = np.array(w["mean"])
                self.std = np.array(w["std"])
                self.coef = np.array(w["coefficients"])
                self.intercept = w["intercept"]
                self.feature_names = w["feature_names"]
                print("Classifier loaded calibrated weights successfully.")
            except Exception as e:
                print(f"Error loading weights.json: {e}. Will require calibration run.")
        else:
            print("Weights file not found. Classifier running on baseline parameters until calibration.")
            # Default fallback weights if not calibrated yet
            self.mean = np.array([50.0, 20.0, 0.6, 0.8, 0.6, 5.0, 0.02])
            self.std = np.array([20.0, 10.0, 0.1, 0.1, 0.1, 2.0, 0.01])
            self.coef = np.array([-1.5, -0.8, 2.5, 1.2, -1.0, -0.5, 1.5])
            self.intercept = 0.5
            self.feature_names = [
                "mean_perplexity", "burstiness", "top10_fraction",
                "top100_fraction", "lexical_diversity", "std_sentence_length",
                "ai_keyword_density"
            ]

    def _sigmoid(self, x):
        return 1.0 / (1.0 + math.exp(-max(min(x, 20.0), -20.0)))

    def predict_sentence_probability(self, sent):
        """Heuristic probability for a single sentence."""
        # A single sentence has: perplexity, rank_fractions (top10, top100), word_count
        ppl = sent["perplexity"]
        t10 = sent["rank_fractions"]["top10"]
        t100 = sent["rank_fractions"]["top100"]
        
        # Formula based on typical token rank distributions:
        # High top10/top100 + low perplexity = AI.
        # Log perplexity: PPL under 10 is typical for AI. PPL over 50 is typical for Human.
        log_ppl = math.log(max(ppl, 1.1))
        
        # z calculation:
        # Baseline: AI text is usually very predictable (low ppl, high top10)
        # We want high z for AI:
        # - High t10 drives z up (+5.0)
        # - High t100 drives z up (+2.5)
        # - High log_ppl drives z down (-1.2)
        z = (5.0 * t10) + (2.5 * t100) - (1.2 * log_ppl) - 0.2
        
        # Adjust for short sentences (less statistical reliability)
        if sent["word_count"] < 6:
            # Shift towards neutral 0.3-0.5
            prob = self._sigmoid(z)
            return 0.3 + 0.4 * prob
            
        return self._sigmoid(z)

    def classify_essay(self, analysis_result):
        """Predicts the overall AI probability for the document."""
        if "error" in analysis_result:
            return {"error": analysis_result["error"]}
            
        metrics = analysis_result["global_metrics"]
        
        # Assemble feature vector
        features = [
            metrics["mean_perplexity"],
            metrics["burstiness"],
            metrics["gltr_fractions"]["top10"],
            metrics["gltr_fractions"]["top100"],
            metrics["lexical_diversity"],
            metrics["std_sentence_length"],
            metrics["ai_keyword_density"]
        ]
        
        # Standardize features
        x_scaled = (np.array(features) - self.mean) / self.std
        
        # Compute logit
        logit = np.dot(self.coef, x_scaled) + self.intercept
        overall_prob = self._sigmoid(logit)
        
        # Sentence-level probabilities
        sentences_out = []
        ai_sentence_count = 0
        
        for sent in analysis_result["sentences"]:
            sent_prob = self.predict_sentence_probability(sent)
            is_ai = sent_prob > 0.55
            if is_ai:
                ai_sentence_count += 1
                
            # Explain sentence flag
            explanation = []
            if sent_prob > 0.55:
                if sent["perplexity"] < 12.0:
                    explanation.append("Extremely high token predictability (Low Perplexity)")
                if sent["rank_fractions"]["top10"] > 0.70:
                    explanation.append(f"{sent['rank_fractions']['top10']*100:.0f}% of words are in the Top 10 most likely selections under GPT-2")
                if sent["word_count"] > 12 and sent["perplexity"] < 20.0:
                    explanation.append("Uniformly smooth flow lacking human complexity spikes")
                if not explanation:
                    explanation.append("Stylistic and statistical properties match machine prose")
            else:
                if sent["perplexity"] > 40.0:
                    explanation.append("High structural complexity (Unpredictable word choices)")
                if sent["rank_fractions"]["other"] > 0.15:
                    explanation.append("Uses unique, low-frequency words (outside Top-1000)")
                if not explanation:
                    explanation.append("Natural human-like writing flow")

            # Get tokens for this sentence
            sent_tokens = [
                {
                    "token": t["token"],
                    "rank": t["rank"],
                    "category": t["category"],
                    "prob": float(t["prob"])
                }
                for t in analysis_result["tokens"]
                if t["start"] >= sent["start"] and t["start"] < sent["end"]
            ]

            sentences_out.append({
                "index": sent["index"],
                "text": sent["text"],
                "start": sent["start"],
                "end": sent["end"],
                "word_count": sent["word_count"],
                "perplexity": float(sent["perplexity"]),
                "ai_probability": float(sent_prob),
                "is_flagged": is_ai,
                "explanation": explanation,
                "rank_fractions": sent["rank_fractions"],
                "tokens": sent_tokens
            })
            
        # Determine ESL heuristic adjustment
        # Non-native English: High top10/top100 ratio, but high perplexity variance (burstiness)
        # and simple vocabulary (lexical diversity < 0.6 but burstiness > 12)
        is_esl_pattern = False
        esl_score = 0.0
        
        # Simple heuristic for ESL:
        # If vocabulary is simplified (high Top-100 fraction > 0.8) and lexical diversity is relatively low
        # BUT they write with high sentence-level complexity spikes (burstiness > 15) or sentence-length variations (std_sentence_length > 6)
        if (metrics["gltr_fractions"]["top100"] > 0.78 and 
            metrics["lexical_diversity"] < 0.65 and 
            (metrics["burstiness"] > 14.0 or metrics["std_sentence_length"] > 6.0)):
            is_esl_pattern = True
            # Compute a strength score for the ESL pattern
            esl_score = min(1.0, (metrics["burstiness"] / 30.0) + (metrics["std_sentence_length"] / 15.0))
            
        # If ESL pattern is strong, we apply a safety adjustment to the overall AI probability to avoid false accusations
        adjusted_prob = overall_prob
        if is_esl_pattern and overall_prob > 0.40:
            # Dampen AI probability: drag it down towards neutral/safe
            adjusted_prob = overall_prob - (0.25 * esl_score)
            adjusted_prob = max(0.15, adjusted_prob)
            
        # Generate global feedback flags
        flags = []
        if adjusted_prob > 0.60:
            flags.append("AI_GENERATED")
            if metrics["ai_keyword_density"] > 0.03:
                flags.append("AI_BUZZWORDS")
            if metrics["std_sentence_length"] < 3.0:
                flags.append("UNIFORM_SENTENCE_RHYTHM")
        elif adjusted_prob > 0.40:
            flags.append("AI_POLISHED")
        else:
            flags.append("HUMAN_WRITTEN")
            
        if is_esl_pattern:
            flags.append("ESL_WRITING_STYLE")

        # Explain global result
        global_explanation = []
        if adjusted_prob > 0.60:
            global_explanation.append("The essay exhibits high predictability and exceptionally uniform sentence rhythms, which are hallmark traits of machine-generated text.")
            if "UNIFORM_SENTENCE_RHYTHM" in flags:
                global_explanation.append(f"Sentence lengths are very uniform (std dev of {metrics['std_sentence_length']:.1f} words), showing a lack of natural human pacing.")
        elif adjusted_prob > 0.40:
            global_explanation.append("The document shows signs of being AI-polished: it retains core narrative concepts but possesses an artificially smoothed sentence flow and typical machine transition terms.")
        else:
            global_explanation.append("The essay displays natural, bursty sentence patterns and unpredictable vocabulary transitions characteristic of human authorship.")
            
        if is_esl_pattern:
            global_explanation.append("Note: The text matches a non-native English (ESL) profile (simplified vocabulary with organic sentence structure variation). The AI score has been calibrated to prevent a false positive.")

        return {
            "overall_ai_probability": float(adjusted_prob),
            "original_ai_probability": float(overall_prob),
            "is_flagged": adjusted_prob > 0.55,
            "flags": flags,
            "global_explanation": global_explanation,
            "ai_sentence_ratio": ai_sentence_count / len(sentences_out) if sentences_out else 0,
            "sentences": sentences_out,
            "global_metrics": {
                "word_count": metrics["word_count"],
                "token_count": metrics["token_count"],
                "mean_sentence_length": float(metrics["mean_sentence_length"]),
                "std_sentence_length": float(metrics["std_sentence_length"]),
                "mean_perplexity": float(metrics["mean_perplexity"]),
                "burstiness": float(metrics["burstiness"]),
                "lexical_diversity": float(metrics["lexical_diversity"]),
                "ai_keyword_density": float(metrics["ai_keyword_density"]),
                "ai_matched_terms": metrics["ai_matched_terms"],
                "gltr_fractions": metrics["gltr_fractions"],
                "esl_calibrated": is_esl_pattern
            }
        }
