# Quick Start Guide

## 🚀 Installation & Setup (5 minutes)

### Step 1: Create the Extension

```bash
# Navigate to your desired directory
# The extension files have already been created in rpy-panel/
cd rpy-panel
```

### Step 2: Install Dependencies

```bash
npm install
```

This will install:
- Foxglove Studio SDK
- React and TypeScript dependencies
- Build tools and linters

### Step 3: Build the Extension

```bash
npm run build
```

This compiles the TypeScript code into a Foxglove-compatible extension.

### Step 4: Package (Optional - for distribution)

```bash
npm run package
```

This creates a `.foxe` file in the `dist/` folder that you can:
- Share with teammates
- Install on other machines
- Version control and distribute

### Step 5: Install in Foxglove Studio

**Option A: Development Mode (Recommended for development)**

1. Open Foxglove Studio
2. Click **Extensions** in the top menu
3. Select **Install Extension**
4. Navigate to `./rpy-panel`
5. Select the entire folder (not individual files)
6. Click **Open**

**Option B: Production Mode (Using .foxe file)**

1. Open Foxglove Studio
2. Click **Extensions** → **Install Extension**
3. Navigate to `rpy-panel/dist/`
4. Select the `.foxe` file
5. Click **Open**

---

## 🎯 Using the Panel

### Step 1: Add the Panel to Your Layout

1. In Foxglove Studio, click the **"+"** button in the layout
2. Search for **"RPY Visualization"**
3. Click to add the panel to your workspace

### Step 2: Select Your Topic

1. Click the dropdown at the top of the panel labeled **"Select RPY Topic"**
2. Choose your ROS topic that contains roll, pitch, and yaw data
3. The panel will auto-detect topics with names containing:
   - `rpy`
   - `orientation`
   - `attitude`

### Step 3: View Real-Time Data

Once you select a topic and play your data source:
- **Roll** (Red gauge, left) shows rotation around X-axis
- **Pitch** (Green gauge, center) shows rotation around Y-axis
- **Yaw** (Blue gauge, right) shows rotation around Z-axis

---

## 📊 Example ROS Message

Your custom ROS message should look like this:

### Message Definition (e.g., `RPYData.msg`)

```
float64 roll    # degrees, range: -180 to +180
float64 pitch   # degrees, range: -180 to +180
float64 yaw     # degrees, range: -180 to +180
```

### Example Publisher (Python)

```python
#!/usr/bin/env python3
import rospy
from your_package.msg import RPYData
import math

def publish_rpy():
    rospy.init_node('rpy_publisher')
    pub = rospy.Publisher('/robot/rpy', RPYData, queue_size=10)
    rate = rospy.Rate(10)  # 10 Hz

    angle = 0.0
    while not rospy.is_shutdown():
        msg = RPYData()
        msg.roll = 30.0 * math.sin(angle)     # Oscillating roll
        msg.pitch = 20.0 * math.cos(angle)    # Oscillating pitch
        msg.yaw = angle * 10.0 % 360 - 180    # Rotating yaw

        pub.publish(msg)
        angle += 0.1
        rate.sleep()

if __name__ == '__main__':
    try:
        publish_rpy()
    except rospy.ROSInterruptException:
        pass
```

---

## 🔧 Development Workflow

### Live Development with Hot Reload

```bash
npm run watch
```

This starts a file watcher that automatically rebuilds when you save changes. Foxglove Studio will hot-reload the extension.

### Making Changes

1. Edit files in `src/`
2. Save (auto-rebuilds with `npm run watch`)
3. Changes appear instantly in Foxglove

### Common Customizations

**Change gauge colors** (src/RPYPanel.tsx:112):
```typescript
const colors = {
  roll: "#FF0000",   // Your custom color
  pitch: "#00FF00",
  yaw: "#0000FF",
};
```

**Adjust gauge size** (src/RPYPanel.tsx:178):
```typescript
<CircularGauge ... size={300} />  // Larger gauges
```

**Handle different message schemas** (src/RPYPanel.tsx:85):
```typescript
// If your message has nested fields
const roll = msg.orientation?.roll ?? 0;
```

---

## ✅ Verify Installation

After installing, you should see:
- ✅ "RPY Visualization" in the panel picker
- ✅ Topic dropdown showing available topics
- ✅ Three circular gauges when data is playing
- ✅ Real-time updates as messages arrive

---

## 🐛 Troubleshooting

### Extension Not Showing Up

```bash
# Rebuild the extension
npm run build

# Check for errors in the build output
# Reinstall in Foxglove Studio
```

### No Data Appearing

1. ✅ Check topic is selected in dropdown
2. ✅ Verify data source is playing (not paused)
3. ✅ Confirm message has `roll`, `pitch`, `yaw` fields
4. ✅ Ensure values are in **degrees** (not radians)

### Converting from Radians

If your data is in radians, modify `src/RPYPanel.tsx`:

```typescript
const roll = (msg.roll * 180 / Math.PI);
const pitch = (msg.pitch * 180 / Math.PI);
const yaw = (msg.yaw * 180 / Math.PI);
```

---

## 📚 Next Steps

- **Customize**: Edit gauge colors, sizes, or layouts
- **Extend**: Add more features like history graphs or alerts
- **Share**: Package as `.foxe` and distribute to your team
- **Contribute**: Add features and share improvements

---

## 🆘 Need Help?

- 📖 [Foxglove Extension Docs](https://docs.foxglove.dev/docs/visualization/extensions/)
- 💬 [Foxglove Slack Community](https://foxglove.dev/slack)
- 🐛 [Report Issues](https://github.com/foxglove/studio/issues)

Happy visualizing! 🎉
