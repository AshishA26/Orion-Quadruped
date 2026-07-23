# Camera Config Settings

Fix the pink borders: 
- https://wiki.seeedstudio.com/how_to_use_camera_imx219/
- https://jonathantse.medium.com/fix-pink-tint-on-jetson-nano-wide-angle-camera-a8ce5fbd797f

```bash
sudo cp camera_overrides.isp /var/nvidia/nvcam/settings/
sudo chmod 664 /var/nvidia/nvcam/settings/camera_overrides.isp
sudo chown root:root /var/nvidia/nvcam/settings/camera_overrides.isp
```
