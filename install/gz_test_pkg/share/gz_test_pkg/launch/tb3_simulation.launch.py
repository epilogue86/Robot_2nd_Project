import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 맵 파일 경로 설정
    map_dir = LaunchConfiguration(
        'map',
        default='/home/jonghun/ros2_ws/src/gz_test_pkg/maps/project_map_gz_test.yaml'
    )

    # 1. turtlebot3_gazebo의 my_world.launch.py 가져오기
    gazebo_launch_dir = os.path.join(
        get_package_share_directory('turtlebot3_gazebo'),
        'launch',
        'my_world.launch.py'
    )
    launch_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_dir),
        launch_arguments=[('use_sim_time', 'true')]
    )

    # 2. nav2_bringup 및 turtlebot3_navigation2 기본 설정 가져오기
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    tb3_nav2_dir = get_package_share_directory('turtlebot3_navigation2')
    
    model_name = os.getenv('TURTLEBOT3_MODEL', 'waffle_pi')
    rviz_config_file = os.path.join(tb3_nav2_dir, 'rviz', 'tb3_navigation2.rviz')
    params_file = os.path.join(tb3_nav2_dir, 'param', model_name + '.yaml')

    # 3. 💡 [핵심 수정] 플러그인 이름 버그를 우회하기 위한 파라미터 강제 재정의
    # 원래 yaml 파일에 적힌 더블 콜론(::) 형식을 슬래시(/) 형식으로 바꾼 딕셔너리를 주입합니다.
    nav2_params_overrides = {
        'use_sim_time': True,
        'planner_server.ros__parameters.expected_planner_plugins': ['GridBased'],
        'planner_server.ros__parameters.GridBased.plugin': 'nav2_navfn_planner/NavfnPlanner'
    }

    launch_nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments=[
            ('map', map_dir),
            ('use_sim_time', 'true'),
            ('params_file', params_file),
            ('autostart', 'true'),
            ('use_rviz', 'true'),
            ('rviz_config', rviz_config_file)
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=map_dir,
            description='Full path to map file to load'
        ),
        launch_gazebo,
        launch_nav2
    ])