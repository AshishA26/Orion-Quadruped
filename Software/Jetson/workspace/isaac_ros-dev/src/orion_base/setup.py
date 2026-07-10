from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'orion_base'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='orion',
    maintainer_email='orion@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'stm32_bridge_node = orion_base.stm32_bridge_node:main',
            'roboeyes_node = orion_base.roboeyes_node:main',
            'joystick_parser_node = orion_base.joystick_parser_node:main',
            'cmd_mux_node = orion_base.cmd_mux_node:main',
        ],
    },
)
