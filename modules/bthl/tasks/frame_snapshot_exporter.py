import socket
import json
import bpy
import os
import time
from pathlib import Path
from bthl.operator.frame_snapshot_modal import FrameSnapshotToggleModal
from bthl.operator.global_settings_modal import GlobalSettingsToggleModal
from bthl.tasks.task import Task, HandlerType


def get_frame_export_directory() -> Path:
    """
    Get the export directory for frame snapshots.
    Creates a folder next to the blend file with _frames suffix.
    
    Returns:
        Path: The frame export directory
    """
    blend_file = bpy.data.filepath
    if not blend_file:
        raise ValueError("Blender file must be saved before exporting frames")
    
    blend_path = Path(blend_file)
    export_dir = blend_path.parent / f"{blend_path.stem}_frames"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    return export_dir


def send_frame_snapshot(scene: bpy.types.Scene, depsgraph=None) -> float:
    """
    Send a UDP packet with frame snapshot information when rendering.
    
    Args:
        scene: The Blender scene
        depsgraph: The dependency graph (optional)
    
    Returns:
        float: Interval for next call (required for timer functions)
    """
    try:
        context = bpy.context
        
        # Check if frame snapshot export is enabled
        if not FrameSnapshotToggleModal.get_export_enabled(context):
            return 0.1
        
        # Get configuration
        port = FrameSnapshotToggleModal.get_export_port(context)
        frame_number = scene.frame_current
        
        # Get frame export directory
        try:
            export_dir = get_frame_export_directory()
        except ValueError as e:
            if GlobalSettingsToggleModal.get_debug_enabled(context):
                print(f"Frame snapshot export disabled: {e}")
            return 0.1
        
        # Create the frame file path
        frame_file_path = export_dir / f"frame_{frame_number:06d}.png"
        
        # Create the packet
        packet = {
            "command": "save_frame",
            "frame_number": frame_number,
            "file_path": str(frame_file_path)
        }
        
        # Send via UDP
        json_message = json.dumps(packet)
        send_udp_packet("localhost", port, json_message)
        
        # Wait for file to be created (with timeout)
        timeout = FrameSnapshotToggleModal.get_frame_write_timeout(context)
        wait_for_file(frame_file_path, timeout)
        
        if GlobalSettingsToggleModal.get_debug_enabled(context):
            print(f"Frame snapshot packet sent for frame {frame_number} to port {port}")
        
    except Exception as e:
        print(f"Error in frame snapshot export: {e}")
    
    return 0.1


def send_udp_packet(host: str, port: int, message: str):
    """
    Send a UDP packet with the given message.
    
    Args:
        host: Target host
        port: Target UDP port
        message: Message to send
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(message.encode('utf-8'), (host, port))
    except Exception as e:
        print(f"Error sending UDP packet: {e}")
    finally:
        sock.close()


def wait_for_file(file_path: Path, timeout: float = 5.0, poll_interval: float = 0.01):
    """
    Wait for a file to be created with a timeout.
    
    Args:
        file_path: Path to the file to wait for
        timeout: Maximum time to wait in seconds
        poll_interval: How often to check if file exists in seconds
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if file_path.exists():
            return  # File was created, exit early
        time.sleep(poll_interval)
    
    # Timeout reached - log warning but continue


class FrameSnapshotExporterTask(Task):
    """Task for exporting frame snapshots via UDP during rendering"""
    functions = {
        HandlerType.RENDER_WRITE: send_frame_snapshot,
    }
