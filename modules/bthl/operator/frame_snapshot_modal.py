import bpy
import time
from bpy.types import Operator, Context
from bpy.props import BoolProperty, IntProperty, FloatProperty
from bthl.operator.global_settings_modal import GlobalSettingsToggleModal


class FrameSnapshotSettings:
    """Shared scene property helpers for frame snapshot export settings"""

    export_port_prop_name = "frame_snapshot_export_port"
    frame_write_timeout_prop_name = "frame_snapshot_write_timeout"
    range_start_prop_name = "frame_snapshot_range_start"
    range_end_prop_name = "frame_snapshot_range_end"
    running_prop_name = "frame_snapshot_running"
    current_frame_prop_name = "frame_snapshot_current_frame"
    cancel_requested_prop_name = "frame_snapshot_cancel_requested"
    frames_done_prop_name = "frame_snapshot_frames_done"
    start_time_prop_name = "frame_snapshot_start_time"

    @staticmethod
    def get_export_port(context: Context) -> int:
        return getattr(context.scene, FrameSnapshotSettings.export_port_prop_name, 9123)

    @staticmethod
    def get_frame_write_timeout(context: Context) -> float:
        return getattr(context.scene, FrameSnapshotSettings.frame_write_timeout_prop_name, 5.0)

    @staticmethod
    def get_range_start(context: Context) -> int:
        return getattr(context.scene, FrameSnapshotSettings.range_start_prop_name, context.scene.frame_start)

    @staticmethod
    def get_range_end(context: Context) -> int:
        return getattr(context.scene, FrameSnapshotSettings.range_end_prop_name, context.scene.frame_end)

    @staticmethod
    def get_running(context: Context) -> bool:
        return getattr(context.scene, FrameSnapshotSettings.running_prop_name, False)

    @staticmethod
    def get_current_frame(context: Context) -> int:
        return getattr(context.scene, FrameSnapshotSettings.current_frame_prop_name, 0)

    @staticmethod
    def get_frames_done(context: Context) -> int:
        return getattr(context.scene, FrameSnapshotSettings.frames_done_prop_name, 0)

    @staticmethod
    def get_total_frames(context: Context) -> int:
        total = FrameSnapshotSettings.get_range_end(context) - FrameSnapshotSettings.get_range_start(context) + 1
        return max(total, 0)

    @staticmethod
    def get_progress_stats(context: Context) -> dict:
        """Compute percentage, remaining frame count, and export speed (frames/sec)"""
        import time

        total = FrameSnapshotSettings.get_total_frames(context)
        done = FrameSnapshotSettings.get_frames_done(context)
        start_time = getattr(context.scene, FrameSnapshotSettings.start_time_prop_name, 0.0)
        elapsed = time.time() - start_time if start_time > 0 else 0.0

        speed = (done / elapsed) if elapsed > 0 and done > 0 else 0.0
        remaining = max(total - done, 0)
        percentage = (done / total * 100.0) if total > 0 else 0.0
        eta_seconds = (remaining / speed) if speed > 0 else None

        return {
            "total": total,
            "done": done,
            "remaining": remaining,
            "percentage": percentage,
            "speed": speed,
            "eta_seconds": eta_seconds,
        }

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format a duration in seconds as a compact h/m/s string, e.g. "1h 4m 2s"""
        total_seconds = int(round(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    @staticmethod
    def register():
        """Register the scene properties"""
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

        bpy.types.Scene.frame_snapshot_range_start = IntProperty(
            name="Start Frame",
            description="First frame to export",
            default=1
        )

        bpy.types.Scene.frame_snapshot_range_end = IntProperty(
            name="End Frame",
            description="Last frame to export",
            default=250
        )

        bpy.types.Scene.frame_snapshot_running = BoolProperty(
            name="Frame Snapshot Export Running",
            description="Whether a frame snapshot export is currently in progress",
            default=False,
            options={'HIDDEN', 'SKIP_SAVE'}
        )

        bpy.types.Scene.frame_snapshot_current_frame = IntProperty(
            name="Frame Snapshot Current Frame",
            description="Frame currently being exported",
            default=0,
            options={'HIDDEN', 'SKIP_SAVE'}
        )

        bpy.types.Scene.frame_snapshot_cancel_requested = BoolProperty(
            name="Frame Snapshot Cancel Requested",
            description="Internal flag used to request cancellation from the UI",
            default=False,
            options={'HIDDEN', 'SKIP_SAVE'}
        )

        bpy.types.Scene.frame_snapshot_frames_done = IntProperty(
            name="Frame Snapshot Frames Done",
            description="Number of frames exported so far in the current run",
            default=0,
            options={'HIDDEN', 'SKIP_SAVE'}
        )

        bpy.types.Scene.frame_snapshot_start_time = FloatProperty(
            name="Frame Snapshot Start Time",
            description="Timestamp the current export started at, used to estimate speed",
            default=0.0,
            options={'HIDDEN', 'SKIP_SAVE'}
        )

    @staticmethod
    def unregister():
        """Unregister the scene properties"""
        for prop_name in (
            FrameSnapshotSettings.export_port_prop_name,
            FrameSnapshotSettings.frame_write_timeout_prop_name,
            FrameSnapshotSettings.range_start_prop_name,
            FrameSnapshotSettings.range_end_prop_name,
            FrameSnapshotSettings.running_prop_name,
            FrameSnapshotSettings.current_frame_prop_name,
            FrameSnapshotSettings.cancel_requested_prop_name,
            FrameSnapshotSettings.frames_done_prop_name,
            FrameSnapshotSettings.start_time_prop_name,
        ):
            if hasattr(bpy.types.Scene, prop_name):
                delattr(bpy.types.Scene, prop_name)


class FrameSnapshotRangeModal(Operator):
    """Modal operator that steps through a frame range, sending a frame snapshot after each frame is calculated"""
    bl_idname = "bthl.frame_snapshot_range_export"
    bl_label = "Export Frame Snapshot Range"
    bl_description = "Step through the configured frame range and export a snapshot for each frame. Press ESC to cancel"
    bl_options = {'REGISTER'}

    _timer = None
    _frame_iter = None
    _original_frame = None

    def invoke(self, context: Context, event):
        # Local import to avoid a circular import with frame_snapshot_exporter
        from bthl.tasks.frame_snapshot_exporter import send_frame_snapshot_for_frame
        self._send_frame_snapshot_for_frame = send_frame_snapshot_for_frame

        scene = context.scene

        if FrameSnapshotSettings.get_running(context):
            self.report({'WARNING'}, "Frame snapshot export already running")
            return {'CANCELLED'}

        start = FrameSnapshotSettings.get_range_start(context)
        end = FrameSnapshotSettings.get_range_end(context)
        if start > end:
            self.report({'ERROR'}, "Start frame must be less than or equal to end frame")
            return {'CANCELLED'}

        self._original_frame = scene.frame_current
        self._frame_iter = iter(range(start, end + 1))
        scene.frame_snapshot_running = True
        scene.frame_snapshot_cancel_requested = False
        scene.frame_snapshot_frames_done = 0
        scene.frame_snapshot_start_time = time.time()

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context: Context, event):
        scene = context.scene

        if event.type in {'ESC', 'RIGHTMOUSE'} or scene.frame_snapshot_cancel_requested:
            return self._finish(context, cancelled=True)

        if event.type == 'TIMER':
            frame = next(self._frame_iter, None)
            if frame is None:
                return self._finish(context, cancelled=False)

            scene.frame_snapshot_current_frame = frame
            # Move the timeline; this triggers depsgraph/frame handlers which
            # calculate and send the DMX data for the frame synchronously
            scene.frame_set(frame)

            success = self._send_frame_snapshot_for_frame(context, frame)
            if not success and GlobalSettingsToggleModal.get_debug_enabled(context):
                print(f"Frame snapshot export: timed out waiting for frame {frame} to be written")

            scene.frame_snapshot_frames_done += 1

            # Progress properties changed - force the sidebar panel to redraw
            for area in context.screen.areas:
                area.tag_redraw()

            return {'RUNNING_MODAL'}

        # Let other events (e.g. clicking the Cancel button) reach the UI
        return {'PASS_THROUGH'}

    def _finish(self, context: Context, cancelled: bool):
        scene = context.scene
        wm = context.window_manager

        if self._timer is not None:
            wm.event_timer_remove(self._timer)
            self._timer = None

        if self._original_frame is not None:
            scene.frame_set(self._original_frame)

        scene.frame_snapshot_running = False
        scene.frame_snapshot_cancel_requested = False
        scene.frame_snapshot_current_frame = 0
        scene.frame_snapshot_frames_done = 0
        scene.frame_snapshot_start_time = 0.0

        if cancelled:
            self.report({'INFO'}, "Frame snapshot export cancelled")
            return {'CANCELLED'}

        self.report({'INFO'}, "Frame snapshot export finished")
        return {'FINISHED'}

    @staticmethod
    def dynamic_text(context: Context) -> str:
        return "Cancel Frame Snapshot Export" if FrameSnapshotSettings.get_running(context) else "Start Frame Snapshot Export"


class FrameSnapshotCancelOperator(Operator):
    """Requests cancellation of a running frame snapshot export"""
    bl_idname = "bthl.frame_snapshot_cancel"
    bl_label = "Cancel Frame Snapshot Export"
    bl_description = "Cancel the currently running frame snapshot export"
    bl_options = {'REGISTER'}

    def execute(self, context: Context):
        context.scene.frame_snapshot_cancel_requested = True
        return {'FINISHED'}
