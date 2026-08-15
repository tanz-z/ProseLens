import unittest
import sys
import os

# Append project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.analyzer import TextAnalyzer

class TestTextAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the analyzer once for the tests
        # This will use the cached model from our calibration run
        cls.analyzer = TextAnalyzer()

    def test_split_sentences(self):
        text = "This is the first sentence! Here is another one. And a third?"
        sentences = self.analyzer._split_sentences(text)
        
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0]["text"], "This is the first sentence!")
        self.assertEqual(sentences[1]["text"], "Here is another one.")
        self.assertEqual(sentences[2]["text"], "And a third?")
        
        # Verify indices match
        for s in sentences:
            self.assertEqual(text[s["start"]:s["end"]], s["text"])

    def test_calculate_ttr(self):
        text_diverse = "The quick brown fox jumps over the lazy dog"
        text_repetitive = "dog dog dog dog dog dog dog dog dog dog"
        
        ttr_diverse = self.analyzer._calculate_ttr(text_diverse)
        ttr_repetitive = self.analyzer._calculate_ttr(text_repetitive)
        
        self.assertGreater(ttr_diverse, 0.8)
        self.assertLess(ttr_repetitive, 0.2)

    def test_analyze_empty_and_short_inputs(self):
        res_empty = self.analyzer.analyze("")
        self.assertIn("error", res_empty)
        
        res_short = self.analyzer.analyze(".")
        self.assertIn("error", res_short)

    def test_analyze_valid_input(self):
        text = (
            "Every Sunday morning, my kitchen transforms into a battleground of flour, "
            "spices, and loud voices. My grandmother, the undisputed commander, stands at the "
            "stove, her wooden spoon pointing at me like a baton. In our family, recipes are "
            "suggestions, and cooking is done by feel. This chaotic kitchen is where I learned "
            "the value of adaptability."
        )
        res = self.analyzer.analyze(text)
        
        self.assertNotIn("error", res)
        self.assertIn("global_metrics", res)
        self.assertIn("sentences", res)
        self.assertIn("tokens", res)
        
        metrics = res["global_metrics"]
        self.assertGreater(metrics["word_count"], 15)
        self.assertGreater(metrics["mean_perplexity"], 1.0)
        self.assertGreater(metrics["burstiness"], 0.0)
        self.assertGreater(metrics["lexical_diversity"], 0.5)

    def test_analyze_long_input(self):
        # Generate an input with more than 1024 tokens by repeating a sentence
        long_sentence = "Admissions essays represent a unique opportunity for students to share their personal stories. "
        long_text = long_sentence * 130
        
        res = self.analyzer.analyze(long_text)
        self.assertNotIn("error", res)
        self.assertIn("global_metrics", res)
        self.assertGreater(res["global_metrics"]["token_count"], 1024)

if __name__ == "__main__":
    unittest.main()
