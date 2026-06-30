from bpy.types import Panel, Context
import bthl.operator.sender_modal as sender_modal
import bthl.operator.receiver_modal as receiver_modal
import bthl.operator.gdtf_modal as gdtf_modal
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
        custom_props_box.prop(scene, "sync_properties_to_selected", text="Sync Active to Selected")
        if scene.sync_properties_to_selected:
            sync_row = custom_props_box.row()
            sync_row.label(text="Property changes will sync to other selected objects", icon='INFO')

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
        
        # GDTF Share controls
        gdtf_box = layout.box()
        gdtf_box.label(text="GDTF Share Integration")
        gdtf_box.label(text="Access lighting fixtures from GDTF Share", icon='INFO')
        
        if not scene.gdtf_logged_in:
            # Login section
            login_row = gdtf_box.row()
            login_op = login_row.operator(
                gdtf_modal.GDTFPasswordInputModal.bl_idname,
                text="Login to GDTF Share"
            )
            
            # Display any login errors
            if scene.gdtf_last_error:
                error_row = gdtf_box.row()
                error_row.label(text=scene.gdtf_last_error, icon='ERROR')
        else:
            # Logged in section
            status_row = gdtf_box.row()
            status_row.label(text=f"Logged in | {scene.gdtf_fixture_count} fixtures available", icon='CHECKMARK')
            
            # DMX Universe and Channel configuration
            config_box = gdtf_box.box()
            config_box.label(text="Fixture Settings")
            config_row = config_box.row(align=True)
            config_row.prop(scene, "gdtf_fixture_universe", text="Universe")
            config_row.prop(scene, "gdtf_fixture_channel", text="Channel")
            
            # Fixture Search Section
            search_box = gdtf_box.box()
            search_box.label(text="Search & Browse")
            
            search_op = search_box.operator(gdtf_modal.GDTFSearchModal.bl_idname, text="Search Fixtures", icon='ZOOM_ALL')
            
            # Display search results if any
            if scene.gdtf_search_results:
                results_box = search_box.box()
                results_box.label(text=f"Results ({len(scene.gdtf_search_results)})")
                
                # List results with selection
                for idx, result in enumerate(scene.gdtf_search_results):
                    result_row = results_box.row()
                    
                    # Selection indicator
                    if idx == scene.gdtf_search_result_index:
                        result_row.label(text="●", icon='RADIOBUT_ON')
                    else:
                        result_row.label(text="○", icon='RADIOBUT_OFF')
                    
                    # Fixture info
                    info_text = f"{result.fixture} ({result.manufacturer})"
                    result_row.label(text=info_text)
                    
                    # Click to select
                    select_op = result_row.operator("wm.context_set_int", text="", icon='RADIOBUT_OFF')
                    select_op.data_path = "scene.gdtf_search_result_index"
                    select_op.value = idx
                
                # Add to scene button for selected result
                if scene.gdtf_search_results:
                    selected_result = scene.gdtf_search_results[min(scene.gdtf_search_result_index, len(scene.gdtf_search_results) - 1)]
                    action_row = search_box.row()
                    action_row.label(text=f"Selected: U{selected_result.universe}_C{selected_result.channel} - {selected_result.fixture}")
                    add_btn = action_row.operator(
                        gdtf_modal.GDTFDownloadResultModal.bl_idname,
                        text="Add to Scene",
                        icon='ADD'
                    )
            
            # Buttons
            button_row = gdtf_box.row(align=True)
            list_op = button_row.operator(
                "wm.url_open",
                text="Browse Online",
                icon='WINDOW'
            )
            list_op.url = "https://gdtf-share.com/"
            
            logout_op = button_row.operator(
                gdtf_modal.GDTFShareToggleModal.bl_idname,
                text="Logout",
                icon='PANEL_CLOSE'
            )
            logout_op.action = "logout"
            
            # Display status messages
            if scene.gdtf_last_error:
                status_box = gdtf_box.box()
                status_box.label(text=scene.gdtf_last_error, icon='INFO')
