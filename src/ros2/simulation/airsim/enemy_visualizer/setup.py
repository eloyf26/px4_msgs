from setuptools import setup

package_name = 'airsim_enemy_visualizer'

setup(
    name=package_name,
    version='1.0.0',
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
    description='Enemy drone visualizer for AirSim - queries AirSim API for ground truth',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'enemy_visualizer = airsim_enemy_visualizer.enemy_visualizer:main',
        ],
    },
)
