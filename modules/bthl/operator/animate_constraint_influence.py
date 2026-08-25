import bpy
from bpy.types import Operator, Context
from bpy.props import IntProperty, EnumProperty, StringProperty

class OBJECT_OT_animate_constraint_influence(Operator):
    """Keyframes a constraint's influence to animate it in or out around the current frame"""
    bl_idname = "constraint.animate_influence"
    bl_label = "Animate Influence"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        items=[
            ('IN', "Animate In", "Influence goes from 0 at the start keyframe to 1 at the current frame"),
            ('OUT', "Animate Out", "Influence goes from 1 at the start keyframe to 0 at the current frame"),
        ],
        default='IN'
    )

    gap: IntProperty(
        name="Gap",
        description="Number of frames before the current frame to place the starting keyframe",
        default=10,
        min=1
    )

    constraint_name: StringProperty(options={'HIDDEN'})

    @staticmethod
    def find_constraint(context: Context, name: str):
        obj = context.active_object
        if obj:
            constraint = obj.constraints.get(name)
            if constraint:
                return constraint

        pbone = context.active_pose_bone
        if pbone:
            constraint = pbone.constraints.get(name)
            if constraint:
                return constraint

        return None

    def invoke(self, context: Context, event):
        self.gap = getattr(context.scene, "constraint_animate_gap", 10)
        return self.execute(context)

    def execute(self, context: Context):
        constraint = self.find_constraint(context, self.constraint_name)
        if constraint is None:
            self.report({'ERROR'}, f"Constraint '{self.constraint_name}' not found")
            return {'CANCELLED'}

        context.scene.constraint_animate_gap = self.gap

        current_frame = context.scene.frame_current
        start_frame = current_frame - self.gap
        start_value, end_value = (0.0, 1.0) if self.direction == 'IN' else (1.0, 0.0)

        constraint.influence = start_value
        constraint.keyframe_insert(data_path="influence", frame=start_frame)

        constraint.influence = end_value
        constraint.keyframe_insert(data_path="influence", frame=current_frame)

        return {'FINISHED'}

    def draw_constraint_context_menu(self, context):
        try:
            prop = context.button_prop
            owner = context.button_pointer
        except Exception:
            return

        if not prop or prop.identifier != "influence":
            return
        if not isinstance(owner, bpy.types.Constraint):
            return

        layout = self.layout
        if layout is None:
            return

        layout.separator()
        op_in = layout.operator(
            OBJECT_OT_animate_constraint_influence.bl_idname,
            text="Animate Influence In",
            icon='KEYFRAME_HLT'
        )
        op_in.direction = 'IN'
        op_in.constraint_name = owner.name

        op_out = layout.operator(
            OBJECT_OT_animate_constraint_influence.bl_idname,
            text="Animate Influence Out",
            icon='KEYFRAME_HLT'
        )
        op_out.direction = 'OUT'
        op_out.constraint_name = owner.name

    @staticmethod
    def register():
        bpy.types.Scene.constraint_animate_gap = IntProperty(
            name="Constraint Animate Gap",
            description="Default number of frames between the start and end keyframes when animating a constraint's influence",
            default=10,
            min=1
        )
        bpy.types.UI_MT_button_context_menu.append(OBJECT_OT_animate_constraint_influence.draw_constraint_context_menu)

    @staticmethod
    def unregister():
        bpy.types.UI_MT_button_context_menu.remove(OBJECT_OT_animate_constraint_influence.draw_constraint_context_menu)
        if hasattr(bpy.types.Scene, "constraint_animate_gap"):
            del bpy.types.Scene.constraint_animate_gap
