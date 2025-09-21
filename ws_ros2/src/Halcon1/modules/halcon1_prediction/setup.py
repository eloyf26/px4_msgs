from setuptools import setup

package_name = 'halcon1_prediction'

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
    description='Trajectory prediction module',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'prediction_node = halcon1_prediction.prediction_node:main',
        ],
    },
)