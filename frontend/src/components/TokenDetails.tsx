import React, { useState } from "react";
import { Info, HelpCircle } from "lucide-react";

interface TokenDetail {
  token: string;
  rank: number;
  category: string;
  prob: number;
}

interface SentenceResult {
  index: number;
  text: string;
  start: number;
  end: number;
  word_count: number;
  perplexity: number;
  ai_probability: number;
  is_flagged: boolean;
  explanation: string[];
  tokens?: TokenDetail[];
}

interface TokenDetailsProps {
  sentence: SentenceResult | null;
}

const TokenDetails: React.FC<TokenDetailsProps> = ({ sentence }) => {
  const [hoveredToken, setHoveredToken] = useState<TokenDetail | null>(null);

  if (!sentence) {
    return (
      <div className="empty-inspector-state">
        <Info size={28} />
        <p style={{ fontSize: "0.85rem", lineHeight: 1.4 }}>
          Click on any sentence in the essay text to view the word-by-word vocabulary ranks and model checklist.
        </p>
      </div>
    );
  }

  const pPercent = Math.round(sentence.ai_probability * 100);
  const isFlagged = sentence.ai_probability > 0.55;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <div className="inspector-section" style={{ padding: "0 0 1rem 0", borderBottom: "1px solid var(--border-color)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="inspector-section-title">
            <Info size={14} /> Sentence #{sentence.index + 1}
          </span>
          <span
            className={`sample-item-tag ${isFlagged ? "tag-ai" : "tag-human"}`}
            style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
          >
            {pPercent}% AI Prob
          </span>
        </div>
        <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontStyle: "italic", marginTop: "0.5rem", lineHeight: "1.5" }}>
          "{sentence.text}"
        </p>
      </div>

      {sentence.tokens && sentence.tokens.length > 0 && (
        <div className="inspector-section" style={{ padding: "0 0 1rem 0", borderBottom: "1px solid var(--border-color)", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          <span className="inspector-section-title">
            GLTR Token Map
            <span title="Green words are highly predictable, while red/purple are unexpected. Machine text contains almost zero red/purple tokens." style={{ cursor: "help", display: "inline-flex", alignItems: "center" }}>
              <HelpCircle size={12} />
            </span>
          </span>
          
          <div className="token-chip-container">
            {sentence.tokens.map((tok, idx) => (
              <span
                key={idx}
                className={`token-chip ${tok.category}`}
                onMouseEnter={() => setHoveredToken(tok)}
                onMouseLeave={() => setHoveredToken(null)}
              >
                {tok.token}
              </span>
            ))}
          </div>

          <div className="gltr-legend">
            <div className="legend-row">
              <span className="legend-bullet top10" />
              <span>Top 10 (predictable)</span>
            </div>
            <div className="legend-row">
              <span className="legend-bullet top100" />
              <span>Top 100</span>
            </div>
            <div className="legend-row">
              <span className="legend-bullet top1000" />
              <span>Top 1000</span>
            </div>
            <div className="legend-row">
              <span className="legend-bullet other" />
              <span>Other (creative)</span>
            </div>
          </div>

          {hoveredToken && (
            <div
              style={{
                fontSize: "0.75rem",
                padding: "0.5rem",
                backgroundColor: "var(--bg-primary)",
                border: "1px solid var(--border-color)",
                borderRadius: "4px",
                color: "var(--text-secondary)",
                marginTop: "0.5rem",
              }}
            >
              Token: <strong>"{hoveredToken.token.trim()}"</strong> | Rank: <strong>#{hoveredToken.rank + 1}</strong> | Prob: <strong>{(hoveredToken.prob * 100).toFixed(2)}%</strong>
            </div>
          )}
        </div>
      )}

      <div className="inspector-section" style={{ padding: 0 }}>
        <span className="inspector-section-title" style={{ marginBottom: "0.5rem" }}>
          Linguistic Indicators
        </span>
        <div className="inspector-checks-list">
          {sentence.explanation.map((item, idx) => (
            <div className="inspector-check-item" key={idx}>
              <span className="inspector-check-icon" style={{ color: isFlagged ? "var(--color-danger)" : "var(--color-success)" }}>
                {isFlagged ? "⚠️" : "✓"}
              </span>
              <span>{item}</span>
            </div>
          ))}
          <div className="inspector-check-item" style={{ color: "var(--text-muted)" }}>
            <span>•</span>
            <span>Length: {sentence.word_count} words | Perplexity: {sentence.perplexity.toFixed(1)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TokenDetails;
