from setuptools import setup
import os
from glob import glob

package_name = 'gazebo_enemy_visualizer'

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
    maintainer_email='eloyf26@gmail.com',
    description='Enemy drone visualization node for RViz2 (Gazebo-specific)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'enemy_visualizer = gazebo_enemy_visualizer.enemy_visualizer:main',
        ],
    },
)
