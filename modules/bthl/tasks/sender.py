import socket
import time
import bpy
from bthl.operator.sender_modal import UDPClientToggleModal
from bthl.operator.global_settings_modal import GlobalSettingsToggleModal
from bthl.types.ArtNet import ArtnetDMXPacket, ArtnetPollPacket
from bthl.tasks.customproperties import update_custom_properties
from bthl.tasks.task import Task, HandlerType
from bthl.api.dmxdata import dmx_buffer

# Module-level socket
_udp_socket = None

def _get_socket():
    """Get or create the UDP socket"""
    global _udp_socket
    if _udp_socket is None:
        _udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return _udp_socket

def _close_socket():
    """Close the UDP socket"""
    global _udp_socket
    if _udp_socket is not None:
        try:
            _udp_socket.close()
        except Exception as e:
            print(f"Error closing socket: {e}")
        _udp_socket = None

def auto_send() -> float:
    """Auto-send function that works like receiver.py"""
    #print("test")
    try:
        context = bpy.context
        scene = context.scene
        
        # Check if auto-send is enabled and UDP client is active
        if (not UDPClientToggleModal.get_auto_send_enabled(context) or 
            not UDPClientToggleModal.get_udp_client_state(context)):
            # Return a small interval to keep checking
            return 0.1
        
        #trigger custom property serialization and then send
        depsgraph = context.evaluated_depsgraph_get()
        update_custom_properties(scene, depsgraph)
        send(scene, depsgraph)
            
    except Exception as e:
        print(f"Error in auto-send: {e}")
    
    # Return the configured interval for the next call
    return UDPClientToggleModal.get_auto_send_interval(bpy.context)

def send_udp_packet(ip, port, message, id = 0):
    try:
        sock = _get_socket()
        sock.sendto(message, (ip, port))
        # Print if debug is enabled
        if GlobalSettingsToggleModal.get_debug_enabled(bpy.context):
            print(f"Sent message to {ip}:{port} (ID: {id})")
    except Exception as e:
        print(f"Error sending message: {e}")

def send(scene, depsgraph):
    #print("Sending DMX data via UDP...")
    #we should only send if the udp client is active
    if not UDPClientToggleModal.get_udp_client_state(bpy.context):
        #print("UDP Client is not active, skipping send.")
        return
    
    # Get configurable target IP, port, and universe offset
    target_ip = UDPClientToggleModal.get_target_ip(bpy.context)
    target_port = UDPClientToggleModal.get_target_port(bpy.context)
    universe_offset = UDPClientToggleModal.get_universe_offset(bpy.context)
    
    messages = ArtnetDMXPacket.global_dict_to_packets(dmx_buffer, universe_offset=universe_offset)

    for id, message in enumerate(messages):
        send_udp_packet(target_ip, target_port, message.pack(), id=id)
        #time.sleep(0.001)  # brief pause to avoid overwhelming the network
    
    dmx_buffer.clear()

class UDPClientTasks(Task):
    functions = {
        HandlerType.DEPSGRAPH_UPDATE_POST: send,
        HandlerType.FRAME_CHANGE_POST: send,
        HandlerType.LOAD_POST: send
    }
