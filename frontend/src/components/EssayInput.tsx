import React from "react";
import { Sparkles, Trash2 } from "lucide-react";

interface EssayInputProps {
  text: string;
  setText: (t: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
}

const EssayInput: React.FC<EssayInputProps> = ({
  text,
  setText,
  onAnalyze,
  isLoading,
}) => {
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const isInputValid = wordCount >= 15;

  const handleClear = () => {
    setText("");
  };

  return (
    <div className="editor-container">
      <textarea
        className="workspace-textarea"
        placeholder="Paste college admissions essay here (minimum 15 words)..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={isLoading}
      />

      <div className="editor-footer">
        <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
          <span>{wordCount} words</span>
          {wordCount > 0 && wordCount < 15 && (
            <span style={{ color: "var(--color-danger)", marginLeft: "1rem" }}>
              Needs {15 - wordCount} more words
            </span>
          )}
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            onClick={handleClear}
            className="btn-secondary"
            disabled={isLoading || !text}
          >
            <Trash2 size={16} /> Clear
          </button>
          <button
            onClick={onAnalyze}
            className="btn-primary"
            disabled={isLoading || !isInputValid}
          >
            {isLoading ? (
              <>Analyzing...</>
            ) : (
              <>
                <Sparkles size={16} /> Analyze Essay
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EssayInput;
