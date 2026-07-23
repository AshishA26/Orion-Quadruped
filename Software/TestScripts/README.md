# Leg Assembly Instructions

1. Power up each servo
1. Use Servo Clocking script to set approx. 135 degrees (270/2)
1. Place Servo arm on Servo, per appropriate orientation (hip vs femur/tibia)
1. Assemble Entire Leg
1. Use Servo Clocking script to finetune i.e. clock position. Record the angle/microseconds needed to put the servo arm in the middle position.
1. This angle will be added in the code for each servo.

# STM32 setup in Arduino IDE:
 - In Arduino IDE, go to File -> Preferences
 - Add this URL to `Additional Board Manager URLs`: https://github.com/stm32duino/BoardManagerFiles/raw/main/package_stmicroelectronics_index.json
 
# Camera Setup
1. ENSURE that the camera cables are connected properly. I am doing from dual camera (imx-219) to jetson orin nano. There is a red light on the camera PCB that should switch on if powered correctly. Options for camera connection are:
	- Use the short wires (1 per camera) that came with the camera, OR
	- Use 3 wires + 2 extension boards per camera. This is the only way I have found so far because the wire needs to be flipped and then flipped again.
2. Do
	```bash
	cd /opt/nvidia/jetson-io/
	sudo python3 jetson-io.py 
	```

3. Set the camera pins to be configured for `Camera IMX219 Dual`. Then do `Save and reboot to reconfigure pins` option
4. `ls /dev/video*` should now should 2 video feeds
5. Now you can run `python3 csi-camera/dual_camera.py` (needs `numpy`, can do `pip3 install numpy`). The `csi-camera` folder is from [JetsonHacks](https://github.com/JetsonHacksNano/CSI-Camera).
6. To fix the pink edges (from: [Jonathan Tse](https://jonathantse.medium.com/fix-pink-tint-on-jetson-nano-wide-angle-camera-a8ce5fbd797f))

	```bash
	sudo cp camera-config/camera_overrides.isp /var/nvidia/nvcam/settings/
	sudo chmod 664 /var/nvidia/nvcam/settings/camera_overrides.isp
	sudo chown root:root /var/nvidia/nvcam/settings/camera_overrides.isp
	```
