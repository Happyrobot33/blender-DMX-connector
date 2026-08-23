bl_info = {
    "name": "Blender DMX Connector",
    "blender": (4, 5, 0),
    "category": "Object",
}

import bpy
import inspect
import sys
from bthl.tasks.task import Task, HandlerType
from bthl.panel.global_control import GlobalControlPanel
from bthl.operator.sender_modal import UDPClientToggleModal
from bthl.operator.global_settings_modal import GlobalSettingsToggleModal
from bthl.operator.customproperties_modal import CustomPropertiesToggleModal
from bthl.operator.receiver_modal import MIDITimecodeOperator, MIDITimecodeToggleModal
from bthl.operator.frame_snapshot_modal import FrameSnapshotSettings, FrameSnapshotRangeModal, FrameSnapshotCancelOperator
from bthl.operator.copy_property import OBJECT_OT_copy_custom_property_to_selected
from bthl.operator.setup_dmx_properties import OBJECT_OT_add_base_dmx_custom_properties
from bthl.operator.duplicate_property import OBJECT_OT_duplicate_custom_property
from bthl.tasks.sender import UDPClientTasks
from bthl.tasks.customproperties import CustomPropertiesTask
from bthl.tasks.sync_properties import SyncPropertiesTask
from bthl.tasks.receiver import receive
from bthl.tasks.sender import auto_send

classes = {
    GlobalControlPanel,
    UDPClientToggleModal,
    GlobalSettingsToggleModal,
    CustomPropertiesToggleModal,
    FrameSnapshotRangeModal,
    FrameSnapshotCancelOperator,
    MIDITimecodeOperator,
    MIDITimecodeToggleModal,
    OBJECT_OT_copy_custom_property_to_selected,
    OBJECT_OT_add_base_dmx_custom_properties,
    OBJECT_OT_duplicate_custom_property,
}

def fixorder(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
    #used to fix the order of critical handlers to be last
    for task in tasks:
        #print(f"Checking handlers for {task.__name__}")
        for handler_name, func in task._registered_handlers:
            #print(f"Handler {handler_name}: {func}")
            task.enforce_run_last(task, handler_name)
    
    #print out the function order in frame_change_post
    #print("Handler order for frame_change_post:")
    #for func in bpy.app.handlers.frame_change_post:
    #    print(func)

class FixOrderTask(Task):
    functions = {
        HandlerType.DEPSGRAPH_UPDATE_PRE: fixorder,
        HandlerType.FRAME_CHANGE_PRE: fixorder,
        HandlerType.LOAD_PRE: fixorder
    }

#This is maintained as an array to keep order
tasks = [
    FixOrderTask,
    SyncPropertiesTask,
    CustomPropertiesTask,
    UDPClientTasks, #This MUST be last so everything above it is allowed to run
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    for task in tasks:
        task.register(task)
    
    # Register properties for modals that have them
    MIDITimecodeToggleModal.register()
    UDPClientToggleModal.register()
    GlobalSettingsToggleModal.register()
    CustomPropertiesToggleModal.register()
    FrameSnapshotSettings.register()
    
    bpy.app.timers.register(receive, persistent=True)
    bpy.app.timers.register(auto_send, persistent=True)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    for task in tasks:
        task.unregister(task)
    
    # Unregister properties for modals that have them
    MIDITimecodeToggleModal.unregister()
    UDPClientToggleModal.unregister()
    GlobalSettingsToggleModal.unregister()
    CustomPropertiesToggleModal.unregister()
    FrameSnapshotSettings.unregister()
    
    bpy.app.timers.unregister(receive)
    bpy.app.timers.unregister(auto_send)
