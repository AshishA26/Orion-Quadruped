# Reinforcement Learning

## Isaac Sim Setup

### Links used:
- [Installation using Isaac Sim Pip Package](https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/pip_installation.html)
- [Step by Step Walkthrough: Installing Isaac Sim and Isaac Lab on Windows](https://www.youtube.com/watch?v=R7zUlsUfdYk)
- [Import Your Robots From URDF to USD - Isaac Sim Tutorial](https://www.youtube.com/watch?v=AMfEtZ4hyLY)
- [URDF Importer Extension](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/robot_setup/ext_isaacsim_asset_importer_urdf.html)
- [Using the Interactive Scene](https://isaac-sim.github.io/IsaacLab/main/source/tutorials/02_scene/create_scene.html)

### Other Links:
- [Direct Workflow - Isaac Lab Tutorial 3 (Reinforcement Learning](https://www.youtube.com/watch?v=gdIJ_FcYXvM&list=PLQQ577DOyRN_hY6OAoxBh8K5mKsgyJi-r&index=8)
- [Importing a New Asset](https://isaac-sim.github.io/IsaacLab/main/source/how-to/import_new_asset.html)
- [Tutorial: Import URDF](https://docs.isaacsim.omniverse.nvidia.com/4.5.0/robot_setup/import_urdf.html)

### Commands ran to setup Isaac Lab:
```bash
conda create -n env_isaaclab python=3.11
conda activate env_isaaclab
pip install --upgrade pip
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com
pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
isaacsim
git clone git@github.com:isaac-sim/IsaacLab.git
sudo apt install cmake build-essential
./isaaclab.sh --install
cd IsaacLab/
./isaaclab.sh --install

# Testing Isaac Lab
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
./isaaclab.sh -p scripts/tutorials/00_sim/spawn_prims.py 
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
./isaaclab.sh -p scripts/tutorials/02_scene/create_scene.py 
./isaaclab.sh -p scripts/tutorials/03_envs/create_quadruped_base_env.py 
./isaaclab.sh -p scripts/tutorials/02_scene/create_scene.py 
```

### Tip 1
Isaac Sim and Lab are very graphics card dependent and may give errors if you don't have the proper drivers. Ensure you have the correct drivers by doing the following (this also fixes an issue where an HDMI connected monitor does not get displayed on Ubuntu - https://askubuntu.com/questions/1105332/external-monitor-not-working-ubuntu-nvidia):

```bash
sudo prime-select nvidia
sudo ubuntu-drivers autoinstall
reboot
```

That might work only temporarily. Then do `prime-select query` to ensure it says `nvidia`. Then log out, and log in, but choose Ubuntu on Xorg on the bottom right of your screen.

### Tip 2
Expect random glitches and try:
- Restart isaac lab / sim
- Restart machine
- Reinstall drivers / dependencies


## Training

To execute play.py using model shown in the video, move the "2025-03-03_05-00-17" folder
into the "/rsl_rl/logs/rsl_rl/custom_quad_flat" directory.