#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from geometry_msgs.msg import TwistStamped


class TwistStampedToTwist(Node):

    def __init__(self):
        super().__init__("twist_stamped_to_twist")

        # Parameters
        self.declare_parameter("input_topic", "/cmd_vel")
        self.declare_parameter("output_topic", "/cmd_vel_twist")

        input_topic = self.get_parameter(
            "input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter(
            "output_topic").get_parameter_value().string_value

        self.publisher = self.create_publisher(
            Twist,
            output_topic,
            10
        )

        self.subscription = self.create_subscription(
            TwistStamped,
            input_topic,
            self.callback,
            10
        )

        self.get_logger().info(
            f"Converting {input_topic} (TwistStamped) -> {output_topic} (Twist)"
        )

    def callback(self, msg: TwistStamped):
        twist = Twist()

        twist.linear = msg.twist.linear
        twist.angular = msg.twist.angular

        self.publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)

    node = TwistStampedToTwist()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()