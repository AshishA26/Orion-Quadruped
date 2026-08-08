# RPY Visualization Panel for Foxglove Studio

A custom Foxglove Studio panel extension for visualizing Roll, Pitch, and Yaw (RPY) orientation data with circular gauges.

## Features

- **Three Side-by-Side Circular Gauges**: Visual representation of Roll, Pitch, and Yaw angles
- **Aerospace Color Coding**: Red (Roll/X), Green (Pitch/Y), Blue (Yaw/Z)
- **Real-time Updates**: Subscribes to ROS topics for live data visualization
- **Clear Numerical Displays**: Shows exact angle values in degrees
- **Range: -180° to +180°**: Industry-standard angle representation with zero at top
- **Lightweight & Fast**: Custom SVG-based rendering with no heavy dependencies
- **Topic Selection**: Easy dropdown to select from available ROS topics

## Installation

### Prerequisites

- [Foxglove Studio](https://foxglove.dev/download) installed
- Node.js 16+ and npm

### Build from Source

1. Clone or navigate to this directory:
   ```bash
   cd rpy-panel
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the extension:
   ```bash
   npm run build
   ```

4. Package the extension (creates a `.foxe` file):
   ```bash
   npm run package
   ```

5. Install in Foxglove Studio:
   - Open Foxglove Studio
   - Go to Extensions → Install Extension
   - Select the generated `.foxe` file from the `dist` folder

### Development Mode

To develop with hot reload:

```bash
npm run watch
```

Then in Foxglove Studio:
- Go to Extensions → Install Extension
- Navigate to the `rpy-panel` directory and select it

## Usage

### Message Format

Your custom ROS message should contain the following fields:

```
float64 roll   # degrees, -180 to +180
float64 pitch  # degrees, -180 to +180
float64 yaw    # degrees, -180 to +180
```

Example message types that work:
- Custom messages with `roll`, `pitch`, `yaw` fields
- Ensure values are in **degrees** (not radians)

### Using the Panel

1. **Add Panel**: In Foxglove Studio, click the "+" button and select "RPY Visualization"

2. **Select Topic**: Use the dropdown at the top of the panel to select your ROS topic containing RPY data

3. **View Data**: The three gauges will update in real-time as messages arrive:
   - **Roll** (Red): Left gauge
   - **Pitch** (Green): Middle gauge
   - **Yaw** (Blue): Right gauge

### Interpreting the Gauges

- **Zero Position**: Top of each gauge (12 o'clock) represents 0°
- **Clockwise**: Positive angles rotate clockwise
- **Counter-clockwise**: Negative angles rotate counter-clockwise
- **Range Markers**: Major ticks every 90° (-180°, -90°, 0°, +90°)
- **Numeric Display**: Large number below each gauge shows the exact value

## Configuration

### Customizing Colors

Edit `src/RPYPanel.tsx` and modify the `colors` object:

```typescript
const colors = {
  roll: "#EF4444",   // Red - change to your preferred color
  pitch: "#10B981",  // Green
  yaw: "#3B82F6",    // Blue
};
```

### Adjusting Gauge Size

In `src/RPYPanel.tsx`, modify the `size` prop:

```typescript
<CircularGauge
  value={rpyData.roll}
  label="Roll"
  color={colors.roll}
  size={220}  // Change this value (default: 220px)
/>
```

### Handling Different Message Schemas

If your message has a different structure (e.g., nested fields), modify the message extraction logic in `src/RPYPanel.tsx`:

```typescript
// Example for nested structure
const roll = msg.orientation?.roll ?? 0;
const pitch = msg.orientation?.pitch ?? 0;
const yaw = msg.orientation?.yaw ?? 0;
```

## Troubleshooting

### No Data Appearing

1. **Check Topic**: Ensure you've selected the correct topic from the dropdown
2. **Verify Message Format**: Use Foxglove's raw message viewer to confirm your message contains `roll`, `pitch`, `yaw` fields
3. **Check Units**: This panel expects degrees, not radians. If your data is in radians, multiply by `180 / Math.PI`

### Gauge Not Updating

1. **Playback**: Ensure your data source is playing (not paused)
2. **Message Rate**: Check that messages are being published to the topic
3. **Browser Console**: Open Developer Tools (F12) to check for errors

### Converting from Quaternions or Euler Radians

If your data comes as quaternions or radians, you'll need to add conversion logic in `RPYPanel.tsx`:

```typescript
// Example: Convert radians to degrees
const roll = (msg.roll * 180 / Math.PI);
const pitch = (msg.pitch * 180 / Math.PI);
const yaw = (msg.yaw * 180 / Math.PI);
```

## Project Structure

```
rpy-panel/
├── src/
│   ├── RPYPanel.tsx       # Main panel component with subscription logic
│   ├── CircularGauge.tsx  # Reusable SVG gauge component
│   ├── index.ts           # Extension registration
│   └── types.ts           # TypeScript interfaces
├── package.json           # Dependencies and scripts
├── tsconfig.json          # TypeScript configuration
└── README.md              # This file
```

## Development

### Building

```bash
npm run build
```

### Packaging

```bash
npm run package
```

Creates a `.foxe` file in the `dist` directory that can be shared and installed.

### Testing

```bash
npm run pretest
```

## License

MIT

## Support

For issues or questions:
- Check Foxglove Studio documentation: https://docs.foxglove.dev/
- Review the Extension API: https://docs.foxglove.dev/docs/visualization/extensions/getting-started

## Credits

Built with the Foxglove Studio Extension SDK.
