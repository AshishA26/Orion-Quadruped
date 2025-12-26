#!/usr/bin/env python3
# https://github.com/engineerm-jp/Inverse_Kinematics_YouTube/tree/main/4Legs

from math import atan, pi, radians, cos, sin
import numpy as np

def safe_atan2(p1, p2):
    """
    Converts 2D cartesian points to polar angles in range 0 - 2pi
    """
        
    if (p1 > 0 and p2 >= 0): return atan(p2/(p1))
    elif (p1 == 0 and p2 >= 0): return pi/2
    elif (p1 < 0 and p2 >= 0): return -abs(atan(p2/p1)) + pi
    elif (p1 < 0 and p2 < 0): return atan(p2/p1) + pi
    elif (p1 > 0 and p2 < 0): return -abs(atan(p2/p1)) + 2*pi
    elif (p1 == 0 and p2 < 0): return pi * 3/2
    elif (p1 == 0 and p2 == 0): return pi * 3/2 # edge case
    
def RotMatrix3D(rotation=[0,0,0],is_radians=True, order='xyz'):
    """
    Create 3D Rotation Matrix from given roll,pitch,yaw angles
    
    :param rotation: List of [roll, pitch, yaw]
    :param is_radians: Whether 
    :param order: rotation order
    """
    # https://en.wikipedia.org/wiki/Rotation_matrix#General_3D_rotations
    
    roll, pitch, yaw = rotation[0], rotation[1], rotation[2]

    if not is_radians: 
        roll = radians(roll)
        pitch = radians(pitch)
        yaw = radians(yaw)
    
    # rotation matrix about each axis  (x = roll, y = pitch, z = yaw)
    rotX = np.matrix([[1, 0, 0], [0, cos(roll), -sin(roll)], [0, sin(roll), cos(roll)]])
    rotY = np.matrix([[cos(pitch), 0, sin(pitch)], [0, 1, 0], [-sin(pitch), 0, cos(pitch)]])
    rotZ = np.matrix([[cos(yaw), -sin(yaw), 0], [sin(yaw), cos(yaw), 0], [0, 0, 1]])
    
    # Rotation matrix order
    # Matrix multiplications are applied right to left
    if order == 'xyz': rotationMatrix = rotZ * rotY * rotX # ZYX Intrinsic
    elif order == 'xzy': rotationMatrix = rotY * rotZ * rotX
    elif order == 'yxz': rotationMatrix = rotZ * rotX * rotY
    elif order == 'yzx': rotationMatrix = rotX * rotZ * rotY
    elif order == 'zxy': rotationMatrix = rotY * rotX * rotZ
    elif order == 'zyx': rotationMatrix = rotX * rotY * rotZ
    
    return rotationMatrix # roll pitch and yaw rotation 
