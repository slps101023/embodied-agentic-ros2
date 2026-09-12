import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription, LaunchService
from launch.actions import AppendEnvironmentVariable, SetEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node

def generate_launch_description():
    pkg_share = get_package_share_directory('jetrover_description')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    # 1. 補全 Gazebo 模型資源搜尋路徑
    install_share_path = os.path.abspath(os.path.join(pkg_share, '..'))
    set_gz_resource_path = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=install_share_path
    )

    # 2. 設定預設環境變數
    set_lidar_env = SetEnvironmentVariable(
        name='LIDAR_TYPE', 
        value=os.environ.get('LIDAR_TYPE', 'A1')
    )
    set_machine_env = SetEnvironmentVariable(
        name='MACHINE_TYPE', 
        value=os.environ.get('MACHINE_TYPE', 'jetrover')
    )

    # 3. 動態轉譯 Xacro 檔案為 URDF
    xacro_file = os.path.join(pkg_share, 'urdf', 'jetrover.xacro')
    robot_description_content = Command(['xacro ', xacro_file])

    # 4. 啟動 robot_state_publisher 節點
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_content}]
    )

    # 5. 啟動 Gazebo Sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r /home/lihsun/physical_ai_project/src/JetRover/jetrover_description/worlds/livingroom.sdf'}.items(),
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

    return LaunchDescription([
        set_gz_resource_path,
        set_lidar_env,
        set_machine_env,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        joint_state_broadcaster_spawner,
        arm_controller_spawner,
        gripper_controller_spawner
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()