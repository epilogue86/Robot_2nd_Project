from setuptools import find_packages, setup

package_name = 'my_first_pkg'

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
    maintainer='jonghun',
    maintainer_email='jonghun@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            "hello_pub = my_first_pkg.hello_publisher:main",
            "hello_sub = my_first_pkg.hello_subscriber:main",
            "move_forward = my_first_pkg.move_forward:main",
            "scan_reader = my_first_pkg.scan_reader:main",
            "obstacle_stop = my_first_pkg.obstacle_stop:main",
            "obstacle_avoid_v2 = my_first_pkg.obstacle_avoid_v2:main",
            "obstacle_avoid_v3 = my_first_pkg.obstacle_avoid_v3:main",
            "obstacle_avoid_v4 = my_first_pkg.obstacle_avoid_v4:main",
            "odom_reader = my_first_pkg.odom_reader:main",
            "move_1m = my_first_pkg.move_1m:main",
            "go_to_goal = my_first_pkg.go_to_goal:main",
            "go_to_goal_with_avoid = my_first_pkg.go_to_goal_with_avoid:main",
            "patrol_robot = my_first_pkg.patrol_robot:main",
            "camera_viewer = my_first_pkg.camera_viewer:main",
            "color_tracker = my_first_pkg.color_tracker:main",
            "camera_basic = my_first_pkg.camera_basic:main",
            "multi_goal_navigator = my_first_pkg.multi_goal_navigator:main",
            "navigation_coltroller = my_first_pkg.navigation_coltroller:main",
            "yolo_detect = my_first_pkg.yolo_detect:main",
        ],
    },
)
