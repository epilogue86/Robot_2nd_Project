import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 1. 원래 실행하던 turtlebot3_bringup의 robot.launch.py 가져오기
    tb3_bringup_dir = get_package_share_directory('turtlebot3_bringup')
    launch_robot = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_bringup_dir, 'launch', 'robot.launch.py')
        )
    )

    # 2. v4l2_camera_node 설정
    camera_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name='v4l2_camera_node',
        parameters=[{
            'video_device': '/dev/video0',
            'image_size': [640, 480]
        }]
    )

    return LaunchDescription([
        launch_robot,
        camera_node
    ])
