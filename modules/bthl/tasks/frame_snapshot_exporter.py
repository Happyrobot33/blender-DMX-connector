import socket
import json
import bpy
from pathlib import Path
from bthl.operator.global_settings_modal import GlobalSettingsToggleModal
from bthl.tasks.task import Task, HandlerType

FRAME_SNAPSHOT_RESPONSE_PORT = 9124
MAX_CONSECUTIVE_FAILURES = 4
_response_socket = None


def _get_response_socket():
    global _response_socket
    if _response_socket is None:
        _response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _response_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _response_socket.bind(("localhost", FRAME_SNAPSHOT_RESPONSE_PORT))
    return _response_socket


def _wait_for_snapshot_response(timeout: float) -> bool:
    response_socket = _get_response_socket()
    import time

    deadline = time.monotonic() + timeout

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False

        response_socket.settimeout(remaining)
        try:
            response_socket.recvfrom(65535)
            return True
        except socket.timeout:
            return False
        except ConnectionResetError:
            continue


def frame_snapshot_handler(scene: "bpy.types.Scene", depsgraph: "bpy.types.Depsgraph"):
    from bthl.operator.frame_snapshot_modal import FrameSnapshotSettings

    context = bpy.context
    if not FrameSnapshotSettings.get_running(context):
        return

    frame_number = FrameSnapshotSettings.get_current_frame(context)
    if frame_number != scene.frame_current:
        return

    success = send_frame_snapshot_for_frame(context, frame_number)
    if success:
        scene.frame_snapshot_consecutive_failures = 0
    else:
        scene.frame_snapshot_consecutive_failures += 1
        if GlobalSettingsToggleModal.get_debug_enabled(context):
            print(f"Frame snapshot export failed for frame {frame_number}")
        if scene.frame_snapshot_consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            scene.frame_snapshot_cancel_requested = True

    scene.frame_snapshot_frames_done += 1


class FrameSnapshotTask(Task):
    functions = {
        HandlerType.FRAME_CHANGE_POST: frame_snapshot_handler
    }


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
        "file_path": str(frame_file_path),
        "response_port": FRAME_SNAPSHOT_RESPONSE_PORT
    }

    response_socket = _get_response_socket()
    response_socket.setblocking(False)
    try:
        while True:
            response_socket.recvfrom(65535)
    except (BlockingIOError, ConnectionResetError):
        pass

    response_socket.sendto(json.dumps(packet).encode("utf-8"), ("localhost", port))

    timeout = FrameSnapshotSettings.get_frame_write_timeout(context)
    if not _wait_for_snapshot_response(timeout):
        if GlobalSettingsToggleModal.get_debug_enabled(context):
            print(f"Frame snapshot export: no response received for frame {frame_number}")
        return False

    # written = wait_for_file(frame_file_path, timeout)

    if GlobalSettingsToggleModal.get_debug_enabled(context):
        print(f"Frame snapshot packet sent for frame {frame_number} to port {port}")

    return True


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
