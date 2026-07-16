# Isaac ROS Workspace

Setup on Jetson:
```bash
cp src/orion_bringup/docker/.isaac_ros_common-config ~/.
```

```bash
cp src/orion_bringup/docker/.isaac_ros_common-config ~/.
cd ${ISAAC_ROS_WS}/src/submodules/isaac_ros_common && ./scripts/run_dev.sh --skip_image_build
./scripts/build_robot.sh
./scripts/run_robot.sh
```

## Notes

Creating a package (when inside docker container):
```bash
cd src
ros2 pkg create --build-type ament_python orion_bringup
```
