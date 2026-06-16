import bpy
from bthl.tasks.task import Task, HandlerType

# Track the last state of the active object's properties for change detection
_last_active_object_state = {}

def _get_custom_properties_snapshot(obj: bpy.types.Object) -> dict:
    """Get a snapshot of all custom properties and their values for an object."""
    props_snapshot = {}
    if len(obj.keys()) > 1:
        for K in obj.keys():
            if K not in '_RNA_UI':
                try:
                    props_snapshot[K] = obj[K]
                except (KeyError, AttributeError):
                    pass
    return props_snapshot

def _detect_property_changes(new_state: dict, old_state: dict) -> dict:
    """Detect which properties have changed between two snapshots."""
    changes = {}
    for key, value in new_state.items():
        # Only detect as changed if it existed before and the value is different
        # This prevents detecting all properties as "changed" on first run
        if key in old_state and old_state[key] != value:
            changes[key] = value
    return changes

def _copy_properties_to_object(src_obj: bpy.types.Object, dest_obj: bpy.types.Object, properties_to_copy: dict):
    """Copy specific properties from source object to destination object."""
    for prop_name, prop_value in properties_to_copy.items():
        try:
            if prop_name in dest_obj and type(dest_obj[prop_name]) == type(prop_value):
                dest_obj[prop_name] = prop_value
        except (KeyError, AttributeError, TypeError):
            # Skip properties that can't be copied
            pass

def _sync_active_object_properties_to_selected():
    """If sync is enabled, copy changed properties from active object to all selected objects."""
    try:
        from bthl.operator.customproperties_modal import CustomPropertiesToggleModal
        context = bpy.context
        scene = context.scene
        
        # Check if syncing is enabled
        sync_enabled = CustomPropertiesToggleModal.get_sync_to_selected(context)
        if not sync_enabled:
            _last_active_object_state.clear()
            return
        
        active_obj = context.active_object
        if active_obj is None:
            _last_active_object_state.clear()
            return
        
        # Get current state of active object
        current_state = _get_custom_properties_snapshot(active_obj)
        
        # Get previous state (or empty dict if first run for this object)
        obj_id = id(active_obj)
        prev_state = _last_active_object_state.get(obj_id, {})
        
        # Detect changes (only properties that existed before and changed)
        changes = _detect_property_changes(current_state, prev_state)
        
        # If there are changes and other objects are selected, copy them
        if changes:
            selected_objects = [obj for obj in context.selected_objects if obj != active_obj]
            if selected_objects:
                for target_obj in selected_objects:
                    _copy_properties_to_object(active_obj, target_obj, changes)
        
        # Update the tracked state
        _last_active_object_state.clear()
        _last_active_object_state[obj_id] = current_state
        
    except Exception as e:
        print(f"Error syncing properties to selected objects: {e}")

def sync_properties_handler(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
    """Handler for syncing properties on frame changes and updates."""
    _sync_active_object_properties_to_selected()

class SyncPropertiesTask(Task):
    functions = {
        HandlerType.DEPSGRAPH_UPDATE_POST: sync_properties_handler,
        HandlerType.FRAME_CHANGE_POST: sync_properties_handler,
        HandlerType.LOAD_POST: sync_properties_handler
    }
