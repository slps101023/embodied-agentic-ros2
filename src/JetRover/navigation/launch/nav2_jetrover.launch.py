import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    jetrover_share = get_package_share_directory("jetrover_description")
    navigation_share = get_package_share_directory("navigation")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                jetrover_share,
                "launch",
                "gazebo.launch.py",
            )
        ),
        launch_arguments={
            "use_nav2": "true",
        }.items(),
    )

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                navigation_share,
                "launch",
                "include",
                "bringup.launch.py",
            )
        )
    )

    twist_converter = Node(
        package="navigation",
        executable="twist_stamped_to_twist",
        name="twist_stamped_to_twist",
        output="screen",
    )


    return LaunchDescription(
        [
            gazebo,

            # 等待 Gazebo 啟動
            TimerAction(
                period=3.0,
                actions=[navigation],
            ),

            # 再啟動轉換器與 bridge
            TimerAction(
                period=5.0,
                actions=[
                    twist_converter,
                ],
            ),
        ]
    )