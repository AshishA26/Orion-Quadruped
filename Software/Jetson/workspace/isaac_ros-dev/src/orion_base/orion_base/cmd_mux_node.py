import rclpy
from rclpy.node import Node
from orion_msgs.msg import OrionMotionCmd
from orion_msgs.msg import OrionEyesCmd

class CmdMux(Node):
    def __init__(self):
        super().__init__('cmd_mux_node')
        
        self.joy_motion_cmd_sub = self.create_subscription(
            OrionMotionCmd,
            'joy_motion_cmd',
            self.joy_motion_cmd_callback,
            10
        )
        self.joy_eyes_cmd_sub = self.create_subscription(
            OrionEyesCmd,
            'joy_eyes_cmd',
            self.joy_eyes_cmd_callback,
            10
        )
        # TODO(orion)
        # self.nav_motion_cmd_sub = self.create_subscription(
        #     OrionMotionCmd,
        #     'nav_motion_cmd',
        #     self.nav_motion_cmd_callback,
        #     10
        # )
        self.orion_motion_cmd_pub = self.create_publisher(OrionMotionCmd, 'orion_motion_cmd', 10)
        self.orion_eyes_cmd_pub = self.create_publisher(OrionEyesCmd, 'orion_eyes_cmd', 10)            

        self.declare_parameter('send_rate_hz', 50.0)
        self.declare_parameter('max_motion_speed', 1.5)
        self.declare_parameter('strafe_gaze_weight', 0.7)
        self.declare_parameter('turn_gaze_weight', 0.3)
        # Asymmetric eye scaling (curiosity on motion)
        self.declare_parameter('curious_scale_enabled', True)
        self.declare_parameter('curious_scale_max', 1.3)
        self.declare_parameter('strafe_scale_weight', 0.7)
        self.declare_parameter('turn_scale_weight', 0.3)
        self.declare_parameter('yaw_scale_weight', 0.4)
        self.declare_parameter('max_yaw', 0.524)
        
        send_rate = 1.0 / self.get_parameter('send_rate_hz').value
        self.max_motion_speed = self.get_parameter('max_motion_speed').value
        self.strafe_gaze_weight = self.get_parameter('strafe_gaze_weight').value
        self.turn_gaze_weight = self.get_parameter('turn_gaze_weight').value
        self.curious_scale_enabled = self.get_parameter('curious_scale_enabled').value
        self.curious_scale_max = self.get_parameter('curious_scale_max').value
        self.strafe_scale_weight = self.get_parameter('strafe_scale_weight').value
        self.turn_scale_weight = self.get_parameter('turn_scale_weight').value
        self.yaw_scale_weight = self.get_parameter('yaw_scale_weight').value
        self.max_yaw = self.get_parameter('max_yaw').value

        self.latest_joy_motion = OrionMotionCmd()
        self.latest_joy_eyes = OrionEyesCmd()

        self.pub_timer = self.create_timer(send_rate, self.publish_latest)

    def joy_motion_cmd_callback(self, msg):
        self.latest_joy_motion = msg

    def joy_eyes_cmd_callback(self, msg):
        self.latest_joy_eyes = msg
    
    def eyes_mux(self, joy_eyes, motion) -> OrionEyesCmd:
        eyes_out = OrionEyesCmd()
        eyes_out.power = joy_eyes.power
        eyes_out.mood = joy_eyes.mood
        eyes_out.mood_changed = joy_eyes.mood_changed
        eyes_out.gaze_locked = joy_eyes.gaze_locked

        # In CMD_EYES mode: joystick directly controls eyes
        if motion.cmd_type == OrionMotionCmd.CMD_EYES:
            eyes_out.gaze_x = joy_eyes.gaze_x
            eyes_out.gaze_y = joy_eyes.gaze_y

        # Not in CMD_EYES mode: derive gaze from motion (unless locked)
        elif not joy_eyes.gaze_locked:
            # Derive gaze from motion commands
            gaze_from_strafe = self._clamp(motion.lin_y / self.max_motion_speed, -1.0, 1.0)
            gaze_from_turn = self._clamp(motion.ang_z / self.max_motion_speed, -1.0, 1.0)
            
            # Weighted blend: strafe dominates, turn adds subtle offset
            eyes_out.gaze_x = self._clamp(
                gaze_from_strafe * self.strafe_gaze_weight + 
                gaze_from_turn * self.turn_gaze_weight, 
                -1.0, 1.0
            )
            
            # TODO(orion): Vertical: could map pitch to gaze_y in the future
            eyes_out.gaze_y = 0.0

        # --- Asymmetric eye scaling (curiosity on motion) ---
        # Compute a turn_factor from strafe, angular velocity, and body yaw.
        # Positive = turning/strafing left, negative = turning/strafing right.
        # The eye on the SAME side as the turn direction becomes bigger.
        if self.curious_scale_enabled:
            strafe_norm = self._clamp(motion.lin_y / self.max_motion_speed, -1.0, 1.0)
            turn_norm = self._clamp(motion.ang_z / self.max_motion_speed, -1.0, 1.0)
            yaw_norm = self._clamp(motion.yaw / self.max_yaw, -1.0, 1.0)

            turn_factor = self._clamp(
                strafe_norm * self.strafe_scale_weight +
                turn_norm * self.turn_scale_weight +
                yaw_norm * self.yaw_scale_weight,
                -1.0, 1.0
            )

            scale_amount = abs(turn_factor) * (self.curious_scale_max - 1.0)
            if turn_factor > 0:  # Turning/strafing left → left eye bigger
                eyes_out.left_eye_scale = 1.0 + scale_amount
                eyes_out.right_eye_scale = 1.0
            elif turn_factor < 0:  # Turning/strafing right → right eye bigger
                eyes_out.left_eye_scale = 1.0
                eyes_out.right_eye_scale = 1.0 + scale_amount
            else:
                eyes_out.left_eye_scale = 1.0
                eyes_out.right_eye_scale = 1.0
        else:
            eyes_out.left_eye_scale = 1.0
            eyes_out.right_eye_scale = 1.0
        
        return eyes_out

    @staticmethod
    def _clamp(val, lo, hi):
        return max(lo, min(hi, val))

    def publish_latest(self):
        joy_motion = self.latest_joy_motion
        joy_eyes = self.latest_joy_eyes

        # TODO(orion): For now we directly send joy command to orion_base
        self.orion_motion_cmd_pub.publish(self.latest_joy_motion)

        # Get eyes cmd from mux function and publish
        eyes_cmd = self.eyes_mux(joy_eyes, joy_motion)
        self.orion_eyes_cmd_pub.publish(eyes_cmd)

def main(args=None):
    rclpy.init(args=args)
    cmd_mux_node = CmdMux()
    
    try:
        rclpy.spin(cmd_mux_node)
    except KeyboardInterrupt:
        pass
    finally:
        cmd_mux_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()