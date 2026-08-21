import bpy
from bthl.tasks.task import Task
import socket
import struct
import random
import time

sock = None
last_timecode_frame = None
current_port = None
last_frames = None
last_milliseconds = None

def receive() -> float:
    from bthl.operator.receiver_modal import MIDITimecodeToggleModal
    global sock, current_port
    update_rate = 0.001
    scene = bpy.context.scene

    if not MIDITimecodeToggleModal.get_timecode_receive_enabled(bpy.context):
        return update_rate

    receivebuffer_size = 64
    port = MIDITimecodeToggleModal.get_timecode_port(bpy.context)

    # Check if we need to recreate the socket due to port change
    if sock is not None and current_port != port:
        sock.close()
        sock = None

    #receive via udp socket
    if sock is None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #make the receive buffer small
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, receivebuffer_size)
        #bind to the configured port
        try:
            sock.bind(("localhost", port))
            sock.setblocking(False)
            current_port = port
        except OSError as e:
            print(f"Failed to bind socket to port {port}: {e}")
            sock.close()
            sock = None
            return update_rate

    try:
        data, addr = sock.recvfrom(receivebuffer_size)
        # print(f"Received message from {addr}: {data}")
        #the data coming in is a signed long long in bytes, big endian
        milliseconds = int.from_bytes(data[0:4], byteorder='big', signed=True)

        #frames is a single byte
        frames = data[4]
        # print(len(data))
        
        # Discard frames that jump to 0 without milliseconds changing
        # Non correct fix, but should fix timecode seconds jumping theoretically
        global last_frames, last_milliseconds
        if last_frames != 0 and frames == 0 and last_milliseconds is not None and milliseconds == last_milliseconds:
            print(f"Discarding spurious frames jump to 0: frames={frames}, milliseconds={milliseconds}")
            last_frames = frames
            last_milliseconds = milliseconds
            return update_rate

        last_frames = frames
        
        #get the scene
        fps = scene.render.fps / scene.render.fps_base
        #convert the value to frames
        frame = frames
        #use round() instead of int(): fractional fps (e.g. 29.97) causes float error that lands just under
        #whole-second boundaries, and int() truncates that down a frame instead of rounding to the correct one
        frame += round((milliseconds / 1000) * fps)
        
        # Apply timecode offset
        frame_offset = MIDITimecodeToggleModal.get_timecode_offset_frames(bpy.context)
        frame += frame_offset
        
        # Track frame and millisecond values
        last_milliseconds = milliseconds
        
        global last_timecode_frame
        #set the current frame of the scene
        #check if we are still on this frame, if so do nothing
        should_set_frame = False
        
        if not MIDITimecodeToggleModal.get_timecode_allow_timeline_move(bpy.context):
            # If timeline move is FALSE: set frame whenever scene frame is different
            should_set_frame = (scene.frame_current != frame)
        else:
            # If timeline move is TRUE: set frame when scene frame is different AND timecode frame has changed
            should_set_frame = (scene.frame_current != frame and last_timecode_frame != frame)
        
        if should_set_frame:
            scene.frame_set(frame)
            
        # Track the last received timecode frame
        last_timecode_frame = frame
        
        return update_rate
    except BlockingIOError:
        #no data received
        return update_rate


def get_last_timecode_frame():
    """Get the last received timecode frame value"""
    global last_timecode_frame
    return last_timecode_frame
