from setuptools import setup

package_name = 'airsim_viz_translator'

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
    maintainer='Eloy Fernandez',
    maintainer_email='eloyf26@gmail.com',
    description='PX4 to ROS2 message translator for AirSim RViz2 visualization',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'viz_translator = airsim_viz_translator.viz_translator_node:main',
        ],
    },
)
