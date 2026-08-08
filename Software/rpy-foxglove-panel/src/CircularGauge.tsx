import React from "react";

interface CircularGaugeProps {
  value: number;          // -180 to +180 degrees
  label: string;          // "Roll", "Pitch", or "Yaw"
  color: string;          // Primary color for the gauge
  size?: number;          // Diameter in pixels
  mode?: "standard" | "attitude";  // Standard or attitude indicator mode
}

/**
 * Custom SVG-based circular gauge component for angle visualization
 * Standard mode: 0° at top (12 o'clock), for Roll and Yaw
 * Attitude mode: 0° at right (3 o'clock, horizontal), for Pitch deviation from horizon
 */
export const CircularGauge: React.FC<CircularGaugeProps> = ({
  value,
  label,
  color,
  size = 200,
  mode = "standard",
}) => {
  // Normalize value to -180 to +180 range
  const normalizedValue = ((value + 180) % 360) - 180;

  // Convert angle to SVG rotation
  // Standard mode: 0° = top (12 o'clock), clockwise positive
  // Attitude mode: 0° = right (3 o'clock, horizontal), for pitch
  const rotation = mode === "attitude" ? normalizedValue + 90 : normalizedValue;

  const center = size / 2;
  const radius = size * 0.35;
  const needleLength = radius * 0.85;
  const needleWidth = 3;

  // Generate tick marks every 30 degrees
  const generateTicks = () => {
    const ticks = [];
    for (let angle = 0; angle < 360; angle += 30) {
      const isCardinal = angle % 90 === 0;
      const tickLength = isCardinal ? 12 : 8;
      const tickWidth = isCardinal ? 2 : 1;
      const startRadius = radius - tickLength;

      // Convert to radians for calculation (0° = top)
      const rad = ((angle - 90) * Math.PI) / 180;
      const x1 = center + startRadius * Math.cos(rad);
      const y1 = center + startRadius * Math.sin(rad);
      const x2 = center + radius * Math.cos(rad);
      const y2 = center + radius * Math.sin(rad);

      ticks.push(
        <line
          key={`tick-${angle}`}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="#666"
          strokeWidth={tickWidth}
          strokeLinecap="round"
        />
      );

      // Add degree labels for cardinal directions
      if (isCardinal) {
        const labelRadius = radius + 20;
        const labelRad = ((angle - 90) * Math.PI) / 180;
        const labelX = center + labelRadius * Math.cos(labelRad);
        const labelY = center + labelRadius * Math.sin(labelRad);

        // Calculate display angle based on mode
        let displayAngle: number;
        if (mode === "attitude") {
          // Attitude mode (pitch): 0° at right (horizon), +90° at top (nose up), -90° at bottom (nose down)
          // angle 0 (top) → +90°, angle 90 (right) → 0°, angle 180 (bottom) → -90°, angle 270 (left) → ±180°
          displayAngle = 90 - angle;
          if (displayAngle < -180) displayAngle += 360;
          if (displayAngle > 180) displayAngle -= 360;
        } else {
          // Standard mode: 0° at top, +90° at right, 180° at bottom, -90° at left
          displayAngle = angle > 180 ? angle - 360 : angle;
        }

        ticks.push(
          <text
            key={`label-${angle}`}
            x={labelX}
            y={labelY}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#999"
            fontSize="11"
            fontWeight="500"
          >
            {displayAngle}°
          </text>
        );
      }
    }
    return ticks;
  };

  // Calculate needle endpoint
  const needleRad = ((rotation - 90) * Math.PI) / 180;
  const needleX = center + needleLength * Math.cos(needleRad);
  const needleY = center + needleLength * Math.sin(needleRad);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "8px",
      }}
    >
      {/* Label */}
      <div
        style={{
          fontSize: "16px",
          fontWeight: "600",
          color: color,
          textTransform: "uppercase",
          letterSpacing: "1px",
        }}
      >
        {label}
      </div>

      {/* SVG Gauge */}
      <svg width={size} height={size} style={{ overflow: "visible" }}>
        {/* Outer circle background */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#333"
          strokeWidth="2"
        />

        {/* Tick marks and labels */}
        {generateTicks()}

        {/* Zero indicator - highlighted */}
        {/* Standard mode: at top (12 o'clock). Attitude mode: at right (3 o'clock, horizon) */}
        <circle
          cx={mode === "attitude" ? center + radius : center}
          cy={mode === "attitude" ? center : center - radius}
          r="4"
          fill={color}
          opacity={0.6}
        />

        {/* Center hub */}
        <circle cx={center} cy={center} r="8" fill="#444" stroke="#666" strokeWidth="1" />

        {/* Needle */}
        <line
          x1={center}
          y1={center}
          x2={needleX}
          y2={needleY}
          stroke={color}
          strokeWidth={needleWidth}
          strokeLinecap="round"
        />

        {/* Needle tip */}
        <circle cx={needleX} cy={needleY} r="5" fill={color} />

        {/* Center dot */}
        <circle cx={center} cy={center} r="4" fill={color} />
      </svg>

      {/* Numeric value display */}
      <div
        style={{
          fontSize: "24px",
          fontWeight: "700",
          fontFamily: "monospace",
          color: color,
          backgroundColor: "rgba(0, 0, 0, 0.3)",
          padding: "8px 16px",
          borderRadius: "8px",
          border: `2px solid ${color}`,
          minWidth: "100px",
          textAlign: "center",
        }}
      >
        {normalizedValue.toFixed(1)}°
      </div>
    </div>
  );
};
