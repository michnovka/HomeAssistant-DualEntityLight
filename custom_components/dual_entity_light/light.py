import voluptuous as vol
from homeassistant.components.light import (
    LightEntity, PLATFORM_SCHEMA, ColorMode, LightEntityFeature,
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_RGB_COLOR, ATTR_XY_COLOR, ATTR_HS_COLOR, ATTR_RGBW_COLOR, ATTR_RGBWW_COLOR, ATTR_COLOR_TEMP_KELVIN, ATTR_EFFECT_LIST, ATTR_EFFECT, ATTR_COLOR_MODE
)
from homeassistant.const import CONF_NAME, STATE_ON, STATE_OFF, CONF_ENTITY_ID, EVENT_HOMEASSISTANT_START
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import callback
import logging

_LOGGER = logging.getLogger(__name__)

CONF_ONOFF_ENTITY = "onoff_entity"
CONF_feature_entity = "feature_entity"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Required(CONF_ONOFF_ENTITY): cv.entity_id,
    vol.Required(CONF_feature_entity): cv.entity_id,
    vol.Optional(CONF_ENTITY_ID): cv.entity_id,
})

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Set up the Dual Entity light."""
    async def setup_light(_) -> None:
        """Set up the light after Home Assistant has started."""
        light = DualEntityLight(
            config[CONF_NAME],
            config[CONF_ONOFF_ENTITY],
            config[CONF_feature_entity],
            config.get(CONF_ENTITY_ID)
        )

        async_add_entities([light])
        _LOGGER.debug(f"Dual Entity Light '{config[CONF_NAME]}' has been initialized")

    # Defer setup until Home Assistant is fully started
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, setup_light)

class DualEntityLight(LightEntity):
    def __init__(self, name, onoff_entity, feature_entity, entity_id=None):
        self._name = name
        self._onoff_entity = onoff_entity
        self._feature_entity = feature_entity
        self._attr_unique_id = entity_id if entity_id else f"{onoff_entity}_{feature_entity}_dual"
        self.entity_id = self._attr_unique_id

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        # Add listeners
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._onoff_entity, self._feature_entity], self._async_state_changed
            )
        )

        _LOGGER.debug(f"{self.entity_id}: async_added_to_hass - DONE")


    @callback
    def _async_state_changed(self, event) -> None:
        _LOGGER.debug(f"{self.entity_id}: _async_state_changed - {event}")
        self.async_write_ha_state()

    @property
    def supported_color_modes(self) -> set[ColorMode]|None:
        """Return the list of supported color modes."""

        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state is not None:
            feature_entity_supported_color_modes = feature_entity_state.attributes.get('supported_color_modes')
            return set(feature_entity_supported_color_modes)
        return None

    @property
    def supported_features(self) -> int|None:
        """Return the list of supported features."""

        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state is not None:
            return feature_entity_state.attributes.get('supported_features')
        return None

    @property
    def color_mode(self) -> ColorMode | None:
        """Return the current color mode."""
        feature_entity_state = self.hass.states.get(self._feature_entity)
        feature_entity_color_mode = feature_entity_state.attributes.get(ATTR_COLOR_MODE)

        # This can be empty for now, so in such case we should pick any value from the supported list
        if feature_entity_color_mode is None:
            feature_entity_supported_color_modes = self.supported_color_modes
            feature_entity_color_mode = feature_entity_supported_color_modes.pop() if feature_entity_supported_color_modes else None
        return feature_entity_color_mode

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature in Kelvin."""
        return self._xxx_color(ColorMode.COLOR_TEMP, ATTR_COLOR_TEMP_KELVIN)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color."""
        return self._xxx_color(ColorMode.RGB, ATTR_RGB_COLOR)


    @property
    def xy_color(self) -> tuple[float, float] | None:
        """Return the XY color."""
        return self._xxx_color(ColorMode.XY, ATTR_XY_COLOR)


    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the HS color."""
        return self._xxx_color(ColorMode.HS, ATTR_HS_COLOR)


    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the RGBW color."""
        return self._xxx_color(ColorMode.RGBW, ATTR_RGBW_COLOR)


    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return the RGBWW color."""
        return self._xxx_color(ColorMode.RGBWW, ATTR_RGBWW_COLOR)

    def _xxx_color(self, color_mode, color_attribute):
        if color_mode in self.supported_color_modes :
            feature_entity_state = self.hass.states.get(self._feature_entity)
            return feature_entity_state.attributes.get(color_attribute)
        return None


    @property
    def effect_list(self) -> list[str] | None:
        """Return effect list"""

        feature_entity_state = self.hass.states.get(self._feature_entity)
        _LOGGER.debug(f"{self.entity_id}: effect_list - "
                      f"is_on: {feature_entity_state}, ")
        if feature_entity_state.attributes.get('supported_features') & LightEntityFeature.EFFECT:
            return feature_entity_state.attributes.get(ATTR_EFFECT_LIST)
        return None

    @property
    def effect(self) -> str | None:
        """Return current effect"""
        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state.attributes.get('supported_features') & LightEntityFeature.EFFECT:
            return feature_entity_state.attributes.get(ATTR_EFFECT)
        return None

    @property
    def min_color_temp_kelvin(self) -> int | None:
        """Return the minimum color temperature in Kelvin."""
        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state:
            return feature_entity_state.attributes.get('min_color_temp_kelvin')
        return None

    @property
    def max_color_temp_kelvin(self) -> int | None:
        """Return the maximum color temperature in Kelvin."""
        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state:
            return feature_entity_state.attributes.get('max_color_temp_kelvin')
        return None

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool | None:
        on_off_entity_state = self.hass.states.get(self._onoff_entity)
        feature_entity_state = self.hass.states.get(self._feature_entity)
        if on_off_entity_state and feature_entity_state:
            return on_off_entity_state.state == STATE_ON and feature_entity_state.state != STATE_OFF
        return None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light."""
        brightness = None
        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state is not None:
            if feature_entity_state.state == STATE_ON:
                brightness = feature_entity_state.attributes.get(ATTR_BRIGHTNESS)

        _LOGGER.debug(f"{self.entity_id}: brightness - {brightness}")
        return brightness

    async def async_turn_on(self, **kwargs) -> None:
        _LOGGER.debug(f"{self.entity_id}: async_turn_on - START")

        await self.hass.services.async_call('light', 'turn_on', {'entity_id': self._onoff_entity})

        # Prepare data for brightness entity
        brightness_data = {'entity_id': self._feature_entity}

        # Handle color temperature
        if 'color_temp_kelvin' in kwargs:
            brightness_data['color_temp_kelvin'] = kwargs['color_temp_kelvin']
        elif 'color_temp' in kwargs:
            brightness_data['color_temp'] = kwargs['color_temp']

        # Add all other kwargs to brightness_data, except 'entity_id' and color temp keys
        excluded_keys = {'entity_id', 'color_temp', 'color_temp_kelvin'}
        brightness_data.update({k: v for k, v in kwargs.items() if k not in excluded_keys})

        # Only call the service if we have data to set
        if len(brightness_data) > 1:  # More than just the entity_id
            await self.hass.services.async_call('light', 'turn_on', brightness_data)

        _LOGGER.info(f"{self.entity_id}: Turned on - {brightness_data}")

    async def async_turn_off(self, **kwargs) -> None:
        _LOGGER.debug(f"{self.entity_id}: async_turn_off - {kwargs}")
        await self.hass.services.async_call('light', 'turn_off', {'entity_id': self._onoff_entity})
        _LOGGER.info(f"{self.entity_id}: Turned off")

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        on_off_entity_state = self.hass.states.get(self._onoff_entity)
        feature_entity_state = self.hass.states.get(self._feature_entity)

        _LOGGER.debug(f"{self.entity_id}: async_update - "
                      f"is_on: {self.is_on}, "
                      f"OnOff entity state: {on_off_entity_state}, "
                      f"Feature entity state: {feature_entity_state}")
