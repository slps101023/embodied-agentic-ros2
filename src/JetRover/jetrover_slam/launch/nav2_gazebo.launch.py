import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    jetrover_navigation_dir = get_package_share_directory(
        'jetrover_slam'
    )

    map_file = os.path.join(
        jetrover_navigation_dir,
        'map',
        'livingromm_map.yaml'
    )

    params_file = os.path.join(
        jetrover_navigation_dir,
        'config',
        'nav2_params.yaml'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('use_rviz')

    return LaunchDescription([

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true'
        ),

        DeclareLaunchArgument(
            'use_rviz',
            default_value='true'
        ),

        # -------------------------
        # Nav2 Bringup
        # -------------------------

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(
                    nav2_bringup_dir,
                    'launch',
                    'bringup_launch.py'
                )
            ),
            launch_arguments={
                'map': map_file,
                'params_file': params_file,
                'use_sim_time': use_sim_time,
                'autostart': 'true',
            }.items()
        ),

        # -------------------------
        # RViz
        # -------------------------

        Node(
            condition=IfCondition(use_rviz),
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time}
            ]
        ),
    ])