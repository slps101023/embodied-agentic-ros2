import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import AppendEnvironmentVariable, IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch.conditions import IfCondition, UnlessCondition

def generate_launch_description():
    pkg_share = get_package_share_directory('jetrover_description')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')
    ros_gz_bridge_nav2_config_file = os.path.join(pkg_share, 'config', 'bridge.yaml')

    use_nav2_arg = DeclareLaunchArgument(
        'use_nav2',
        default_value='false',
        description='Whether to use Nav2 (switches to YAML config)'
    )

    use_nav2 = LaunchConfiguration('use_nav2')

    # 1. 補全 Gazebo 模型資源搜尋路徑
    install_share_path = os.path.abspath(os.path.join(pkg_share, '..'))
    set_gz_resource_path = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=install_share_path
    )

    # 2. 啟動 robot_state_publisher 節點
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'display.launch.py')
        ),
        launch_arguments={
            'use_sim_time': 'true',
            'use_gui': 'false',
            'use_rsp': 'true',
            'use_rviz': 'false',
            }.items()
    )

    # 5. 啟動 Gazebo Sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': '-r /home/lihsun/physical_ai_project/src/JetRover/jetrover_description/worlds/livingroom.sdf'
            }.items(),
    )

    # 6. 透過 ros_gz_sim 在 Gazebo 中生成機器人
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'jetrover',
            '-z', '0.2'
        ],
        output='screen'
    )

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # cmd_vel 需要雙向控制，保持 @
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            # 里程計、雷達與關節狀態只需要 GZ -> ROS (改用 [ 符號)
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen',
        condition=UnlessCondition(use_nav2)
    )

    ros_gz_bridge_nav2 = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': ros_gz_bridge_nav2_config_file}],
        output='screen',
        condition=IfCondition(use_nav2)
    )

    # 7. ros2_control Controller Spawner 節點
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller'],
        output='screen'
    )

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['gripper_controller'],
        output='screen'
    )

    rviz_config_file = os.path.join(pkg_share, 'rviz', 'gazebo.rviz')
    rviz_args = ['-d', rviz_config_file] if os.path.exists(rviz_config_file) else []
    
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=rviz_args,
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        set_gz_resource_path,
        use_nav2_arg,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        ros_gz_bridge,
        ros_gz_bridge_nav2,
        # joint_state_broadcaster_spawner,
        # arm_controller_spawner,
        # gripper_controller_spawner
        rviz_node
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()