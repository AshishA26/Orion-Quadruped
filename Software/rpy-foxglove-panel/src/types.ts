/**
 * Custom ROS message interface for RPY data
 */
export interface RPYMessage {
  roll: number;   // degrees, range: -180 to +180
  pitch: number;  // degrees, range: -180 to +180
  yaw: number;    // degrees, range: -180 to +180
  // Add any other fields your custom message might have
  header?: {
    stamp: {
      sec: number;
      nsec: number;
    };
    frame_id: string;
  };
}

/**
 * Panel state type
 */
export interface RPYPanelState {
  roll: number;
  pitch: number;
  yaw: number;
  lastUpdateTime?: number;
}
