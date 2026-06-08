from bpy.types import Panel, Context
import bthl.operator.sender_modal as sender_modal
import bthl.operator.receiver_modal as receiver_modal
from bthl.tasks.receiver import get_last_timecode_frame

class GlobalControlPanel(Panel):
    bl_label = "DMX Connector"
    bl_idname = "OBJECT_PT_main_panel"

    #Specific controls for the sidebar in the 3d view
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DMX Connector'

    def draw(self, context: Context):
        layout = self.layout
        if layout is None:
            return
        scene = context.scene

        # Global Settings
        global_box = layout.box()
        global_box.label(text="Global Settings")
        global_box.prop(scene, "debug_enabled", text="Debug Mode")
        
        # Custom Properties Settings
        custom_props_box = layout.box()
        custom_props_box.label(text="Custom Properties")
        custom_props_box.prop(scene, "serialize_invisible", text="Serialize Invisible Objects")

        # UDP Client controls
        box = layout.box()
        box.label(text="UDP Client Settings")
        
        # Target IP and Port inputs
        row = box.row()
        row.prop(scene, "udp_target_ip", text="Target IP")
        row.prop(scene, "udp_target_port", text="Port")
        
        # Universe offset input
        box.prop(scene, "universe_offset", text="Universe Offset")
        
        # Toggle button
        box.operator(sender_modal.UDPClientToggleModal.bl_idname, text=sender_modal.UDPClientToggleModal.dynamic_text(context))
        
        # Auto-send controls
        auto_send_box = box.box()
        auto_send_box.label(text="Auto Send Settings")
        auto_send_box.prop(scene, "auto_send_enabled", text="Enable Auto Send")
        
        # Show interval control only when auto-send is enabled
        if scene.auto_send_enabled:
            auto_send_box.prop(scene, "auto_send_interval", text="Interval (seconds)")
            # Show status when auto-send is active and UDP client is running
            if scene.udp_client_active:
                status_row = auto_send_box.row()
                status_row.label(text="Auto-sending active", icon='PLAY')

        
        # MIDI Timecode controls
        timecode_box = layout.box()
        timecode_box.label(text="MIDI Timecode Settings")
        timecode_box.label(text="Requires HNode MTC Exporter", icon='INFO')
        
        # Enable/disable timecode receiving
        timecode_box.prop(scene, "timecode_receive_enabled", text="Receive MIDI Timecode")
        
        # Display last received timecode
        last_timecode = get_last_timecode_frame()
        if last_timecode is not None:
            info_row = timecode_box.row()
            info_row.label(text=f"Last Timecode: Frame {last_timecode}", icon='TIME')
        else:
            info_row = timecode_box.row()
            info_row.label(text="Last Timecode: None received", icon='ERROR')
        
        # Show timeline controls only when timecode is enabled
        if scene.timecode_receive_enabled:
            timecode_box.prop(scene, "timecode_allow_timeline_move", text="Allow Free Timeline Movement")
            timecode_box.prop(scene, "timecode_latency_compensation_enabled", text="Latency Compensation")
            timecode_box.prop(scene, "timecode_port", text="MIDI Timecode Port")
            timecode_box.prop(scene, "timecode_offset_frames", text="Timecode Offset (Frames)")
            
            # Manual timeline control section
            if scene.timecode_allow_timeline_move:
                control_row = timecode_box.row(align=True)
                # Sync to last received timecode button
                op_sync = control_row.operator(receiver_modal.MIDITimecodeOperator.bl_idname, text="Sync to Last Timecode", icon='TIME')
                op_sync.action = "sync_to_last_timecode"
