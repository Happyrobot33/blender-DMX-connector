import idprop
import bpy
from bthl.tasks.task import Task, HandlerType
from bthl.api.dmxdata import get_channel_value, set_channel_value
from bthl.util.dmx import getColorAsDMX, getTupleAsDMX, getPanTiltAsDMX
from bthl.util.general import scale_number
import mathutils
import math

def handleobjectproperties(object: bpy.types.Object):
    #print("Handling properties for object:", object.name)
    properties = {}
    if len(object.keys()) > 1:
        # First item is _RNA_UI
        for K in object.keys():
            if K not in '_RNA_UI':
                try:
                    prop_ui = object.id_properties_ui(K)
                except TypeError: # does not support ui data
                    #print("No UI data for property:", K)
                    continue
                dict = prop_ui.as_dict()
                dict["value"] = object[K]
                properties[K] = dict
    
    #check if universe and channel are defined
    if "Universe" in properties and "Channel" in properties:
        #store these and convert to a global index
        universe = properties["Universe"]["value"]
        channel = properties["Channel"]["value"]
        globalChannel = (universe - 1) * 512 + (channel - 1)
        
        #now that we have the global channel index, interpret all custom props that have descriptions as offsets to the base channel
        for p in properties:
            #print("Processing property:", p)
            #ignore universe and channel props
            if p in ["Universe","Channel"]:
                continue
            #check if description field exists
            if "description" in properties[p]:
                if properties[p]["description"] != "":
                    props = properties[p]
                    #check if we can interpret as int
                    try:
                        #read the first section before the first space as the offset
                        #offset = int(props["description"])
                        offset_str = props["description"].split(" ")[0]
                        offset = int(offset_str)
                    except ValueError:
                        print("Not a valid offset:", props["description"])
                        continue
                    finalChannel = globalChannel + offset
                    #we now need to interpret it to a value
                    #floats should be converted from 0 to 1 to 0 to 255
                    #ints should be direct mapping
                    subtype = props["subtype"]
                    value = props["value"]
                    typ = type(value)
                    # if object.name == "Clouds":
                    #     print(typ)
                    if typ == int:
                        set_channel_value(finalChannel, value)
                    elif typ == float:
                        #read the second part of the description and if it says 16bit, we map to 16 bit instead
                        desc_parts = properties[p]["description"].split(" ")
                        #New method, grab the second channel we should write to
                        second_channel : int = finalChannel + 1
                        is_16bit = False
                        if len(desc_parts) > 1:
                            try:
                                if desc_parts[1].lower() == "16bit":
                                    #Old method, should be deprecated eventually. Maybe with an auto migration framework idk
                                    second_channel = finalChannel + 1
                                else:
                                    #New method, allows defining the fine channel somewhere else
                                    second_channel = globalChannel + int(desc_parts[1])
                                is_16bit = True
                            except ValueError:
                                is_16bit = False

                        #remap from the properties min and max if they exist
                        min_val = props.get("min", 0.0)
                        max_val = props.get("max", 1.0)
                        if is_16bit:
                            remapped = int(scale_number(value, 0, 65535, min_val, max_val))
                            set_channel_value(finalChannel, (remapped >> 8) & 0xFF)
                            set_channel_value(second_channel, remapped & 0xFF)
                        else:
                            remapped = int(scale_number(value, 0, 255, min_val, max_val))
                            set_channel_value(finalChannel, remapped)
                    elif typ == bool:
                        #first we need to check if this is composite or if this is a single channel boolean
                        #if its a single channel, we use the next two values to determine the off and on values
                        #if its composite, we use the next value for the bitmask, IE bit 0 is b0
                        desc_parts = properties[p]["description"].split(" ")
                        if len(desc_parts) == 1:
                            #do nothing, this is the assumed mode
                            set_channel_value(finalChannel, 255 if value else 0)
                        elif len(desc_parts) == 2:
                            #composite mode
                            #get the bitmask from the second value
                            try:
                                bitindex = int(desc_parts[1])
                                bitmask = 1 << bitindex
                                #read the current value of the channel
                                current_value: int | None = get_channel_value(finalChannel)
                                if current_value is None:
                                    current_value = 0
                                #set or clear the bit based on the boolean value
                                if value:
                                    new_value = current_value | bitmask
                                else:
                                    new_value = current_value & ~bitmask
                                set_channel_value(finalChannel, new_value)
                            except ValueError:
                                print("Invalid bitmask for boolean property:", properties[p]["description"])
                        elif len(desc_parts) == 3:
                            #single channel mode, read the next two values as off and on values
                            try:
                                off_value = int(desc_parts[1])
                                on_value = int(desc_parts[2])
                                set_channel_value(finalChannel, on_value if value else off_value)
                            except ValueError:
                                print("Invalid off/on values for boolean property:", properties[p]["description"])
                        else:
                            print("Invalid description for boolean property:", properties[p]["description"])
                    elif typ == idprop.types.IDPropertyArray:
                        #print(value.typecode)
                        dmx = getTupleAsDMX(value)
                        for i in range(len(dmx)):
                            set_channel_value(finalChannel + i, dmx[i])
                    #handle data blocks
                    #Text os executed as python code with finalChannel passed in
                    elif typ == bpy.types.Text:
                        #print("detected text")
                        #exec the text block as python
                        textblock: bpy.types.Text = value
                        globals_dict = {
                            #"__builtins__": None,
                            "finalChannel": finalChannel,      #pass in the channel index
                            "object": object,                  #pass along the object we are referencing
                            "object_properties": properties,   #pass along all properties on the object
                            "current_property": properties[p], #pass along the current property being referenced
                        }

                        exec(textblock.as_string(), globals_dict)
                    #objects are treated as directional pointers for pan/tilt
                    elif typ == bpy.types.Object:
                        dmx = get_angle_to_target_as_pan_tilt_DMX(object, value, properties[p])
                        for i in range(len(dmx)):
                            set_channel_value(finalChannel + i, dmx[i])

