import bpy
from bpy.types import Operator, Context
from bpy.props import BoolProperty, StringProperty, IntProperty, FloatProperty
from typing import TYPE_CHECKING

class UDPClientToggleModal(Operator):
    """Simple toggle operator for UDP client on/off"""
    bl_idname = "bthl.udp_client_toggle"
    bl_label = "UDP Client Toggle"
    bl_description = "Toggle UDP client connection on/off"
    bl_options = {'REGISTER', 'UNDO'}

    udp_client_active_prop_name = "udp_client_active"
    udp_target_ip_prop_name = "udp_target_ip"
    udp_target_port_prop_name = "udp_target_port"
    universe_offset_prop_name = "universe_offset"
    auto_send_enabled_prop_name = "auto_send_enabled"
    auto_send_interval_prop_name = "auto_send_interval"

    @staticmethod
    def get_udp_client_state(context: Context):
        return getattr(context.scene, UDPClientToggleModal.udp_client_active_prop_name, False)
    
    @staticmethod
    def get_target_ip(context: Context):
        return getattr(context.scene, UDPClientToggleModal.udp_target_ip_prop_name, "127.0.0.1")
    
    @staticmethod
    def get_target_port(context: Context):
        return getattr(context.scene, UDPClientToggleModal.udp_target_port_prop_name, 6454)
    
    @staticmethod
    def get_universe_offset(context: Context):
        return getattr(context.scene, UDPClientToggleModal.universe_offset_prop_name, 0)
    
    @staticmethod
    def get_auto_send_enabled(context: Context):
        return getattr(context.scene, UDPClientToggleModal.auto_send_enabled_prop_name, False)
    
    @staticmethod
    def get_auto_send_interval(context: Context):
        return getattr(context.scene, UDPClientToggleModal.auto_send_interval_prop_name, 1.0)
    
    def execute(self, context: Context):
        """Toggle UDP client state and exit"""
        
        # Get current state or default to False
        current_state = getattr(context.scene, UDPClientToggleModal.udp_client_active_prop_name, False)
        
        # Toggle the state
        new_state = not current_state
        setattr(context.scene, UDPClientToggleModal.udp_client_active_prop_name, new_state)
        
        # Report the new state
        status = "ON" if new_state else "OFF"
        self.report({'INFO'}, f"UDP Client: {status}")
        
        return {'FINISHED'}

    @staticmethod
    def dynamic_text(context: Context):
        """Dynamically change button text based on state"""
        current_state = getattr(context.scene, UDPClientToggleModal.udp_client_active_prop_name, False)
        return "Stop UDP Client" if current_state else "Start UDP Client"

    @staticmethod
    def register():
        """Register the operator"""
        # Add scene property to store UDP client state globally
        bpy.types.Scene.udp_client_active = BoolProperty(
            name="UDP Client Active",
            description="Global UDP client active state",
            default=False
        )
        
        # Add scene properties for target IP and port
        bpy.types.Scene.udp_target_ip = StringProperty(
            name="Target IP",
            description="Target IP address for UDP packets",
            default="127.0.0.1"
        )
        
        bpy.types.Scene.udp_target_port = IntProperty(
            name="Target Port",
            description="Target port for UDP packets",
            default=6454,
            min=1,
            max=65535
        )
        
        # Add scene property for universe offset
        bpy.types.Scene.universe_offset = IntProperty(
            name="Universe Offset",
            description="Offset to add to DMX universe numbers when sending to ArtNet",
            default=0,
            min=0,
            max=32767
        )
        
        # Add scene properties for auto-send functionality
        bpy.types.Scene.auto_send_enabled = BoolProperty(
            name="Auto Send Enabled",
            description="Enable automatic sending of ArtNet data at regular intervals",
            default=False
        )
        
        bpy.types.Scene.auto_send_interval = FloatProperty(
            name="Auto Send Interval",
            description="Interval in seconds between automatic ArtNet data sends",
            default=1.0,
            min=0.1,
            max=60.0,
            step=10,
            precision=1
        )

    @staticmethod
    def unregister():
        """Unregister the operator"""
        # Remove scene properties
        if hasattr(bpy.types.Scene, UDPClientToggleModal.udp_client_active_prop_name):
            del bpy.types.Scene.udp_client_active
        if hasattr(bpy.types.Scene, UDPClientToggleModal.udp_target_ip_prop_name):
            del bpy.types.Scene.udp_target_ip
        if hasattr(bpy.types.Scene, UDPClientToggleModal.udp_target_port_prop_name):
            del bpy.types.Scene.udp_target_port
        if hasattr(bpy.types.Scene, UDPClientToggleModal.universe_offset_prop_name):
            del bpy.types.Scene.universe_offset
        if hasattr(bpy.types.Scene, UDPClientToggleModal.auto_send_enabled_prop_name):
            del bpy.types.Scene.auto_send_enabled
        if hasattr(bpy.types.Scene, UDPClientToggleModal.auto_send_interval_prop_name):
            del bpy.types.Scene.auto_send_interval

