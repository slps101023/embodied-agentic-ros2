import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, AppendEnvironmentVariable, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit

def generate_launch_description():
    # 取得套件的 share 目錄路徑
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_jetrover_description = get_package_share_directory('jetrover_description')

    # 宣告預設參數
    default_world_path = '/home/lihsun/physical_ai_project/src/JetRover/jetrover_description/worlds/livingroom.sdf'
    default_lidar_type = os.environ.get('LIDAR_TYPE', 'A1')
    default_machine_type = os.environ.get('MACHINE_TYPE', 'JetRover_Mecanum')

    # 宣告 launch 參數
    set_gz_resource_path = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.join(pkg_jetrover_description, '..')
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world_path,
        description='SDF world file path'
    )

    lidar_type_arg = DeclareLaunchArgument(
        'lidar_type',
        default_value=default_lidar_type,
        description='LiDAR type'
    )

    machine_type_arg = DeclareLaunchArgument(
        'machine_type',
        default_value=default_machine_type,
        description='Machine base type'
    )

    # 啟動 Gazebo Sim
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': [LaunchConfiguration('world'), ' -r -v 4']
        }.items()
    )

    # 啟動 robot_state_publisher 節點
    xacro_file = os.path.join(pkg_jetrover_description, 'urdf', 'jetrover.xacro')
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': Command(['xacro ', xacro_file]),
            'use_sim_time': True
        }]
    )

    # spawn robot in Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'jetrover',
            '-z', '0.05'
        ],
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # 啟動 ros2_control 控制器 Spawners
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', "--controller-manager", "/controller_manager"],
        output='screen'
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_controller',
            '--controller-manager', '/controller_manager',
            '--param-file',
            os.path.join(
                pkg_jetrover_description,
                'config',
                'ros2_controllers.yaml'
            )
        ],
        output='screen'
    )

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'gripper_controller',
            '--controller-manager', '/controller_manager',
            '--param-file',
            os.path.join(
                pkg_jetrover_description,
                'config',
                'ros2_controllers.yaml'
            )
        ],
        output='screen'
    )

    # 當 joint_state_broadcaster 啟動完成並退出 Spawner 時，接著啟動手臂控制器
    delay_arm_after_joint_state = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_controller_spawner],
        )
    )

    # 當手臂控制器啟動完成後，接著啟動夾爪控制器
    delay_gripper_after_arm = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[gripper_controller_spawner],
        )
    )

    ld = LaunchDescription()

    ld.add_action(set_gz_resource_path)
    ld.add_action(world_arg)
    ld.add_action(gz_sim)
    ld.add_action(lidar_type_arg)
    ld.add_action(machine_type_arg)
    ld.add_action(robot_state_publisher)
    ld.add_action(spawn_robot)
    ld.add_action(joint_state_broadcaster_spawner)  
    ld.add_action(delay_arm_after_joint_state)
    ld.add_action(delay_gripper_after_arm)

    return ld