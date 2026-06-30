# Blender DMX Connector

A Blender addon that enables real-time DMX lighting control through Art-Net protocol. Generate and send Art-Net packets for light programming, sync object properties to DMX channels, and receive MIDI timecode data from [HNode](https://github.com/Happyrobot33/HNode).

## Installation

1. Download the addon folder containing this plugin
2. In Blender, go to **Edit → Preferences → Add-ons**
3. Click **Install** and select the addon folder
4. Search for "DMX Connector" and enable it
5. A new **DMX Connector** panel will appear in the 3D View sidebar (press `N` to toggle)

**Requirements**: Blender 4.5 or later

## Getting Started

### 1. Set Up DMX Properties on Objects

Before you can send DMX data, your objects need DMX custom properties:

1. Select an object in the 3D viewport
2. In the **DMX Connector** panel, find the **Custom Properties** section
3. Click **Add DMX Properties** to add the base properties:
   - **Universe**: Which DMX universe to use (1-256)
   - **Channel**: Starting DMX channel (1-512)

### 2. Create Custom Properties

After adding base DMX properties, you can add custom properties to control specific lighting parameters:

1. In the object's properties panel, go to **Object Properties** → **Custom Properties**
2. Click **Add** to create a new property
3. Set the property name (e.g., `intensity`, `color`, `pan_position`)
4. Set the base channel offset for this property in the description field. For example, the first channel of a fixture would be 0
   1. There is additional settings that can be controlled using the description field based on the property type below
5. Select a property type from the dropdown:
    - **Float**: For continuous values (e.g., intensity, pan/tilt)
      - For pan/tilt or other angle fields, set the subtype to **Angle** to automatically convert degrees to DMX values. Keep in mind the min/max fields will be in radians, not degrees
      - For 16bit values, the description can be used to enable 16bit mode. For example, if the description is `0 1`, it will use channel 0 for the coarse value and channel 1 for the fine value
    - **Float Array**: For multi-channel values (e.g., RGB color)
      - Each element in the array corresponds to a DMX channel offset from the base channel defined in the description
      - For color, set the length to 3. Under the subtype field, set to either linear, or gamma corrected color. Most common uses with be with linear color.
    - **Integer**: For discrete values (e.g., gobos modes)
    - **Boolean**: For on/off states (e.g., light enabled)
      - By default, booleans will serialize as 0 when off or 255 when on. This can be configured using the description
        - **Bitmask**: If the description contains a number, it will be treated as a bitmask for the channel. For example, if the description is `0 3`, it will set or clear bit 3 of channel 0 based on the boolean value
        - **Custom Values**: If the description contains two numbers, it will use those as the values for off and on states. For example, if the description is `0 100 200`, it will set channel 0 to 100 when off and 200 when on

### 3. Configure UDP Client Settings

1. In the **DMX Connector** panel, locate **UDP Client Settings**
2. Set **Target IP**: The IP address of your DMX gateway/console (e.g., `127.0.0.1` for local nodes)
3. Set **Port**: The port your DMX system listens on (typically `6454` for Art-Net)
4. Set **Universe Offset**: Adds an offset to universes that are sent (usually keep `0`)

### 4. Start Sending DMX Data

**Manual Send**:
- Click the **Toggle UDP Client** button to connect/disconnect

**Auto-Send Mode**:
1. Enable **Auto Send**
2. Set the **Interval** (in seconds) for how often to update DMX data
3. When enabled, all properties automatically send to the DMX gateway on this interval. This is useful if your feeding into another lighting console such as MA or QLC+

### 5. Working with Multiple Objects

#### Copy Properties to Selected Objects

To apply the same DMX configuration to multiple objects:

1. Select a "source" object with configured DMX properties
2. Hold Shift and select additional target objects
3. Right-click on the source objects custom property and select **Copy DMX Property to Selected**
4. All selected objects now share the same DMX property

#### Sync Properties Across Selected Objects

Enable **Sync Active to Selected** to have property changes on the active object automatically update all selected objects. This is useful for batch controlling multiple lights dimmers or colors.

## Global Settings

### Invisible Object Serialization

**Serialize Invisible Objects**: Controls whether objects hidden from the viewport contribute to DMX output. Useful for having different "scenes" or "modes" defined in the same blender file

## MIDI Timecode Support

Sync Blender's timeline with external timecode sources (requires [HNode](https://github.com/Happyrobot33/HNode)):

1. Set up HNode with MIDI timecode plugin in the exporters tab
2. In the **MIDI Timecode Settings** section, enable **Receive MIDI Timecode**
3. Set the **Timecode Port** to match your HNode configuration (default: typically `10001`)
4. The panel displays the last received timecode frame
5. Blender's timeline will automatically sync to incoming MTC timecode

## Tips & Tricks

### Quick Property Duplication
- Select an object with DMX properties
- Right-click and select **Duplicate DMX Property** to quickly copy a single property on the same object
