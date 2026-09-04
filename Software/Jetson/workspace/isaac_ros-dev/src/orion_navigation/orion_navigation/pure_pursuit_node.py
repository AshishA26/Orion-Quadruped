import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from nav_msgs.msg import Path
from tf2_ros import Buffer, TransformListener, LookupException, ConnectivityException, ExtrapolationException

from orion_msgs.msg import OrionMotionCmd


class PurePursuitNode(Node):
    # Implements a pure pursuit path-following controller that consumes a Nav2-planned
    # path (nav_msgs/Path) and outputs OrionMotionCmd velocity commands on the
    # 'nav_motion_cmd' topic.
    #
    # The node only produces lin_x (forward speed) and ang_z (yaw rate); lin_y is
    # always zero because the quadruped uses forward-turn locomotion.

    def __init__(self):
        super().__init__('pure_pursuit_node')

        # Parameters
        self.declare_parameter('lookahead_distance', 0.4)    # metres
        self.declare_parameter('max_linear_speed', 0.3)      # m/s
        self.declare_parameter('max_angular_speed', 1.0)     # rad/s
        self.declare_parameter('goal_tolerance', 0.15)       # metres
        self.declare_parameter('control_frequency', 20.0)    # Hz
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('base_frame', 'base_link')

        self.lookahead_distance = self.get_parameter('lookahead_distance').value
        self.max_linear_speed   = self.get_parameter('max_linear_speed').value
        self.max_angular_speed  = self.get_parameter('max_angular_speed').value
        self.goal_tolerance     = self.get_parameter('goal_tolerance').value
        control_frequency       = self.get_parameter('control_frequency').value
        self.map_frame          = self.get_parameter('map_frame').value
        self.base_frame         = self.get_parameter('base_frame').value

        # TF
        self.tf_buffer   = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # State
        self.current_path: Path | None = None
        self.goal_reached = False

        # Subscriptions, publishers, and timer
        self.path_sub = self.create_subscription(Path, 'plan', self.path_callback, 10)
        self.cmd_pub = self.create_publisher(OrionMotionCmd, 'nav_motion_cmd', 10)
        self.control_timer = self.create_timer(1.0 / control_frequency, self.control_loop)

    def path_callback(self, msg: Path):
        # Receive a new planned path and reset goal-reached state.
        if len(msg.poses) == 0:
            self.get_logger().warn('Received empty path, ignoring.')
            return
        self.current_path = msg
        self.goal_reached = False
        self.get_logger().info(f'New path received with {len(msg.poses)} waypoints.')

    def control_loop(self):
        if self.current_path is None or self.goal_reached:
            return

        # Look up current robot pose in map frame
        robot_x, robot_y, robot_yaw = self._get_robot_pose()
        if robot_x is None:
            return  # TF not yet available

        # Get the list of poses (geometry_msgs/PoseStamped) from the path
        path_poses = self.current_path.poses

        # Check if we have reached the final goal
        goal = path_poses[-1].pose.position
        dist_to_goal = math.hypot(goal.x - robot_x, goal.y - robot_y)
        if dist_to_goal < self.goal_tolerance:
            self.get_logger().info('Goal reached — stopping.')
            self.goal_reached = True
            self.current_path = None
            self._publish_stop()
            return

        # Find the lookahead point
        lookahead_point = self._find_lookahead_point(
            path_poses, robot_x, robot_y
        )
        if lookahead_point is None:
            # Robot is past all path points — drive toward goal directly
            lookahead_point = (goal.x, goal.y)

        # Pure pursuit curvature calculation
        # Transform lookahead point into robot frame
        dx = lookahead_point[0] - robot_x
        dy = lookahead_point[1] - robot_y

        # Heading-relative coordinates
        local_x =  math.cos(robot_yaw) * dx + math.sin(robot_yaw) * dy
        local_y = -math.sin(robot_yaw) * dx + math.cos(robot_yaw) * dy

        # Actual distance to lookahead point
        L_dist = math.hypot(local_x, local_y)
        if L_dist < 1e-6:
            return

        # Curvature (k) = 2 * local_y / L_dist^2  ->  ang_z = v * k
        curvature = 2.0 * local_y / (L_dist * L_dist)

        # Linear speed: slow down when turning hard
        turn_scale = max(0.0, 1.0 - abs(curvature) * self.lookahead_distance)
        lin_x = self.max_linear_speed * turn_scale

        # Angular speed
        ang_z = self._clamp(curvature * lin_x, -self.max_angular_speed, self.max_angular_speed)

        # Publish
        cmd = OrionMotionCmd()
        cmd.cmd_type = OrionMotionCmd.CMD_AUTONOMY
        cmd.lin_x = float(lin_x)
        cmd.lin_y = 0.0
        cmd.ang_z = float(ang_z)
        self.cmd_pub.publish(cmd)

    def _get_robot_pose(self):
        """Return (x, y, yaw) of base_link in map frame, or (None, None, None)."""
        try:
            tf = self.tf_buffer.lookup_transform(
                self.map_frame,
                self.base_frame,
                Time()  # latest available
            )
        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().warn(f'TF lookup failed: {e}', throttle_duration_sec=2.0)
            return None, None, None

        t = tf.transform.translation
        q = tf.transform.rotation
        yaw = self._quat_to_yaw(q.x, q.y, q.z, q.w)
        return t.x, t.y, yaw

    def _find_lookahead_point(self, poses, rx, ry):
        """
        Walk the path and return the first point that is at least
        lookahead_distance away from the robot, interpolated on the path.
        Returns None if no such point exists within the path.
        """
        # Find the closest path point index first so we don't look backward
        closest_idx = 0
        closest_dist = float('inf')
        for i, pose in enumerate(poses):
            d = math.hypot(pose.pose.position.x - rx, pose.pose.position.y - ry)
            if d < closest_dist:
                closest_dist = d
                closest_idx = i

        # Search forward from closest point
        for i in range(closest_idx, len(poses)):
            px = poses[i].pose.position.x
            py = poses[i].pose.position.y
            if math.hypot(px - rx, py - ry) >= self.lookahead_distance:
                return (px, py)

        return None  # No point found beyond lookahead distance

    def _publish_stop(self):
        cmd = OrionMotionCmd()
        cmd.cmd_type = OrionMotionCmd.CMD_AUTONOMY
        cmd.lin_x = 0.0
        cmd.lin_y = 0.0
        cmd.ang_z = 0.0
        self.cmd_pub.publish(cmd)

    @staticmethod
    def _quat_to_yaw(qx, qy, qz, qw) -> float:
        """Convert quaternion to yaw (rotation about Z)."""
        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
        return math.atan2(siny_cosp, cosy_cosp)

    @staticmethod
    def _clamp(val, lo, hi):
        return max(lo, min(hi, val))


def main(args=None):
    rclpy.init(args=args)
    node = PurePursuitNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
