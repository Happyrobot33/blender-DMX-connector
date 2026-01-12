import bpy

class OBJECT_OT_duplicate_custom_property(bpy.types.Operator):
    bl_idname = "object.duplicate_custom_property"
    bl_label = "Duplicate Custom Property"
    bl_options = {'REGISTER', 'UNDO'}

    property_name: bpy.props.StringProperty()

    def execute(self, context):
        active = context.active_object
        if not active:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        if self.property_name not in active.keys():
            self.report({'ERROR'}, "Property not found on active object")
            return {'CANCELLED'}

        value = active[self.property_name]

        # UI metadata (if any)
        ui_data = active.id_properties_ui(self.property_name)

        # Data-block properties (Objects, Texts, Materials, etc.) are handled
        # by direct assignment. Blender's ID property system supports storing
        # references to any bpy.types.ID subclass (data-blocks).
        # The reference is copied, not the data-block itself.
        active[self.property_name + "COPY"] = value

        ui = active.id_properties_ui(self.property_name + "COPY")
        if ui_data and ui:
            ui.update(**ui_data.as_dict())

        return {'FINISHED'}

    def draw_custom_property_context_menu(self, context):
        try: 
            prop = context.button_prop
            if not prop:
                return
        except Exception:
            return

        #owner = context.button_owner
        #if not isinstance(owner, bpy.types.Object):
        #    return

        layout = self.layout
        if layout is None:
            return
        op = layout.operator(
            OBJECT_OT_duplicate_custom_property.bl_idname,
            text="Duplicate Custom Property",
            icon='DUPLICATE'
        )
        op.property_name = context.button_prop.identifier

    @staticmethod
    def register():
        bpy.types.UI_MT_button_context_menu.append(OBJECT_OT_duplicate_custom_property.draw_custom_property_context_menu)

    @staticmethod
    def unregister():
        bpy.types.UI_MT_button_context_menu.remove(OBJECT_OT_duplicate_custom_property.draw_custom_property_context_menu)
