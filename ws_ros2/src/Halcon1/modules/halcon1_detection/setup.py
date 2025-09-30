from setuptools import setup
import os
from glob import glob

package_name = 'halcon1_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Halcon Team',
    maintainer_email='dev@halcon.com',
    description='Drone detection module',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detection_node = halcon1_detection.detection_node:main',
        ],
    },
    package_data={
        package_name: [
            'models/*.pt',
            'models/*.pth',
            'config.yaml',
        ],
    },
    include_package_data=True,
)