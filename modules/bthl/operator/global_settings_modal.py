import bpy
from bpy.types import Operator, Context
from bpy.props import BoolProperty

class GlobalSettingsToggleModal(Operator):
    """Operator for managing global addon settings"""
    bl_idname = "bthl.global_settings_toggle"
    bl_label = "Global Settings"
    bl_description = "Configure global addon settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    debug_enabled_prop_name = "debug_enabled"
    
    @staticmethod
    def get_debug_enabled(context: Context):
        """Get the global debug toggle state"""
        return getattr(context.scene, GlobalSettingsToggleModal.debug_enabled_prop_name, False)
    
    def execute(self, context: Context):
        """No-op execute for this settings operator"""
        return {'FINISHED'}
    
    @staticmethod
    def register():
        """Register scene properties"""
        bpy.types.Scene.debug_enabled = BoolProperty(
            name="Debug Enabled",
            description="Enable debug print statements for the addon",
            default=False
        )
    
    @staticmethod
    def unregister():
        """Unregister scene properties"""
        if hasattr(bpy.types.Scene, GlobalSettingsToggleModal.debug_enabled_prop_name):
            del bpy.types.Scene.debug_enabled
