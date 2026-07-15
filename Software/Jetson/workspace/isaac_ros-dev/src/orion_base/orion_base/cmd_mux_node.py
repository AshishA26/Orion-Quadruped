import copy
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
        self.declare_parameter('curious_scale_enabled', True)
        self.declare_parameter('curious_scale_max', 1.3)
        
        send_rate = 1.0 / self.get_parameter('send_rate_hz').value
        self.curious_scale_enabled = self.get_parameter('curious_scale_enabled').value
        self.curious_scale_max = self.get_parameter('curious_scale_max').value

        self.latest_joy_motion = OrionMotionCmd()
        self.latest_joy_eyes = OrionEyesCmd()

        self.pub_timer = self.create_timer(send_rate, self.publish_latest)

    def joy_motion_cmd_callback(self, msg):
        self.latest_joy_motion = msg

    def joy_eyes_cmd_callback(self, msg):
        self.latest_joy_eyes = msg
    
    def eyes_mux(self, joy_eyes, motion) -> OrionEyesCmd:
        eyes_out = copy.copy(joy_eyes)

        gaze_from_strafe = self._clamp(motion.lin_y, -1.0, 1.0)
        gaze_from_turn = self._clamp(motion.ang_z, -1.0, 1.0)
        gaze_max = max([gaze_from_strafe, gaze_from_turn], key=abs)

        # In CMD_EYES mode: joystick directly controls eyes
        if motion.cmd_type == OrionMotionCmd.CMD_EYES:
            eyes_out.gaze_x = joy_eyes.gaze_x
            eyes_out.gaze_y = joy_eyes.gaze_y

        # Not in CMD_EYES mode: derive gaze from motion
        else:
            eyes_out.gaze_x = self._clamp(gaze_max, -1.0, 1.0)
            
            # TODO(orion): Vertical: could map pitch to gaze_y in the future
            eyes_out.gaze_y = 0.0

        # Asymmetric eye scaling (curiosity on motion)
        # The eye on the SAME side as the turn direction becomes bigger.
        if self.curious_scale_enabled:
            scale_amount = abs(gaze_max) * (self.curious_scale_max - 1.0)

            if gaze_max > 0:
                eyes_out.left_eye_scale = 1.0
                eyes_out.right_eye_scale = 1.0 + scale_amount
            elif gaze_max < 0:
                eyes_out.left_eye_scale = 1.0 + scale_amount
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

        # TODO(orion): Create a unified state machine to handle nav and joystick
        # For now we directly send joy command to orion_base
        overall_motion = joy_motion

        self.orion_motion_cmd_pub.publish(overall_motion)

        # Get eyes cmd from mux function and publish
        eyes_cmd = self.eyes_mux(joy_eyes, overall_motion)
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