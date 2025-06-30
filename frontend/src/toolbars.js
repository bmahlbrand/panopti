import React from 'react';

export function changeBackgroundColor(sceneManagerRef, setBackgroundColor, color) {
    setBackgroundColor(color);
    if (sceneManagerRef.current) {
        sceneManagerRef.current.setBackgroundColor(color);
    }
}

export function resetCamera(sceneManagerRef) {
    if (sceneManagerRef.current) {
        sceneManagerRef.current.resetCamera();
    }
}

export function toggleRenderSetting(sceneManagerRef, setRenderSettings, setting) {
    setRenderSettings(prev => {
        let newValue;
        if (setting === 'wireframe') {
            newValue = (prev[setting] + 1) % 3;
        } else {
            newValue = !prev[setting];
        }
        const newSettings = { ...prev, [setting]: newValue };
        if (sceneManagerRef.current) {
            sceneManagerRef.current.applyRenderSettings(newSettings);
        }
        return newSettings;
    });
}

export function updateLightSetting(sceneManagerRef, setLightSettings, setting, value) {
    setLightSettings(prev => {
        const newSettings = { ...prev, [setting]: value };
        if (sceneManagerRef.current) {
            sceneManagerRef.current.applyLightSettings(newSettings);
        }
        return newSettings;
    });
}

export function captureCurrentView(rendererRef, sceneManagerRef, setCapturedImage, setShowRenderModal) {
    if (!rendererRef.current) return;
    rendererRef.current.render(sceneManagerRef.current.scene, sceneManagerRef.current.camera);
    const dataURL = rendererRef.current.domElement.toDataURL('image/png');
    setCapturedImage(dataURL);
    setShowRenderModal(true);
}

export async function renderToClipboard(rendererRef, sceneManagerRef) {
    if (!rendererRef.current) return;
    try {
        rendererRef.current.render(sceneManagerRef.current.scene, sceneManagerRef.current.camera);
        rendererRef.current.domElement.toBlob(async (blob) => {
            if (blob && navigator.clipboard && navigator.clipboard.write) {
                const item = new ClipboardItem({ 'image/png': blob });
                await navigator.clipboard.write([item]);
            } else {
                console.warn('Clipboard API not supported');
            }
        }, 'image/png');
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
    }
}

export function saveImage(capturedImage, setShowRenderModal, setCapturedImage) {
    if (!capturedImage) return;
    const link = document.createElement('a');
    link.download = 'panopti-render.png';
    link.href = capturedImage;
    link.click();
    setShowRenderModal(false);
    setCapturedImage(null);
}

export function discardImage(setShowRenderModal, setCapturedImage) {
    setShowRenderModal(false);
    setCapturedImage(null);
}

export function renderSceneToolbar({ resetCamera, toggleBackgroundColor, refreshState, restartScript, toggleConsole, isDark }) {
    return React.createElement(
        'div',
        { className: 'scene-toolbar' },
        React.createElement(
            'button',
            { className: 'toolbar-button tooltip', 'data-tooltip': 'Reset Camera', onClick: resetCamera },
            React.createElement('i', { className: 'fa-solid fa-camera-rotate' })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': isDark ? 'Light Background' : 'Dark Background',
                onClick: toggleBackgroundColor
            },
            React.createElement('i', { className: isDark ? 'fas fa-sun' : 'fas fa-moon' })
        ),
        React.createElement(
            'button',
            { className: 'toolbar-button tooltip', 'data-tooltip': 'Refresh Scene', onClick: refreshState },
            React.createElement('i', { className: ' mdi mdi-cloud-sync', style: { fontSize: '20px' } })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Restart Script',
                onClick: restartScript,
                disabled: false
            },
            React.createElement('i', { className: 'fas fa-sync-alt' }),
        ),
        React.createElement(
            'button',
            { className: 'toolbar-button tooltip', 'data-tooltip': 'Show Console', onClick: toggleConsole },
            React.createElement('i', { className: 'fas fa-terminal' })
        )
    );
}

