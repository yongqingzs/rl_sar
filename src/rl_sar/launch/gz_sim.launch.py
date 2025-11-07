# Copyright (c) 2024-2025 Ziqi Fan
# SPDX-License-Identifier: Apache-2.0

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    rname = LaunchConfiguration("rname")

    wname = "stairs"
    robot_name = ParameterValue(Command(["echo -n ", rname]), value_type=str)
    ros_namespace = ParameterValue(Command(["echo -n ", "/", rname, "_gazebo"]), value_type=str)
    gazebo_model_name = ParameterValue(Command(["echo -n ", rname, "_gazebo"]), value_type=str)

    robot_description = ParameterValue(
        Command([
            "xacro ",
            Command(["echo -n ", Command(["ros2 pkg prefix ", rname, "_description"])]),
            "/share/", rname, "_description/xacro/robot.xacro"
        ]),
        value_type=str
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description}],
    )

    # For Jazzy: Use ros_gz_sim's gz_server.launch.py
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_server.launch.py")
        ),
        launch_arguments={
            "world_sdf_file": os.path.join(get_package_share_directory("rl_sar"), "worlds", wname + ".world"),
        }.items(),
    )

    # For Jazzy: Use ros_gz_sim's spawn_entity
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="spawn_entity",
        arguments=[
            "-topic", "/robot_description",
            "-name", "robot_model",
            "-z", "1.0",
        ],
        output="screen",
    )

    joint_state_broadcaster_node = Node(
        package="controller_manager",
        executable='spawner',
        arguments=["joint_state_broadcaster"],
        output="screen",
    )

    robot_joint_controller_node = Node(
        package="controller_manager",
        executable='spawner',
        arguments=["robot_joint_controller"],
        output="screen",
    )

    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[{
            'deadzone': 0.1,
            'autorepeat_rate': 0.0,
        }],
    )

    param_node = Node(
        package="demo_nodes_cpp",
        executable="parameter_blackboard",
        name="param_node",
        parameters=[{
            "robot_name": robot_name,
            "gazebo_model_name": gazebo_model_name,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "rname",
            description="Robot name (e.g., a1, go2)",
            default_value=TextSubstitution(text=""),
        ),
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
        joint_state_broadcaster_node,
        # robot_joint_controller_node,  # Spawn in rl_sim.cpp
        joy_node,
        param_node,
    ])