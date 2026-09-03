# URDF Models

URDF robot description files at various stages of the SolidWorks → ROS2 → Isaac Lab pipeline.

## Structure
URDF Files in this folder are primarily the solidworks models for URDFs, and the exported URDF files from solidworks via the SW2URDF plugin. 

The actual used URDF files can be found in [`Software/reinforcement-learning/src/robot_description`](../Software/reinforcement-learning/src/robot_description) and [`Software/Jetson/workspace/isaac_ros-dev/src/orion_urdf/urdf`](../Software/Jetson/workspace/isaac_ros-dev/src/orion_urdf/urdf). Note these files are different from the ones in this folder and different from each other. Each of these have different modifications for their specific purposes.

```
urdf/
├── models_urdf/           # Soliworks model for ROS2.
├── models_urdf_rl/        # Solidworks model adapted for RL — Added foot joints.
├── orion_urdf_rl/         # Isaac Lab ROS2 package with URDF, meshes, textures, launch
├── urdf_files_original/   # Raw SolidWorks URDF export (v1)
└── urdf_files_original_v2/ # Raw SolidWorks URDF export (v2)
```