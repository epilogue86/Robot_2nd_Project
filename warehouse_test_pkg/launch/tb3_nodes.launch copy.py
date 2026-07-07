from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. robot_logger.py
        Node(
            package='gz_test_pkg',
            executable='robot_logger.py',
            name='robot_logger',
            output='screen'
        ),
        # 2. tb3_object_detector.py
        Node(
            package='gz_test_pkg',
            executable='tb3_object_detector.py',
            name='tb3_object_detector',
            output='screen'
        ),
        # 3. tb3_pilot.py
        Node(
            package='gz_test_pkg',
            executable='tb3_pilot.py',
            name='tb3_pilot',
            output='screen'
        )
    ])