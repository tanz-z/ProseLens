import re
import math
import string
import torch
import numpy as np
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

class TextAnalyzer:
    def __init__(self, model_name="gpt2"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading analyzer model '{model_name}' on device: {self.device}...")
        
        # Load fast tokenizer and model
        self.tokenizer = GPT2TokenizerFast.from_pretrained(model_name)
        self.model = GPT2LMHeadModel.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Standard AI stylistic keywords / patterns (admissions essays focus)
        self.ai_keywords = [
            r"\bdelve\b", r"\btapestry\b", r"\bmultifaceted\b", r"\btestament\b",
            r"\bmoreover\b", r"\bfurthermore\b", r"\bnot only\b.*\bbut also\b",
            r"\bin conclusion\b", r"\bit is important to\b", r"\bit is crucial to\b",
            r"\bbeacons?\b", r"\bprofound impact\b", r"\bjourney of growth\b",
            r"\bshaping my\b", r"\bpassion for\b", r"\bfostered a\b",
            r"\bintricate\b", r"\btransformative\b", r"\bparamount\b"
        ]

    def _split_sentences(self, text):
        """Splits text into sentences while retaining character positions."""
        # Simple robust sentence splitter
        sentence_ends = re.finditer(r'[^.!?\s][^.!?]*(?:[.!?]+|(?=\s*$))', text)
        sentences = []
        for match in sentence_ends:
            sentences.append({
                "text": match.group(0),
                "start": match.start(),
                "end": match.end()
            })
        return sentences

    def _calculate_ttr(self, text):
        """Type-Token Ratio for lexical diversity."""
        # Strip punctuation and convert to lowercase
        translator = str.maketrans('', '', string.punctuation)
        words = text.translate(translator).lower().split()
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    def _get_esl_indicators(self, text, words):
        """Linguistic flags that indicate human ESL writing style (e.g. spelling errors, simpler grammatical structures, high perplexity variance)."""
        # Simplistic heuristic: ESL writers tend to write with high variance in perplexity,
        # lower spelling complexity, but also less AI-like structure.
        # We can look for common spelling or minor grammar markers if we want,
        # but here we focus on vocab profile + syntax.
        text_lower = text.lower()
        
        # Passive voice count
        passive_voice = len(re.findall(r"\b(am|is|are|was|were|be|been|being)\b\s+\w+ed\b", text_lower))
        
        # Spelling errors estimation (simple check of rare words that might be typos)
        # For simplicity, we compare word usage patterns.
        # Simple word length distributions:
        word_lengths = [len(w) for w in words if w.isalpha()]
        avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0.0
        
        return {
            "passive_voice_count": passive_voice,
            "avg_word_length": avg_word_length,
        }

    def analyze(self, text):
        """Analyzes text at token, sentence, and document levels."""
        if not text or not text.strip():
            return {"error": "Text is empty"}
        
        # Split text into sentences
        raw_sentences = self._split_sentences(text)
        if not raw_sentences:
            # Fallback if splitter fails
            raw_sentences = [{"text": text, "start": 0, "end": len(text)}]

        # Tokenize whole text
        inputs = self.tokenizer(text, return_tensors="pt", return_offsets_mapping=True)
        input_ids = inputs["input_ids"].to(self.device)
        offsets = inputs["offset_mapping"][0].tolist()
        
        seq_len = input_ids.shape[1]
        
        if seq_len <= 1:
            return {"error": "Text is too short to analyze"}

        # Model forward pass (processed in chunks of 1024 to prevent position embedding IndexErrors)
        max_chunk_len = 1024
        logits_list = []
        with torch.no_grad():
            for i in range(0, seq_len, max_chunk_len):
                chunk_ids = input_ids[:, i : i + max_chunk_len]
                chunk_outputs = self.model(chunk_ids)
                logits_list.append(chunk_outputs.logits)
            logits = torch.cat(logits_list, dim=1) # (1, seq_len, vocab_size)

        # Shift logits and labels for prediction alignment
        shift_logits = logits[0, :-1, :]  # (seq_len - 1, vocab_size)
        shift_labels = input_ids[0, 1:]   # (seq_len - 1,)
        
        # Compute probabilities, log probabilities and ranks
        log_probs = torch.log_softmax(shift_logits, dim=-1)
        probs = torch.softmax(shift_logits, dim=-1)
        
        token_log_probs = log_probs[range(len(shift_labels)), shift_labels].tolist()
        token_probs = probs[range(len(shift_labels)), shift_labels].tolist()
        
        # Vectorized rank calculation (number of vocab elements with higher logit)
        actual_logits = shift_logits[range(len(shift_labels)), shift_labels].unsqueeze(1)
        ranks = torch.sum(shift_logits > actual_logits, dim=-1).tolist()
        
        # Vectorized entropy calculation
        entropies = (-torch.sum(probs * log_probs, dim=-1)).tolist()
        
        # Reconstruct token details list
        # token at index 0 has no prediction context, so we assign baseline values
        token_details = [{
            "token": self.tokenizer.decode([input_ids[0, 0].item()]),
            "id": input_ids[0, 0].item(),
            "start": offsets[0][0],
            "end": offsets[0][1],
            "log_prob": 0.0,
            "prob": 1.0,
            "rank": 0,
            "entropy": 0.0,
            "category": "top10"
        }]
        
        for i in range(1, seq_len):
            rank = ranks[i-1]
            if rank < 10:
                cat = "top10"      # Green
            elif rank < 100:
                cat = "top100"     # Yellow
            elif rank < 1000:
                cat = "top1000"    # Red
            else:
                cat = "other"      # Violet
                
            token_details.append({
                "token": self.tokenizer.decode([input_ids[0, i].item()]),
                "id": input_ids[0, i].item(),
                "start": offsets[i][0],
                "end": offsets[i][1],
                "log_prob": token_log_probs[i-1],
                "prob": token_probs[i-1],
                "rank": rank,
                "entropy": entropies[i-1],
                "category": cat
            })
            
        # Group tokens into sentences
        sentence_details = []
        for idx, sent in enumerate(raw_sentences):
            sent_start = sent["start"]
            sent_end = sent["end"]
            
            # Find tokens that belong to this sentence based on character offsets
            sent_tokens = [
                tok for tok in token_details 
                # Token belongs if its start character falls within the sentence bounds
                if (tok["start"] >= sent_start and tok["start"] < sent_end)
            ]
            
            if not sent_tokens:
                continue
                
            # Compute sentence metrics
            # Ignore token at index 0 for perplexity if it's the absolute start of text
            valid_toks = [tok for tok in sent_tokens if tok["start"] > 0]
            if not valid_toks:
                valid_toks = sent_tokens # fallback
                
            sum_log_prob = sum(tok["log_prob"] for tok in valid_toks)
            avg_log_prob = sum_log_prob / len(valid_toks)
            perplexity = math.exp(-avg_log_prob) if avg_log_prob > -100 else 1e10
            
            avg_entropy = sum(tok["entropy"] for tok in valid_toks) / len(valid_toks)
            avg_rank = sum(tok["rank"] for tok in valid_toks) / len(valid_toks)
            
            # Rank counts
            t10 = sum(1 for tok in valid_toks if tok["category"] == "top10")
            t100 = sum(1 for tok in valid_toks if tok["category"] == "top100")
            t1000 = sum(1 for tok in valid_toks if tok["category"] == "top1000")
            t_other = sum(1 for tok in valid_toks if tok["category"] == "other")
            total_toks = len(valid_toks)
            
            # Sentence word count
            word_count = len(sent["text"].split())
            
            sentence_details.append({
                "index": idx,
                "text": sent["text"],
                "start": sent_start,
                "end": sent_end,
                "word_count": word_count,
                "token_count": len(sent_tokens),
                "perplexity": perplexity,
                "avg_entropy": avg_entropy,
                "avg_rank": avg_rank,
                "rank_counts": {
                    "top10": t10,
                    "top100": t100,
                    "top1000": t1000,
                    "other": t_other
                },
                "rank_fractions": {
                    "top10": t10 / total_toks if total_toks > 0 else 0,
                    "top100": t100 / total_toks if total_toks > 0 else 0,
                    "top1000": t1000 / total_toks if total_toks > 0 else 0,
                    "other": t_other / total_toks if total_toks > 0 else 0
                }
            })
            
        # Global metrics
        all_words = text.split()
        total_words = len(all_words)
        
        # Sentence length statistics
        sent_lengths = [s["word_count"] for s in sentence_details]
        mean_sent_length = np.mean(sent_lengths) if sent_lengths else 0.0
        std_sent_length = np.std(sent_lengths) if sent_lengths else 0.0
        
        # Sentence perplexity statistics
        sent_ppls = [s["perplexity"] for s in sentence_details if s["perplexity"] < 1e5] # exclude extreme outliers
        mean_ppl = np.mean(sent_ppls) if sent_ppls else 0.0
        std_ppl = np.std(sent_ppls) if sent_ppls else 0.0  # Burstiness representation
        
        # Global GLTR fractions (excluding first token)
        g_valid_toks = token_details[1:] if len(token_details) > 1 else token_details
        g_total = len(g_valid_toks)
        g_t10 = sum(1 for t in g_valid_toks if t["category"] == "top10")
        g_t100 = sum(1 for t in g_valid_toks if t["category"] == "top100")
        g_t1000 = sum(1 for t in g_valid_toks if t["category"] == "top1000")
        g_other = sum(1 for t in g_valid_toks if t["category"] == "other")
        
        # Lexical Diversity
        ttr = self._calculate_ttr(text)
        
        # AI keywords match
        ai_pattern_matches = 0
        ai_matched_terms = []
        for pattern in self.ai_keywords:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                ai_pattern_matches += matches
                ai_matched_terms.append(pattern.replace(r"\b", "").replace(r"\s+", " "))
                
        ai_keyword_density = ai_pattern_matches / total_words if total_words > 0 else 0.0
        
        # ESL Heuristics
        esl_metrics = self._get_esl_indicators(text, all_words)
        
        # Return structured analysis results
        return {
            "text": text,
            "global_metrics": {
                "word_count": total_words,
                "token_count": seq_len,
                "mean_sentence_length": mean_sent_length,
                "std_sentence_length": std_sent_length,  # Rhythm evenness
                "mean_perplexity": mean_ppl,
                "burstiness": std_ppl,                  # Perplexity variance
                "lexical_diversity": ttr,               # Vocab richness
                "ai_keyword_density": ai_keyword_density,
                "ai_matched_terms": ai_matched_terms,
                "gltr_fractions": {
                    "top10": g_t10 / g_total if g_total > 0 else 0,
                    "top100": g_t100 / g_total if g_total > 0 else 0,
                    "top1000": g_t1000 / g_total if g_total > 0 else 0,
                    "other": g_other / g_total if g_total > 0 else 0
                },
                "passive_voice_density": esl_metrics["passive_voice_count"] / total_words if total_words > 0 else 0.0,
                "avg_word_length": esl_metrics["avg_word_length"]
            },
            "sentences": sentence_details,
            "tokens": token_details
        }
