from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 시뮬레이션 시간 동기화 파라미터
    sim_time_param = {'use_sim_time': True}

    # robot_logger.py
    node_logger = Node(
        package='gz_test_pkg',
        executable='robot_logger.py',
        name='robot_logger',
        parameters=[sim_time_param],
        output='screen'
    )

    # tb3_object_detector.py
    node_detector = Node(
        package='gz_test_pkg',
        executable='tb3_object_detector.py',
        name='tb3_object_detector',
        parameters=[sim_time_param],
        output='screen'
    )

    return LaunchDescription([
        node_logger,
        node_detector
    ])