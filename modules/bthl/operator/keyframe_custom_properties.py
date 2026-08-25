import bpy

class OBJECT_OT_keyframe_custom_properties(bpy.types.Operator):
    """Keyframes all custom properties on the active object, excluding Universe/Channel"""
    bl_idname = "object.keyframe_custom_properties"
    bl_label = "Keyframe All Custom Properties"
    bl_options = {'REGISTER', 'UNDO'}

    excluded_properties = {"Universe", "Channel"}

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        frame = context.scene.frame_current
        count = 0
        for key in obj.keys():
            if key == "_RNA_UI" or key in self.excluded_properties:
                continue
            try:
                obj.keyframe_insert(data_path=f'["{key}"]', frame=frame)
                count += 1
            except TypeError:
                continue

        if count == 0:
            self.report({'WARNING'}, "No custom properties keyframed")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Keyframed {count} custom propert{'y' if count == 1 else 'ies'}")
        return {'FINISHED'}

    def draw_custom_properties_context_menu(self, context):
        if not context.active_object:
            return

        layout = self.layout
        if layout is None:
            return
        layout.separator()
        layout.operator(
            OBJECT_OT_keyframe_custom_properties.bl_idname,
            icon='KEYFRAME_HLT'
        )

    @staticmethod
    def register():
        bpy.types.UI_MT_button_context_menu.append(OBJECT_OT_keyframe_custom_properties.draw_custom_properties_context_menu)

    @staticmethod
    def unregister():
        bpy.types.UI_MT_button_context_menu.remove(OBJECT_OT_keyframe_custom_properties.draw_custom_properties_context_menu)
