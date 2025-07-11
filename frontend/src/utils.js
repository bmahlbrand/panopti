export function downloadFileFromBase64(filename, base64Data) {
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray]);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'download.bin';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

export function cameraData(camera, controls) {
    // Grabs relevant data from scene camera:
    const camData = {
        position: camera.position.toArray(),
        rotation: camera.rotation.toArray().slice(0,3), // Remove order parameter
        quaternion: camera.quaternion.toArray(),
        up: camera.up.toArray(),
        projection_mode: camera.isOrthographicCamera ? 'orthographic' : 'perspective',
        fov: camera.fov,
        near: camera.near,
        far: camera.far,
        aspect: camera.aspect,
        target: controls ? controls.target.toArray() : undefined
    };
    return camData;
}

export const debounce = (func, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func(...args);
        }, delay);
    };
};

export const throttle = (fn, delay) => {
    let last = 0;
    return (...args) => {
      const now = Date.now();
      if (now - last >= delay) {
        last = now;
        fn(...args);
      }
    };
  };

export function colorListToDict(colorList, type='rgb') {
    if (type === 'hsv') {
        return { h: colorList[0], s: colorList[1], v: colorList[2], a: colorList.length === 4 ? colorList[3] : 1 };
    }
    if (type === 'rgb') {
        return { r: colorList[0], g: colorList[1], b: colorList[2], a: colorList.length === 4 ? colorList[3] : 1 };
    }
    console.warn('Unexpected color type:', colorList, type);
}

export function colorDictToList(colorDict) {
    // Convert a dict {r, g, b, a} to a list [r, g, b, a]
    return [colorDict.r, colorDict.g, colorDict.b, colorDict.a !== undefined ? colorDict.a : 1];
}

export function pythonRGBAToJS(rgba) {
    // Python operates in [0,1] range, convert to [0,255] range for RGB components

    if (Array.isArray(rgba)) { // Array case
        return { r: rgba[0]*255, g: rgba[1]*255, b: rgba[2]*255, a: rgba.length === 4 ? rgba[3] : 1 };
    }
    
    if (rgba && typeof rgba === 'object') { // Dict case
        return {
            r: rgba.r * 255,
            g: rgba.g * 255,
            b: rgba.b * 255,
            a: rgba.a !== undefined ? rgba.a : 1
        };
    }

    console.warn('Unexpected color format:', rgba);
    return { r: 255, g: 0, b: 0, a: 1 }; // Default to bright red for error
}

/**
 * Wraps an animation loop function so it can be executed at a specific frame-rate
 * loop {Function}  = The function you want to execute each frames
 * fps {Number}     = The desired frame rate
 * source : https://woodenraft.games/blog/how-to-implement-consistent-frame-rate-threejs
 */
export function createFpsCap(loop, fps = 60) {
    console.log('createFpsCap', fps);
    let targetFps = 0, fpsInterval = 0;
    let lastTime = 0, lastOverTime = 0, prevOverTime = 0, deltaTime = 0;
  
    function updateFps(value) {
      targetFps = value;
      fpsInterval = 1000 / targetFps;
    }
  
    updateFps(fps);
  
    return {
      // the targeted frame rate
      get fps() {
        return targetFps;
      },
      set fps(value) {
        updateFps(value);
      },
  
      // the frame-capped loop function
      loop: function(time) {
        deltaTime = time - lastTime;
  
        if(deltaTime < fpsInterval) {
          return;
        }
  
        prevOverTime = lastOverTime;
        lastOverTime = deltaTime % fpsInterval;
        lastTime = time - lastOverTime;
  
        deltaTime -= prevOverTime;
  
        return loop(deltaTime);
      },
    };
  }