import voluptuous as vol
from homeassistant.components.light import (
    LightEntity, PLATFORM_SCHEMA, ColorMode, LightEntityFeature,
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_RGB_COLOR, ATTR_XY_COLOR, ATTR_HS_COLOR, ATTR_RGBW_COLOR, ATTR_RGBWW_COLOR, ATTR_COLOR_TEMP_KELVIN, ATTR_EFFECT_LIST, ATTR_EFFECT
)
from homeassistant.const import CONF_NAME, STATE_ON, CONF_ENTITY_ID, EVENT_HOMEASSISTANT_START
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
        self._is_on = None
        self._attr_unique_id = entity_id if entity_id else f"{onoff_entity}_{feature_entity}_dual"
        self.entity_id = self._attr_unique_id
        self._capabilities_configured = False
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_color_mode = ColorMode.ONOFF
        self._min_color_temp_kelvin = None
        self._max_color_temp_kelvin = None
        self._attr_supported_features = 0

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        _LOGGER.debug(f"{self.entity_id}: async_added_to_hass - START")

        # Add listeners
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._onoff_entity, self._feature_entity], self._async_state_changed
            )
        )

        self._update_capabilities()

        # Set initial state
        self._update_state()

        _LOGGER.debug(f"{self.entity_id}: async_added_to_hass - DONE")

    def _update_capabilities(self) -> None:
        """Update the entity's capabilities based on the brightness entity."""
        if self._capabilities_configured:
            return

        feature_entity_state = self.hass.states.get(self._feature_entity)
        if feature_entity_state:
            supported_color_modes = feature_entity_state.attributes.get('supported_color_modes', ColorMode.ONOFF)
            self._attr_supported_color_modes = set(supported_color_modes)

            supported_features = feature_entity_state.attributes.get('supported_features', 0)
            self._attr_supported_features = supported_features

            if ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
                self._min_color_temp_kelvin = feature_entity_state.attributes.get('min_color_temp_kelvin')
                self._max_color_temp_kelvin = feature_entity_state.attributes.get('max_color_temp_kelvin')

            self._capabilities_configured = True

            _LOGGER.debug(f"{self.entity_id}: _update_capabilities - "
                          f"Color modes: {', '.join(self._attr_supported_color_modes)}, "
                          f"Supported features: {self._attr_supported_features}, "
                          f"Min Color Temperature: {self._min_color_temp_kelvin}, "
                          f"Max Color Temperature: {self._max_color_temp_kelvin}")

    @callback
    def _async_state_changed(self, event) -> None:
        _LOGGER.debug(f"{self.entity_id}: _async_state_changed - {event}")
        self._update_capabilities()

        """Handle child updates."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self) -> None:
        """Update the state of this light."""
        onoff_state = self.hass.states.get(self._onoff_entity)
        feature_entity_state = self.hass.states.get(self._feature_entity)
        _LOGGER.debug(f"{self.entity_id}: _update_state - START")

        if onoff_state is not None and feature_entity_state is not None:
            self._is_on = onoff_state.state == STATE_ON and feature_entity_state.state == STATE_ON

            self._update_attributes(feature_entity_state)

            # Log the current state
            _LOGGER.debug(f"{self.entity_id}: _update_state - "
                          f"_is_on: {self._is_on}, "
                          f"feature_entity_state: {feature_entity_state}")

    @property
    def supported_color_modes(self) -> set[ColorMode]|None:
        """Return the list of supported color modes."""
        return self._attr_supported_color_modes

    @property
    def color_mode(self) -> ColorMode | None:
        """Return the current color mode."""
        return self._attr_color_mode

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the color temperature in Kelvin."""
        if ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_COLOR_TEMP_KELVIN)
        return None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the RGB color."""
        if ColorMode.RGB in self._attr_supported_color_modes :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_RGB_COLOR)
        return None

    @property
    def xy_color(self) -> tuple[float, float] | None:
        """Return the XY color."""
        if ColorMode.XY in self._attr_supported_color_modes :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_XY_COLOR)
        return None

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the HS color."""
        if ColorMode.HS in self._attr_supported_color_modes :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_HS_COLOR)
        return None

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the RGBW color."""
        if ColorMode.RGBW in self._attr_supported_color_modes :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_RGBW_COLOR)
        return None

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return the RGBWW color."""
        if ColorMode.RGBWW in self._attr_supported_color_modes :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_RGBWW_COLOR)
        return None

    @property
    def effect_list(self) -> list[str] | None:
        """Return effect list"""
        if self._attr_supported_features & LightEntityFeature.EFFECT :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_EFFECT_LIST)
        return None

    @property
    def effect(self) -> str | None:
        """Return current effect"""
        if self._attr_supported_features & LightEntityFeature.EFFECT :
            state = self.hass.states.get(self._feature_entity)
            return state.attributes.get(ATTR_EFFECT)
        return None

    @property
    def min_color_temp_kelvin(self) -> int | None:
        """Return the minimum color temperature in Kelvin."""
        return self._min_color_temp_kelvin

    @property
    def max_color_temp_kelvin(self) -> int | None:
        """Return the maximum color temperature in Kelvin."""
        return self._max_color_temp_kelvin

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_on(self) -> bool | None:
        return self._is_on

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

        _LOGGER.debug(f"{self.entity_id}: async_turn_on - {brightness_data}")

    async def async_turn_off(self, **kwargs) -> None:
        _LOGGER.debug(f"{self.entity_id}: async_turn_off - {kwargs}")
        await self.hass.services.async_call('light', 'turn_off', {'entity_id': self._onoff_entity})
        _LOGGER.debug(f"{self.entity_id}: async_turn_off - DONE")

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        _LOGGER.debug(f"{self.entity_id}: async_update")

        if self._capabilities_configured:
            onoff_entity_state = self.hass.states.get(self._onoff_entity)
            feature_entity_state = self.hass.states.get(self._feature_entity)

            _LOGGER.debug(f"{self.entity_id}: async_update - "
                          f"is_on: {self._is_on}, "
                          f"OnOff entity state: {onoff_entity_state}, "
                          f"Feature entity state: {feature_entity_state}")

            if onoff_entity_state and feature_entity_state:
                self._update_attributes(feature_entity_state)

    def _update_attributes(self, feature_entity_state) -> None:
        # color mode is only updated when the light is ON
        if feature_entity_state.state == STATE_ON:
            self._attr_color_mode = feature_entity_state.attributes.get('color_mode', ColorMode.ONOFF)
            _LOGGER.debug(f"{self.entity_id}: _update_attributes - {self._attr_color_mode}")

