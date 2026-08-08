import React, { useEffect, useLayoutEffect, useState } from "react";
import ReactDOM from "react-dom";
import { Immutable, MessageEvent, PanelExtensionContext, Topic } from "@foxglove/extension";

import { CircularGauge } from "./CircularGauge";
import { RPYMessage, RPYPanelState } from "./types";

/**
 * Main RPY Panel Component
 * Subscribes to a ROS topic and visualizes Roll, Pitch, Yaw data
 */
function RPYPanelComponent({ context }: { context: PanelExtensionContext }) {
  const [topics, setTopics] = useState<readonly Topic[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string | undefined>(undefined);
  const [rpyData, setRpyData] = useState<RPYPanelState>({
    roll: 0,
    pitch: 0,
    yaw: 0,
  });
  const [hasData, setHasData] = useState(false);

  // Subscribe to available topics
  useLayoutEffect(() => {
    context.watch("topics");
    context.watch("currentFrame");
  }, [context]);

  // Handle incoming messages and topic updates
  useEffect(() => {
    context.onRender = (renderState, done) => {
      // Update available topics
      if (renderState.topics) {
        setTopics(renderState.topics);
      }

      // Update selected topic from panel state
      if (renderState.topics && !selectedTopic) {
        // Try to auto-select a topic that might contain RPY data
        const defaultTopic = renderState.topics.find(
          (t) =>
            t.name.toLowerCase().includes("rpy") ||
            t.name.toLowerCase().includes("orientation") ||
            t.name.toLowerCase().includes("attitude")
        );
        if (defaultTopic) {
          setSelectedTopic(defaultTopic.name);
          context.subscribe([defaultTopic.name]);
        }
      }

      // Process incoming messages
      if (renderState.currentFrame && selectedTopic) {
        for (const message of renderState.currentFrame) {
          if (message.topic === selectedTopic) {
            const msg = message.message as RPYMessage;

            // Extract RPY values (handle different message structures)
            // Note: Roll and Pitch are negated for correct sign convention
            // Roll: rolling right = positive
            // Pitch: pitching up = positive
            const roll = -(msg.roll ?? 0);
            const pitch = -(msg.pitch ?? 0);
            const yaw = msg.yaw ?? 0;

            setRpyData({
              roll,
              pitch,
              yaw,
              lastUpdateTime: Date.now(),
            });
            setHasData(true);
          }
        }
      }

      done();
    };

    // Cleanup
    return () => {
      context.onRender = undefined;
    };
  }, [context, selectedTopic]);

  // Handle topic selection change
  const handleTopicChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newTopic = event.target.value;

    // Unsubscribe from old topic
    if (selectedTopic) {
      context.subscribe([]);
    }

    // Subscribe to new topic
    if (newTopic) {
      setSelectedTopic(newTopic);
      context.subscribe([newTopic]);
      setHasData(false); // Reset data state
    } else {
      setSelectedTopic(undefined);
    }
  };

  // Color scheme: Red (Roll/X), Green (Pitch/Y), Blue (Yaw/Z)
  const colors = {
    roll: "#EF4444",   // Red
    pitch: "#10B981",  // Green
    yaw: "#3B82F6",    // Blue
  };

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        backgroundColor: "#1a1a1a",
        color: "#ffffff",
        padding: "20px",
        boxSizing: "border-box",
        overflow: "auto",
      }}
    >
      {/* Topic Selector */}
      <div
        style={{
          marginBottom: "20px",
          padding: "12px",
          backgroundColor: "#2a2a2a",
          borderRadius: "8px",
          border: "1px solid #404040",
        }}
      >
        <label
          htmlFor="topic-select"
          style={{
            display: "block",
            marginBottom: "8px",
            fontSize: "14px",
            fontWeight: "600",
            color: "#aaa",
          }}
        >
          Select RPY Topic:
        </label>
        <select
          id="topic-select"
          value={selectedTopic ?? ""}
          onChange={handleTopicChange}
          style={{
            width: "100%",
            padding: "8px 12px",
            fontSize: "14px",
            backgroundColor: "#333",
            color: "#fff",
            border: "1px solid #555",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          <option value="">-- Select a topic --</option>
          {topics.map((topic) => (
            <option key={topic.name} value={topic.name}>
              {topic.name} ({topic.schemaName})
            </option>
          ))}
        </select>
      </div>

      {/* No Data State */}
      {!hasData && selectedTopic && (
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
            color: "#888",
          }}
        >
          Waiting for messages on <strong>{selectedTopic}</strong>...
        </div>
      )}

      {/* No Topic Selected State */}
      {!selectedTopic && (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "16px",
            color: "#888",
            gap: "12px",
          }}
        >
          <div>⚠️ No topic selected</div>
          <div style={{ fontSize: "14px", color: "#666" }}>
            Please select a topic containing roll, pitch, and yaw data
          </div>
        </div>
      )}

      {/* RPY Gauges Display */}
      {hasData && (
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "row",
            justifyContent: "space-around",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "40px",
            padding: "20px 0",
          }}
        >
          <CircularGauge
            value={rpyData.roll}
            label="Roll"
            color={colors.roll}
            size={220}
            mode="standard"
          />
          <CircularGauge
            value={rpyData.pitch}
            label="Pitch"
            color={colors.pitch}
            size={220}
            mode="attitude"
          />
          <CircularGauge
            value={rpyData.yaw}
            label="Yaw"
            color={colors.yaw}
            size={220}
            mode="standard"
          />
        </div>
      )}

      {/* Footer with last update time */}
      {hasData && rpyData.lastUpdateTime && (
        <div
          style={{
            marginTop: "auto",
            paddingTop: "16px",
            fontSize: "12px",
            color: "#666",
            textAlign: "center",
          }}
        >
          Last update: {new Date(rpyData.lastUpdateTime).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

/**
 * Panel initialization function
 * Called by Foxglove Studio to render the panel
 */
export function initRPYPanel(context: PanelExtensionContext): void {
  ReactDOM.render(<RPYPanelComponent context={context} />, context.panelElement);
}
