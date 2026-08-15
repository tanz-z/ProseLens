import React from "react";
import { AlertTriangle, CheckCircle2, ShieldAlert } from "lucide-react";

interface OverviewScoreProps {
  prob: number;
  originalProb: number;
  flags: string[];
  explanation: string[];
}

const OverviewScore: React.FC<OverviewScoreProps> = ({
  prob,
  originalProb,
  flags,
  explanation,
}) => {
  const percentage = Math.round(prob * 100);
  const radius = 32;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (prob * circumference);

  // Verdict selection
  let verdictTitle = "Human-Written";
  let verdictSub = "Natural pacing & style";
  let strokeColor = "#10b981"; // Emerald
  let VerdictIcon = CheckCircle2;

  if (prob > 0.60) {
    verdictTitle = "AI-Generated";
    verdictSub = "Highly predictable prose";
    strokeColor = "#ef4444"; // Crimson
    VerdictIcon = ShieldAlert;
  } else if (prob > 0.40) {
    verdictTitle = "AI-Polished";
    verdictSub = "Artificially smoothed text";
    strokeColor = "#f59e0b"; // Gold
    VerdictIcon = AlertTriangle;
  }

  const isEslCalibrated = flags.includes("ESL_WRITING_STYLE");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
      <div className="inspector-gauge-row">
        <div className="donut-gauge">
          <svg className="donut-svg" viewBox="0 0 80 80">
            <circle
              className="donut-bg"
              cx="40"
              cy="40"
              r={radius}
            />
            <circle
              className="donut-fill"
              cx="40"
              cy="40"
              r={radius}
              stroke={strokeColor}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
            />
          </svg>
          <span className="donut-text">{percentage}%</span>
        </div>

        <div className="inspector-verdict-box">
          <span className="inspector-verdict-title" style={{ color: strokeColor }}>
            <VerdictIcon size={18} style={{ flexShrink: 0 }} />
            {verdictTitle}
          </span>
          <span className="inspector-verdict-sub">{verdictSub}</span>
          {isEslCalibrated && (
            <span style={{ fontSize: "0.65rem", color: "#93c5fd", fontWeight: "600", marginTop: "0.15rem" }}>
              ESL Calibrated ✓
            </span>
          )}
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
        <span className="inspector-section-title">Global Indicators</span>
        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
          {explanation.map((item, idx) => (
            <p key={idx} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "flex", gap: "0.4rem", lineHeight: "1.4" }}>
              <span style={{ color: strokeColor, flexShrink: 0 }}>•</span>
              <span>{item}</span>
            </p>
          ))}
        </div>
      </div>

      {isEslCalibrated && (
        <div className="esl-callout-box">
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: "0.1rem" }} />
          <div>
            <strong>ESL Guard</strong>: Predictable vocab with organic sentence structure variation was detected. AI score damped from {Math.round(originalProb * 100)}% to {percentage}% to protect non-native authorship.
          </div>
        </div>
      )}
    </div>
  );
};

export default OverviewScore;
