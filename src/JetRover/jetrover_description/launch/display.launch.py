import os
from ament_index_python.packages import get_package_share_directory

from launch_ros.actions import Node
from launch import LaunchDescription, LaunchService
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import DeclareLaunchArgument, TimerAction, IncludeLaunchDescription, ExecuteProcess, SetEnvironmentVariable
from launch.conditions import IfCondition

def generate_launch_description():

    set_lidar_env = SetEnvironmentVariable(
        name='LIDAR_TYPE', 
        value=os.environ.get('LIDAR_TYPE', 'A1')
    )
    set_machine_env = SetEnvironmentVariable(
        name='MACHINE_TYPE', 
        value=os.environ.get('MACHINE_TYPE', 'JetRover_Mecanum')
    )

    # compiled = LaunchConfiguration('need_compile', default='True')
    namespace = LaunchConfiguration('namespace', default='')
    use_namespace = LaunchConfiguration('use_namespace', default='false')
    frame_prefix = LaunchConfiguration('frame_prefix', default='')
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_gui = LaunchConfiguration('use_gui', default='true')
    use_rsp = LaunchConfiguration('use_rsp', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    frame_prefix_arg = DeclareLaunchArgument('frame_prefix', default_value=frame_prefix)
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value=use_sim_time)
    namespace_arg = DeclareLaunchArgument('namespace', default_value=namespace)
    use_namespace_arg = DeclareLaunchArgument('use_namespace', default_value=use_namespace)
    use_gui_arg = DeclareLaunchArgument('use_gui', default_value=use_gui)
    use_rsp_arg = DeclareLaunchArgument('use_rsp', default_value=use_rsp)
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value=use_rviz)
    jetrover_description_package_path = get_package_share_directory('jetrover_description')

    # if compiled == 'True':
    #     jetrover_description_package_path = get_package_share_directory('jetrover_description')
    # else:
    #     jetrover_description_package_path = '/home/ubuntu/ros2_ws/src/simulations/jetrover_description'
    urdf_path = os.path.join(jetrover_description_package_path, 'urdf/jetrover.xacro')
    rviz_config_file = os.path.join(jetrover_description_package_path, 'rviz/view.rviz')

    robot_description = Command(['xacro ', urdf_path])
    
    # 动态TF转换(dynamic TF Transformation)
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        output='screen',
        condition=IfCondition(use_gui),
    )
    
    # 静态TF(static TF)
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'frame_prefix': frame_prefix, 'use_sim_time': use_sim_time}],
        arguments=[urdf_path],
        condition=IfCondition(use_rsp),
    )

    rviz_node = ExecuteProcess(
            cmd=['rviz2', 'rviz2', '-d', rviz_config_file],
            output='screen',
            condition=IfCondition(use_rviz)
        )

    # Timer action to delay rviz_node for 5 seconds
    delay_rviz_node = TimerAction(
        period=5.0,
        actions=[rviz_node],
    )

    return LaunchDescription([
        set_lidar_env,
        set_machine_env,
        frame_prefix_arg,
        use_sim_time_arg,
        namespace_arg,
        use_gui_arg,
        use_rsp_arg,
        use_rviz_arg,
        use_namespace_arg,
        joint_state_publisher_gui_node,
        robot_state_publisher_node,
        delay_rviz_node,
    ])

if __name__ == '__main__':
    # 创建一个LaunchDescription对象(create a LaunchDescription object)
    ld = generate_launch_description()

    ls = LaunchService()
    ls.include_launch_description(ld)
    ls.run()
