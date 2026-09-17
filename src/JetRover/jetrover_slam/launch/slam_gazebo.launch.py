import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    # 直接使用 ament_index_python 取得套件路徑，避免 substitution 導入錯誤
    slam_pkg_share = get_package_share_directory('jetrover_slam')
    slam_params_file = os.path.join(slam_pkg_share, 'config', 'slam.yaml')

    # 包含 Gazebo 底層 Launch
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('jetrover_description'),
                'launch',
                'gazebo.launch.py' # 請確認你的 Gazebo Launch 檔名
            )
        ])
    )

    # SLAM Toolbox 節點
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params_file,
            {'use_sim_time': True}
        ]
    )

    # Lifecycle 管理者
    lifecycle_manager_node = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_slam',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'autostart': True,
            'node_names': ['slam_toolbox'],
            'bond_timeout': 10.0
        }]
    )

    # 延遲 10 秒啟動 SLAM
    delayed_slam = TimerAction(
        period=10.0,
        actions=[slam_toolbox_node, lifecycle_manager_node]
    )

    return LaunchDescription([
        gazebo_launch,
        delayed_slam
    ])