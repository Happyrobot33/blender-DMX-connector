import bpy
from bpy.types import Operator, Context
from bpy.props import BoolProperty, IntProperty, FloatProperty


class FrameSnapshotToggleModal(Operator):
    """Toggle operator for frame snapshot export on/off"""
    bl_idname = "bthl.frame_snapshot_toggle"
    bl_label = "Frame Snapshot Export Toggle"
    bl_description = "Toggle frame snapshot export on/off"
    bl_options = {'REGISTER', 'UNDO'}

    export_enabled_prop_name = "frame_snapshot_export_enabled"
    export_port_prop_name = "frame_snapshot_export_port"
    frame_write_timeout_prop_name = "frame_snapshot_write_timeout"

    @staticmethod
    def get_export_enabled(context: Context) -> bool:
        """Get the current export enabled state"""
        return getattr(context.scene, FrameSnapshotToggleModal.export_enabled_prop_name, False)
    
    @staticmethod
    def get_export_port(context: Context) -> int:
        """Get the configured export port"""
        return getattr(context.scene, FrameSnapshotToggleModal.export_port_prop_name, 9123)
    
    @staticmethod
    def get_frame_write_timeout(context: Context) -> float:
        """Get the configured frame write timeout in seconds"""
        return getattr(context.scene, FrameSnapshotToggleModal.frame_write_timeout_prop_name, 5.0)
    
    def execute(self, context: Context):
        """Toggle frame snapshot export state"""
        
        # Get current state or default to False
        current_state = getattr(context.scene, FrameSnapshotToggleModal.export_enabled_prop_name, False)
        
        # Toggle the state
        new_state = not current_state
        setattr(context.scene, FrameSnapshotToggleModal.export_enabled_prop_name, new_state)
        
        # Report the new state
        status = "ON" if new_state else "OFF"
        self.report({'INFO'}, f"Frame Snapshot Export: {status}")
        
        return {'FINISHED'}

    @staticmethod
    def dynamic_text(context: Context) -> str:
        """Dynamically change button text based on state"""
        current_state = getattr(context.scene, FrameSnapshotToggleModal.export_enabled_prop_name, False)
        return "Stop Frame Snapshot Export" if current_state else "Start Frame Snapshot Export"

    @staticmethod
    def register():
        """Register the operator and its properties"""
        bpy.types.Scene.frame_snapshot_export_enabled = BoolProperty(
            name="Frame Snapshot Export Enabled",
            description="Enable frame snapshot export during rendering",
            default=False
        )
        
        bpy.types.Scene.frame_snapshot_export_port = IntProperty(
            name="Frame Snapshot Export Port",
            description="UDP port for frame snapshot export packets",
            default=9123,
            min=1,
            max=65535
        )
        
        bpy.types.Scene.frame_snapshot_write_timeout = FloatProperty(
            name="Frame Snapshot Write Timeout",
            description="Maximum seconds to wait for file to be created after sending UDP packet",
            default=5.0,
            min=0.1,
            max=30.0,
            step=10,
            precision=1
        )

    @staticmethod
    def unregister():
        """Unregister the operator and its properties"""
        if hasattr(bpy.types.Scene, FrameSnapshotToggleModal.export_enabled_prop_name):
            del bpy.types.Scene.frame_snapshot_export_enabled
        if hasattr(bpy.types.Scene, FrameSnapshotToggleModal.export_port_prop_name):
            del bpy.types.Scene.frame_snapshot_export_port
        if hasattr(bpy.types.Scene, FrameSnapshotToggleModal.frame_write_timeout_prop_name):
            del bpy.types.Scene.frame_snapshot_write_timeout
