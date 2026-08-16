# orion_urdf 
Based off of https://github.com/ApostolosApostolou/view_robot_pkg.

## Visualize a Robot's URDF in RViz (ROS2)

This ROS2 package lets you **visualize your robot’s URDF file** in **RViz2**.  
It also runs the **Joint State Publisher GUI**, so you can move the robot’s joints and see how they move in real time.

---
## How to Use

Run this command:

```bash
ros2 launch orion_urdf view_robot.launch
```

## Dependencies
```bash
sudo apt install ros-${ROS_DISTRO}-rviz2 \
                 ros-${ROS_DISTRO}-joint-state-publisher-gui \
                 ros-${ROS_DISTRO}-robot-state-publisher
```
## Related YouTube Video
#### Explains how to convert SolidWorks to URDF for ROS2 & How to use this package.
#### Link: https://www.youtube.com/watch?v=JdZJP3tGcA4&feature=youtu.be