export function renderRenderToolbar(renderSettings, toggleRenderSetting, captureCurrentView, renderToClipboard) {
    return React.createElement(
        'div',
        { className: 'render-toolbar' },
        React.createElement(
            'button',
            {
                className: `toolbar-button tooltip ${renderSettings.wireframe > 0 ? 'active' : ''}`,
                'data-tooltip': renderSettings.wireframe === 0 ? 'Normal Mode' :
                       renderSettings.wireframe === 1 ? 'Wireframe with Geometry' : 'Pure Wireframe',
                onClick: () => toggleRenderSetting('wireframe')
            },
            React.createElement('i', {
                className: renderSettings.wireframe === 0 ? 'fas fa-cube' :
                          renderSettings.wireframe === 1 ? 'fas fa-layer-group' : 'fas fa-vector-square'
            })
        ),
        React.createElement(
            'button',
            {
                className: `toolbar-button tooltip ${renderSettings.flatShading ? 'active' : ''}`,
                'data-tooltip': 'Toggle Flat/Smooth Shading',
                onClick: () => toggleRenderSetting('flatShading')
            },
            React.createElement('i', { className: 'fas fa-square' })
        ),
        React.createElement(
            'button',
            {
                className: `toolbar-button tooltip ${renderSettings.showNormals ? 'active' : ''}`,
                'data-tooltip': 'Toggle Normals',
                onClick: () => toggleRenderSetting('showNormals')
            },
            React.createElement('i', { className: 'fas fa-arrows-alt' })
        ),
        React.createElement(
            'button',
            {
                className: `toolbar-button tooltip ${renderSettings.showGrid ? 'active' : ''}`,
                'data-tooltip': 'Toggle Grid',
                onClick: () => toggleRenderSetting('showGrid')
            },
            React.createElement('i', { className: 'fas fa-border-all' })
        ),
        React.createElement(
            'button',
            {
                className: `toolbar-button tooltip ${renderSettings.showAxes ? 'active' : ''}`,
                'data-tooltip': 'Toggle Axes',
                onClick: () => toggleRenderSetting('showAxes')
            },
            React.createElement('i', { className: 'fas fa-compass' })
        ),
        React.createElement(
            'button',
            {
                className: `toolbar-button tooltip ${renderSettings.inspectMode ? 'active' : ''}`,
                'data-tooltip': 'Inspect Vertices/Faces',
                onClick: () => toggleRenderSetting('inspectMode')
            },
            React.createElement('i', { className: 'fas fa-search' })
        ),
        React.createElement(
            'button',
            { className: 'toolbar-button tooltip', 'data-tooltip': 'Render View (with Save Dialog)', onClick: captureCurrentView },
            React.createElement('i', { className: 'fas fa-camera' })
        ),
        React.createElement(
            'button',
            { className: 'toolbar-button tooltip', 'data-tooltip': 'Render to Clipboard', onClick: renderToClipboard },
            React.createElement('i', { className: 'fas fa-clipboard' })
        )
    );
}

export function renderLightingToolbar(lightSettings, updateLightSetting) {
    const openColorPicker = (setting, currentColor) => {
        const input = document.createElement('input');
        input.type = 'color';
        input.value = currentColor;
        input.addEventListener('input', (e) => {
            updateLightSetting(setting, e.target.value);
        });
        input.click();
    };
    return React.createElement(
        'div',
        { className: 'lighting-toolbar' },
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Ambient Light Color',
                onClick: () => openColorPicker('ambientColor', lightSettings.ambientColor),
                style: { backgroundColor: lightSettings.ambientColor }
            },
            React.createElement('i', { className: 'fas fa-lightbulb' })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Decrease Ambient Light',
                onClick: () => updateLightSetting('ambientIntensity', Math.max(0.1, lightSettings.ambientIntensity - 0.5))
            },
            React.createElement('i', { className: 'fas fa-minus' })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Increase Ambient Light',
                onClick: () => updateLightSetting('ambientIntensity', Math.min(5.0, lightSettings.ambientIntensity + 0.5))
            },
            React.createElement('i', { className: 'fas fa-plus' })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Directional Light Color',
                onClick: () => openColorPicker('directionalColor', lightSettings.directionalColor),
                style: { backgroundColor: lightSettings.directionalColor }
            },
            React.createElement('i', { className: 'fas fa-sun' })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Decrease Directional Light',
                onClick: () => updateLightSetting('directionalIntensity', Math.max(0.1, lightSettings.directionalIntensity - 0.5))
            },
            React.createElement('i', { className: 'fas fa-minus' })
        ),
        React.createElement(
            'button',
            {
                className: 'toolbar-button tooltip',
                'data-tooltip': 'Increase Directional Light',
                onClick: () => updateLightSetting('directionalIntensity', Math.min(5.0, lightSettings.directionalIntensity + 0.5))
            },
            React.createElement('i', { className: 'fas fa-plus' })
        )
    );
}
