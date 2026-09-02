import isaaclab.sim as sim_utils
from isaaclab.actuators import ActuatorNetMLPCfg, DCMotorCfg, ImplicitActuatorCfg
from isaaclab.assets.articulation import ArticulationCfg
import os
from math import pi

CUSTOM_QUAD_CFG = ArticulationCfg(
    spawn=sim_utils.UsdFileCfg(
        usd_path=os.environ['HOME'] + "/IsaacLab/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/config/custom_quadruped/robot.usd",
        activate_contact_sensors=True,
        rigid_props=sim_utils.RigidBodyPropertiesCfg(
            rigid_body_enabled=True, # added this line
            disable_gravity=False,
            retain_accelerations=False,
            linear_damping=0.0,
            angular_damping=0.0,
            max_linear_velocity=1000.0,
            max_angular_velocity=1000.0,
            max_depenetration_velocity=1.0,
        ),
        articulation_props=sim_utils.ArticulationRootPropertiesCfg(
            enabled_self_collisions=True,
            solver_position_iteration_count=4,
            solver_velocity_iteration_count=0
        ),
    ),
    init_state=ArticulationCfg.InitialStateCfg(
        pos=(0.0, 0.0, 0.20679),
        joint_pos={
            ".*L_hip_joint": 0, # Left side hip joints
            ".*R_hip_joint": 0, # Right side hip joints
            ".*L_thigh_joint": -30*pi/180, # Left side thigh joints
            ".*R_thigh_joint": 30*pi/180, # Right side thigh joints
            ".*L_calf_joint": 20*pi/180, # Left side calf joints
            ".*R_calf_joint": -20*pi/180, # Right side calf joints
        },
        joint_vel={".*": 0.0},
    ),
    soft_joint_pos_limit_factor=0.9,
    # actuators={
    #     "base_legs": DCMotorCfg(
    #         joint_names_expr=[".*_hip_joint", ".*_thigh_joint", ".*_calf_joint"],
    #         effort_limit=20.0, # 33.5
    #         saturation_effort=20.0,  # 33.5
    #         velocity_limit=40.0,
    #         stiffness=10.0, # 25.0
    #         damping=0.7, # 0.5
    #         friction=0.0,
    #     ),
    # },
    actuators={
        "hip": DCMotorCfg(
            joint_names_expr=[".*_hip_joint"],
            effort_limit=7.0,
            saturation_effort=7.0,
            velocity_limit=15.0,
            stiffness=25.0,
            damping=0.7,
            friction=0.0,
        ),
        "thigh": DCMotorCfg(
            joint_names_expr=[".*_thigh_joint"],
            effort_limit=8.0,
            saturation_effort=8.0,
            velocity_limit=15.0,
            stiffness=30.0,
            damping=0.8,
            friction=0.0,
        ),
        "calf": DCMotorCfg(
            joint_names_expr=[".*_calf_joint"],
            effort_limit=7.0,
            saturation_effort=7.0,
            velocity_limit=15.0,
            stiffness=25.0,
            damping=0.7,
            friction=0.0,
        ),
    },
)