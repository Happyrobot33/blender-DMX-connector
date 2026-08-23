import socket
import json
import bpy
from pathlib import Path
from bthl.operator.global_settings_modal import GlobalSettingsToggleModal


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


def send_frame_snapshot_for_frame(context: "bpy.types.Context", frame_number: int) -> bool:
    """
    Send a UDP packet requesting a frame snapshot save for the current state of the
    scene, then wait for the resulting file to be written.

    Args:
        context: The Blender context
        frame_number: The frame number the scene is currently set to

    Returns:
        bool: True if the file was written before the timeout, False otherwise
    """
    # Local import to avoid a circular import with frame_snapshot_modal
    from bthl.operator.frame_snapshot_modal import FrameSnapshotSettings

    try:
        export_dir = get_frame_export_directory()
    except ValueError as e:
        if GlobalSettingsToggleModal.get_debug_enabled(context):
            print(f"Frame snapshot export disabled: {e}")
        return False

    port = FrameSnapshotSettings.get_export_port(context)
    frame_file_path = export_dir / f"frame_{frame_number:06d}.png"

    packet = {
        "command": "save_frame",
        "frame_number": frame_number,
        "file_path": str(frame_file_path)
    }

    send_udp_packet("localhost", port, json.dumps(packet))

    timeout = FrameSnapshotSettings.get_frame_write_timeout(context)
    written = wait_for_file(frame_file_path, timeout)

    if GlobalSettingsToggleModal.get_debug_enabled(context):
        print(f"Frame snapshot packet sent for frame {frame_number} to port {port}")

    return written


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


def wait_for_file(file_path: Path, timeout: float = 5.0, poll_interval: float = 0.01) -> bool:
    """
    Wait for a file to be created with a timeout.
    
    Args:
        file_path: Path to the file to wait for
        timeout: Maximum time to wait in seconds
        poll_interval: How often to check if file exists in seconds

    Returns:
        bool: True if the file appeared before the timeout, False otherwise
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if file_path.exists():
            return True
        time.sleep(poll_interval)
    
    return False
