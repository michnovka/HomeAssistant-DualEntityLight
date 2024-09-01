# Home Assistant Dual entity custom component

This integration is useful when you have a smart light such as Philips Hue 
mounted behind a ON/OFF switch (such as KNX or Bticino). You can then configure the
entity to turn on/off using the wall switch, whilst all effects, brightness,
color modes and color temperatures are done through the smart light

## Installation

Copy the `custom_components/dual_light_entity` directory into your HA config folder

## Configuration

The lights have to be configured using yaml:

```yaml
light:
  - platform: dual_entity_light
    name: <User friendly name of the light>
    onoff_entity: <entity ID of the ON/OFF switch>
    feature_entity: <entity ID of the smart light>
    entity_id: <entity ID of the newly created dual light entity>
```

For example:

```yaml
light:
  - platform: dual_entity_light
    name: Office Light
    onoff_entity: light.knx_office_switch
    feature_entity: light.philips_hue_office
    entity_id: light.office_combined
```