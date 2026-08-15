import React from "react";

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
  rank_fractions: {
    top10: number;
    top100: number;
    top1000: number;
    other: number;
  };
}

interface TextVisualizerProps {
  sentences: SentenceResult[];
  activeIndex: number | null;
  setActiveIndex: (idx: number | null) => void;
}

const TextVisualizer: React.FC<TextVisualizerProps> = ({
  sentences,
  activeIndex,
  setActiveIndex,
}) => {
  const getProbabilityClass = (prob: number) => {
    if (prob > 0.60) return "high";
    if (prob > 0.40) return "med";
    return "low";
  };

  return (
    <div className="visualizer-container">
      <div className="visualizer-text-block">
        {sentences.map((sent) => {
          const isSelected = activeIndex === sent.index;
          const probClass = getProbabilityClass(sent.ai_probability);
          
          return (
            <span
              key={sent.index}
              onClick={() => setActiveIndex(sent.index)}
              className={`sentence-span ${probClass} ${isSelected ? "selected" : ""}`}
            >
              {sent.text}{" "}
            </span>
          );
        })}
      </div>
    </div>
  );
};

export default TextVisualizer;
