import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'warehouse_test_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='jonghun',
    maintainer_email='epilogueljh@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "tb3_pilot.py              = warehouse_test_pkg.tb3_pilot:main",
            "tb3_object_detector.py    = warehouse_test_pkg.tb3_object_detector:main",
            "robot_logger.py           = warehouse_test_pkg.robot_logger:main",
            "tb3_state_reporter.py     = warehouse_test_pkg.tb3_state_reporter:main",
        ],
    },
)
