import bpy
from bpy.types import Operator, Context
from bpy.props import BoolProperty

class CustomPropertiesToggleModal(Operator):
    """Operator for managing custom properties settings"""
    bl_idname = "bthl.custom_properties_toggle"
    bl_label = "Custom Properties Settings"
    bl_description = "Configure custom properties behavior"
    bl_options = {'REGISTER', 'UNDO'}
    
    serialize_invisible_prop_name = "serialize_invisible"
    
    @staticmethod
    def get_serialize_invisible(context: Context):
        """Get the serialize invisible objects toggle state"""
        return getattr(context.scene, CustomPropertiesToggleModal.serialize_invisible_prop_name, True)
    
    def execute(self, context: Context):
        """No-op execute for this settings operator"""
        return {'FINISHED'}
    
    @staticmethod
    def register():
        """Register scene properties"""
        bpy.types.Scene.serialize_invisible = BoolProperty(
            name="Serialize Invisible Objects",
            description="Include objects that are not visible when serializing custom properties",
            default=True
        )
    
    @staticmethod
    def unregister():
        """Unregister scene properties"""
        if hasattr(bpy.types.Scene, CustomPropertiesToggleModal.serialize_invisible_prop_name):
            del bpy.types.Scene.serialize_invisible
