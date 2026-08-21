import bpy
from bpy.types import Operator, Context
from bpy.props import BoolProperty, StringProperty, IntProperty
from typing import TYPE_CHECKING
from bthl.tasks.receiver import get_last_timecode_frame

class MIDITimecodeOperator(Operator):
    """Operator for MIDI timecode control functions"""
    bl_idname = "bthl.midi_timecode_control"
    bl_label = "MIDI Timecode Control"
    bl_description = "Control MIDI timecode reception and timeline movement"
    bl_options = {'REGISTER', 'UNDO'}
    
    action: StringProperty()
    
    def execute(self, context: Context):
        if self.action == "sync_to_last_timecode":
            # Sync to last received timecode
            last_frame = get_last_timecode_frame()
            if last_frame is not None:
                context.scene.frame_set(last_frame)
                self.report({'INFO'}, f"Synced timeline to last received timecode (frame {last_frame})")
            else:
                self.report({'WARNING'}, "No timecode data received yet")
        
        return {'FINISHED'}


class MIDITimecodeToggleModal(Operator):
    """Simple toggle operator for MIDI timecode on/off"""
    bl_idname = "bthl.midi_timecode_toggle"
    bl_label = "MIDI Timecode Toggle"
    bl_description = "Toggle MIDI timecode reception on/off"
    bl_options = {'REGISTER', 'UNDO'}

    timecode_receive_enabled_prop_name = "timecode_receive_enabled"
    timecode_allow_timeline_move_prop_name = "timecode_allow_timeline_move"
    timecode_port_prop_name = "timecode_port"
    timecode_offset_frames_prop_name = "timecode_offset_frames"

    @staticmethod
    def get_timecode_receive_enabled(context: Context):
        return getattr(context.scene, MIDITimecodeToggleModal.timecode_receive_enabled_prop_name, False)
    
    @staticmethod
    def get_timecode_allow_timeline_move(context: Context):
        return getattr(context.scene, MIDITimecodeToggleModal.timecode_allow_timeline_move_prop_name, True)
    
    @staticmethod
    def get_timecode_port(context: Context):
        return getattr(context.scene, MIDITimecodeToggleModal.timecode_port_prop_name, 7001)
    
    @staticmethod
    def get_timecode_offset_frames(context: Context):
        return getattr(context.scene, MIDITimecodeToggleModal.timecode_offset_frames_prop_name, 0)

    @staticmethod
    def register():
        """Register the operator"""
        # Add MIDI timecode properties
        bpy.types.Scene.timecode_receive_enabled = BoolProperty(
            name="Receive MIDI Timecode",
            description="Enable/disable receiving MIDI timecode data",
            default=True
        )
        
        bpy.types.Scene.timecode_allow_timeline_move = BoolProperty(
            name="Allow Manual Timeline Movement",
            description="Allow moving the timeline freely if received timecode is not changing",
            default=True
        )
        
        bpy.types.Scene.timecode_port = IntProperty(
            name="MIDI Timecode Port",
            description="UDP port for receiving MIDI timecode data",
            default=7001,
            min=1,
            max=65535
        )
        
        bpy.types.Scene.timecode_offset_frames = IntProperty(
            name="Timecode Offset (Frames)",
            description="Offset timecode by this number of frames (positive for forward, negative for backward)",
            default=0,
            min=-9999,
            max=9999
        )

    @staticmethod
    def unregister():
        """Unregister the operator"""
        # Remove MIDI timecode properties
        if hasattr(bpy.types.Scene, MIDITimecodeToggleModal.timecode_receive_enabled_prop_name):
            del bpy.types.Scene.timecode_receive_enabled
        if hasattr(bpy.types.Scene, MIDITimecodeToggleModal.timecode_allow_timeline_move_prop_name):
            del bpy.types.Scene.timecode_allow_timeline_move
        if hasattr(bpy.types.Scene, MIDITimecodeToggleModal.timecode_port_prop_name):
            del bpy.types.Scene.timecode_port
        if hasattr(bpy.types.Scene, MIDITimecodeToggleModal.timecode_offset_frames_prop_name):
            del bpy.types.Scene.timecode_offset_frames
