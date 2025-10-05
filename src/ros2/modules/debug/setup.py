from setuptools import setup
import os
from glob import glob

package_name = 'ally_visualizer'

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
    description='Ally drone visualization node for RViz2 (simulator-agnostic)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ally_visualizer = ally_visualizer.ally_visualizer:main',
        ],
    },
)
