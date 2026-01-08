# Update rosdep to ensure all system dependencies for the new package are known
rosdep update

# Install any missing system dependencies for RF2O
rosdep install --from-paths src --ignore-src -y