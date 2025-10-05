from setuptools import setup
import os
from glob import glob

package_name = 'airsim_enemy_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Halcon Team',
    maintainer_email='halcon@example.com',
    description='Enemy drone offboard control for AirSim (API-based)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'enemy_offboard_control = airsim_enemy_control.enemy_offboard_control:main',
        ],
    },
)
