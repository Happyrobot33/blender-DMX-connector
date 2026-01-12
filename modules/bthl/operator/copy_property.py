import bpy

class OBJECT_OT_copy_custom_property_to_selected(bpy.types.Operator):
    bl_idname = "object.copy_custom_property_to_selected"
    bl_label = "Copy Custom Property to Selected Objects"
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

        for obj in context.selected_objects:
            if obj == active:
                continue

            # Data-block properties (Objects, Texts, Materials, etc.) are handled
            # by direct assignment. Blender's ID property system supports storing
            # references to any bpy.types.ID subclass (data-blocks).
            # The reference is copied, not the data-block itself.
            obj[self.property_name] = value

            ui = obj.id_properties_ui(self.property_name)
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
            OBJECT_OT_copy_custom_property_to_selected.bl_idname,
            text="Copy Custom Property to Selected Objects",
            icon='DUPLICATE'
        )
        op.property_name = context.button_prop.identifier

    @staticmethod
    def register():
        bpy.types.UI_MT_button_context_menu.append(OBJECT_OT_copy_custom_property_to_selected.draw_custom_property_context_menu)

    @staticmethod
    def unregister():
        bpy.types.UI_MT_button_context_menu.remove(OBJECT_OT_copy_custom_property_to_selected.draw_custom_property_context_menu)