def get_angle_to_target_as_pan_tilt_DMX(object: bpy.types.Object, target_obj: bpy.types.Object, current_property: dict):
    #get world space position lol
    target_loc = target_obj.matrix_world.copy().translation
    object_matrix = object.matrix_world.copy()
    #rotate it 90 degrees on an axis to make it correct
    object_matrix = object_matrix @ mathutils.Matrix.Rotation(math.radians(-90), 4, 'Y')
    #we want to convert the targets world space location to object space
    target_loc = object_matrix.inverted() @ target_loc
    #direction = target_loc - object_loc
    direction = target_loc
    #calculate pan/tilt from direction vector
    direction.normalize()

    #print(rotation.to_euler())
    #pan is rotation around z axis
    #rounding to truncate float imprecisions (observed as high as e-6)
    pan = math.atan2(round(direction.y, 3), round(direction.x, 3))
    pan += math.radians(180) #adjustment required
    #tilt is rotation around x axis
    tilt = math.asin(round(direction.z, 3))
    #wrap both around 360
    pan = pan % math.radians(360)
    tilt = tilt % math.radians(360)
    #read the next two numbers from the description as pan and tilt ranges
    desc_parts = current_property["description"].split(" ")
    pan_range = 540
    tilt_range = 540
    if len(desc_parts) >= 3:
        try:
            pan_range = int(desc_parts[1])
            tilt_range = int(desc_parts[2])
        except ValueError:
            pass
    return getPanTiltAsDMX(math.degrees(pan), math.degrees(tilt), pan_range, tilt_range, bytesPerAxis=2)

def update_custom_properties(scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph):
    bad_obj_types = ['CAMERA','LAMP','ARMATURE']
    
    # Import here to avoid circular imports
    from bthl.operator.global_settings_modal import GlobalSettingsToggleModal
    from bthl.operator.customproperties_modal import CustomPropertiesToggleModal
    
    # Get toggle states from scene properties
    debug_enabled = GlobalSettingsToggleModal.get_debug_enabled(bpy.context)
    serialize_invisible = CustomPropertiesToggleModal.get_serialize_invisible(bpy.context)
    
    if debug_enabled:
        print("UPDATING DMX PROPERTIES")
    
    for obj in bpy.data.objects:
        if obj.type in bad_obj_types:
            continue

        #skip if in library
        if obj.library is not None:
            continue
        
        # Skip invisible objects if toggle is disabled
        if not serialize_invisible and not obj.visible_get():
            if debug_enabled:
                print(f"Skipping invisible object: {obj.name}")
            continue
        
        handleobjectproperties(obj)

class CustomPropertiesTask(Task):
    functions = {
        HandlerType.DEPSGRAPH_UPDATE_POST: update_custom_properties,
        HandlerType.FRAME_CHANGE_POST: update_custom_properties,
        HandlerType.LOAD_POST: update_custom_properties
    }
