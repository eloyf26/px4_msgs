from setuptools import setup
import os
from glob import glob

package_name = 'detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name, f'{package_name}.extensions'],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
        'ultralytics>=8.0.0',
        'opencv-python>=4.8.0',
        'pyyaml>=6.0',
        'numpy>=1.24.0',
    ],
    zip_safe=True,
    maintainer='Halcon Team',
    maintainer_email='dev@halcon.com',
    description='Drone detection module',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'detection_node = detection.detection_node:main',
        ],
    },
    package_data={
        package_name: [
            'models/*.pt',
            'models/*.pth',
            'config.yaml',
            'extensions/*.py',
            'extensions/README.md',
        ],
    },
    include_package_data=True,
)