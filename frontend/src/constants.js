// CONSTANTS: 

// debounce timers in milliseconds:
export let DEBOUNCE_SLIDER = 25;
export let DEBOUNCE_TRANSFORM = 25;
export let DEBOUNCE_CAMERA = 500;

export function setConstantsFromConfig(config) {
    if (config === undefined) return;
    DEBOUNCE_SLIDER = config.viewer.debounce.slider;
    DEBOUNCE_TRANSFORM = config.viewer.debounce.transform;
    DEBOUNCE_CAMERA = config.viewer.debounce.camera;
}