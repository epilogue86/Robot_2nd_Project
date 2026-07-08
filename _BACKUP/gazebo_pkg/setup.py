from setuptools import find_packages, setup

package_name = 'gazebo_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
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
            "tb3_pilot              = gazebo_pkg.tb3_pilot:main",
            "tb3_object_detector    = gazebo_pkg.tb3_object_detector:main",
            "robot_logger           = gazebo_pkg.robot_logger:main",
            "turtlebot_server       = gazebo_pkg.turtlebot_server:main",
            "web_cam                = gazebo_pkg.web_cam:main",
        ],
    },
)
