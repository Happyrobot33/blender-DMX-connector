#import bpy
import mathutils
import math

def scale_number(unscaled: float, to_min: float, to_max: float, from_min: float, from_max: float) -> float:
    #clamp the value
    value = (to_max-to_min)*(unscaled-from_min)/(from_max-from_min)+to_min
    return max(min(value, to_max), to_min)

#these took. WAY TOO LONG. to figure out. save me
def convert_blender_quat_to_unity_quat(blender_quat: mathutils.Quaternion) -> mathutils.Quaternion:
    """Converts a Blender Quaternion to a Unity Quaternion"""
    oq = blender_quat
    #rotate around the Z axis in blender first
    initialfixrot = mathutils.Euler((math.radians(0),math.radians(0),math.radians(90 + 180)))
    oq = initialfixrot.to_quaternion() @ oq
    
    
    baserot = mathutils.Euler((math.radians(-90),math.radians(0),math.radians(0)))
    oq = baserot.to_quaternion() @ mathutils.Quaternion((oq.w, oq.x, -oq.y, -oq.z))
    return oq

def convert_unity_quat_to_unity_euler(unity_quat: mathutils.Quaternion, order: str = "ZXY") -> mathutils.Euler:
    """Converts a Unity Quaternion to a Unity Euler rotation, ZXY is the default application order used by Unity"""
    return unity_quat.to_euler(order)
