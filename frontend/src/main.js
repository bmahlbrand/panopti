// panopti/server/static/js/main.js
import { Buffer } from 'buffer';
// @ts-ignore
window.Buffer = Buffer;
import React from 'react';
import ReactDOM from 'react-dom';
import { marked } from 'marked';
import { initComms } from './comms.js'; 
import Plotly from 'plotly.js';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { ChromePicker } from '@uiw/react-color';

import { downloadFileFromBase64, cameraData, debounce } from './utils.js';
import { createSceneManager } from './sceneManager.js';
import { initTooltips } from './tooltip.js';
import {
    handleSliderChange as uiHandleSliderChange,
    handleSliderInputCommit as uiHandleSliderInputCommit,
    handleSliderArrow as uiHandleSliderArrow,
    handleButtonClick as uiHandleButtonClick,
    handleCheckboxChange as uiHandleCheckboxChange,
    handleDropdownChange as uiHandleDropdownChange,
    handleColorChange as uiHandleColorChange,
    renderControl as renderUIControl
} from './uiControls.js';
import {
    changeBackgroundColor as bgColor,
    resetCamera as resetCam,
    toggleRenderSetting as toggleSetting,
    updateLightSetting as updateLight,
    captureCurrentView as captureView,
    renderToClipboard as copyToClipboard,
    saveImage as saveImg,
    discardImage as discardImg,
    renderSceneToolbar as sceneToolbar,
    renderRenderToolbar as renderToolbar,
    renderLightingToolbar as lightingToolbar
} from './toolbars.js';
import {
    exportObject as exportObj,
    toggleObjectVisibility as toggleVisibility,
    toggleAnimatedMeshPlayback as togglePlayback,
    renderLayersPanel as layersPanel
} from './layersPanel.js';

// const marked = window.marked;
// console.log('Socket.io initialized:', io);
'use strict';

const App = () => {
    const [controls, setControls] = React.useState([]);
    const [isPanelCollapsed, setIsPanelCollapsed] = React.useState(false);
    const [isLoading, setIsLoading] = React.useState(true);
    const [backgroundColor, setBackgroundColor] = React.useState('#f0f0f0');
    const [selectedObject, setSelectedObject] = React.useState(null);
    const [sceneObjects, setSceneObjects] = React.useState([]);
    const [renderSettings, setRenderSettings] = React.useState({
        wireframe: false,
        flatShading: false,
        showNormals: false,
        showGrid: true,
        showAxes: true,
        inspectMode: false
    });
    const [lightSettings, setLightSettings] = React.useState({
        ambientColor: '#ffffff',
        ambientIntensity: 0.5,
        directionalColor: '#ffffff',
        directionalIntensity: 0.7
    });
    const [showRenderModal, setShowRenderModal] = React.useState(false);
    const [capturedImage, setCapturedImage] = React.useState(null);
    const [transformState, setTransformState] = React.useState({
            position: [0, 0, 0],
            rotation: [0, 0, 0],
            scale: [1, 1, 1],
            lockScale: false
        });
    const transformStateRef = React.useRef(transformState);

    const [consoleLines, setConsoleLines] = React.useState([]);
    const [showConsole, setShowConsole] = React.useState(false);
    const [consolePos, setConsolePos] = React.useState({ x: 50, y: 50 });
    const consoleRef = React.useRef(null);
    const dragRef = React.useRef(null);
    
    const sceneRef = React.useRef(null);
    const rendererRef = React.useRef(null);
    const sceneManagerRef = React.useRef(null);
    const socketRef = React.useRef(null);

    React.useEffect(() => {
        if (selectedObject && selectedObject.data && selectedObject.data.position) {
            const newState = {
                position: [...selectedObject.data.position],
                rotation: [...selectedObject.data.rotation],
                scale: [...selectedObject.data.scale],
                lockScale: false};
            setTransformState(newState);
            transformStateRef.current = newState;
        }
    }, [selectedObject]);
    
    React.useEffect(() => {
        const socket = initComms(sceneManagerRef, { setIsLoading, setControls, setConsoleLines });
        socketRef.current = socket;
        
        // Initialize Three.js
        const container = sceneRef.current;
        const { clientWidth, clientHeight } = container;
        
        // Create SceneManager
        const SceneManager = createSceneManager(
            container,
            socketRef.current,
            {
                onSelectObject: setSelectedObject,
                onSceneObjectsChange: updateSceneObjectsList
            },
            backgroundColor
        );
        sceneManagerRef.current = SceneManager;
        rendererRef.current = SceneManager.renderer;
        
        // Observe container resize using ResizeObserver
        const resizeObserver = new ResizeObserver(entries => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                SceneManager.onWindowResize(width, height);
            }
        });

        resizeObserver.observe(container);
        
        // Animation loop
        const animate = () => {
            requestAnimationFrame(animate);
            SceneManager.update();
        };
        
        animate();
        
        // Cleanup
        return () => {
            Object.values(debouncedSliderEmitRef.current).forEach(timeout => {
                clearTimeout(timeout);
            });
            
            resizeObserver.disconnect();
            socket.disconnect();
            if (sceneManagerRef.current) {
                sceneManagerRef.current.dispose();
            }
        };
    }, []);
    
    // Effect to resize the renderer when panel is collapsed/expanded
    React.useEffect(() => {
        // Force an immediate resize
        if (sceneManagerRef.current) {
            sceneManagerRef.current.onWindowResize();
        }
        
        // Add a small delay to let the CSS transition complete for a smoother experience
        const resizeTimeout = setTimeout(() => {
            if (sceneManagerRef.current) {
                sceneManagerRef.current.onWindowResize();
            }
        }, 310);
        
        return () => clearTimeout(resizeTimeout);
    }, [isPanelCollapsed]);
    
    React.useEffect(() => {
        if (sceneManagerRef.current) {
            sceneManagerRef.current.applyRenderSettings(renderSettings);
        }
    }, [renderSettings]);
    
    React.useEffect(() => {
        if (sceneManagerRef.current) {
            sceneManagerRef.current.applyLightSettings(lightSettings);
        }
    }, [lightSettings]);
    
    React.useEffect(() => {
        if (sceneManagerRef.current) {
            updateSceneObjectsList();
        }
    }, [sceneManagerRef.current]);

    React.useEffect(() => {
        if (showConsole && consoleRef.current) {
            consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
        }
    }, [consoleLines, showConsole]);

    React.useEffect(() => {
        setTimeout(() => {
            controls.forEach(c => {
                if (c.type === 'plotly') {
                    const el = document.getElementById(`plotly-${c.id}`);
                    if (el) {
                        console.log('Rendering Plotly:', el, c.spec);
                        Plotly.react(el, c.spec.data || [], c.spec.layout || {}, c.spec.config || {});
                    }
                }
            });
        }, 0);
    }, [controls]);
    
    const updateSceneObjectsList = () => {
        if (sceneManagerRef.current) {
            setSceneObjects(sceneManagerRef.current.getAllObjects());
        }
    };
    
    const debouncedSliderEmitRef = React.useRef({});

    const handleSliderChange = (id, value) =>
        uiHandleSliderChange(controls, socketRef, debouncedSliderEmitRef, id, value);
    const handleSliderInputCommit = (id, value) =>
        uiHandleSliderInputCommit(controls, socketRef, debouncedSliderEmitRef, id, value);
    const handleSliderArrow = (id, dir) =>
        uiHandleSliderArrow(controls, socketRef, debouncedSliderEmitRef, id, dir);
    const handleButtonClick = (id) => uiHandleButtonClick(socketRef, id);
    const handleCheckboxChange = (id, checked) =>
        uiHandleCheckboxChange(socketRef, id, checked);
    const handleDropdownChange = (id, value) =>
        uiHandleDropdownChange(socketRef, id, value);
    const handleColorChange = (id, value) =>
        uiHandleColorChange(socketRef, id, value);
    
    const togglePanelCollapse = () => {
        setIsPanelCollapsed(!isPanelCollapsed);
    };
    
    const changeBackgroundColor = (color) =>
        bgColor(sceneManagerRef, setBackgroundColor, color);

    const toggleBackgroundColor = () =>
        changeBackgroundColor(backgroundColor === '#2d3142' ? '#f0f0f0' : '#2d3142');

    const resetCamera = () => resetCam(sceneManagerRef);
    
    const refreshState = () => {
        
        // Clear existing objects and controls
        if (sceneManagerRef.current) {
            sceneManagerRef.current.clearAllObjects();
        }
        setControls([]);
        setSelectedObject(null);
        socketRef.current.emit('request_state', { viewer_id: window.viewerId });
    };

    const restartScript = () => {
        const payload = {};
        if (window.viewerId) payload.viewer_id = window.viewerId;
        socketRef.current.emit('restart_script', payload);
    };

    const applyTransforms = (updates) => {
        if (!sceneManagerRef.current || !selectedObject) return;
        sceneManagerRef.current.updateObject(selectedObject.data.id, updates);
        const payload = { id: selectedObject.data.id, updates };
        if (window.viewerId) payload.viewer_id = window.viewerId;
        socketRef.current.emit('update_object', payload);
    };

    const handleTransformCommit = (type, index, value) => {
        let num;
        try {
            if (typeof value === 'string' && value.trim() !== '') {
                num = math.evaluate(value);
            }
        } catch (err) {
            num = NaN;
        }
        if (typeof num !== 'number' || isNaN(num)) {
            num = transformState[type][index];
            console.warn(`Invalid input for ${type}[${index}]:`, value, 'Using previous value:', num);
        }

        let currentState = transformStateRef.current;
        let arr = [...currentState[type]];
        if (type === 'scale' && transformState.lockScale) {
            const ratio = num / arr[index];
            arr = arr.map(v => v * ratio);
        } else {
            arr[index] = num;
        }
        applyTransforms({ [type]: arr });
        const newState = { ...currentState, [type]: arr };
        setTransformState(newState);
        transformStateRef.current = newState;
    };

    const handleTransformArrow = (type, index, dir) => {
        const step = 0.1;
        let currentState = transformStateRef.current;
        let arr = [...currentState[type]];
        const prevVal = arr[index];
        const val = prevVal + dir * step;
        if (type === 'scale' && transformState.lockScale) {
            const ratio = val / prevVal;
            arr = arr.map(v => v * ratio);
        } else {
            arr[index] = prevVal + dir * step;
        }
        applyTransforms({ [type]: arr });
        const newState = { ...currentState, [type]: arr };
        setTransformState(newState);
        transformStateRef.current = newState;
    };

    const toggleScaleLock = () => {
        setTransformState(prev => ({ ...prev, lockScale: !prev.lockScale }));
    };

    const resetTransform = () => {
        const defaults = { position: [0,0,0], rotation: [0,0,0], scale: [1,1,1] };
        applyTransforms(defaults);
        const newState = { ...transformState, ...defaults };
        setTransformState(newState);
        transformStateRef.current = newState;
    };

    const toggleConsole = () => setShowConsole(prev => !prev);

    const handleConsoleMouseDown = (e) => {
        dragRef.current = { x: e.clientX, y: e.clientY, start: consolePos };
        document.addEventListener('mousemove', handleConsoleMouseMove);
        document.addEventListener('mouseup', handleConsoleMouseUp);
    };

    const handleConsoleMouseMove = (e) => {
        if (!dragRef.current) return;
        const dx = e.clientX - dragRef.current.x;
        const dy = e.clientY - dragRef.current.y;
        setConsolePos({ x: dragRef.current.start.x + dx, y: dragRef.current.start.y + dy });
    };

    const handleConsoleMouseUp = () => {
        dragRef.current = null;
        document.removeEventListener('mousemove', handleConsoleMouseMove);
        document.removeEventListener('mouseup', handleConsoleMouseUp);
    };
    
    const toggleRenderSetting = (setting) =>
        toggleSetting(sceneManagerRef, setRenderSettings, setting);

    const updateLightSetting = (setting, value) =>
        updateLight(sceneManagerRef, setLightSettings, setting, value);
    
    const exportObject = exportObj;

    // Toggle object visibility with 3 states: visible, semi-transparent, hidden
    const toggleObjectVisibility = (objectId) =>
        toggleVisibility(sceneManagerRef, sceneObjects, objectId, updateSceneObjectsList);

    // Toggle animated mesh playback
    const toggleAnimatedMeshPlayback = (objectId) =>
        togglePlayback(sceneManagerRef, objectId, updateSceneObjectsList);
    
    const renderControl = (control) =>
        renderUIControl(control, {
            handleSliderChange,
            handleSliderInputCommit,
            handleSliderArrow,
            handleButtonClick,
            handleCheckboxChange,
            handleDropdownChange,
            handleColorChange
        });
    
    // Render capture functions
    const captureCurrentView = () =>
        captureView(rendererRef, sceneManagerRef, setCapturedImage, setShowRenderModal);

    const renderToClipboard = () =>
        copyToClipboard(rendererRef, sceneManagerRef);

    const saveImage = () =>
        saveImg(capturedImage, setShowRenderModal, setCapturedImage);

    const discardImage = () =>
        discardImg(setShowRenderModal, setCapturedImage);
    
    // Create Scene Toolbar
    const renderSceneToolbar = () =>
        sceneToolbar({
            resetCamera,
            toggleBackgroundColor,
            refreshState,
            restartScript,
            toggleConsole,
            isDark: backgroundColor === '#2d3142',
        });
    
    // Create Render Toolbar
    const renderRenderToolbar = () =>
        renderToolbar(renderSettings, toggleRenderSetting, captureCurrentView, renderToClipboard);
    
    // Create Lighting Toolbar
    const renderLightingToolbar = () =>
        lightingToolbar(lightSettings, updateLightSetting);

    const renderTransformPanel = () => {
        if (!selectedObject || !selectedObject.data.position) return null;
        const fields = (type) =>
            [0,1,2].map(i =>
                React.createElement(
                    'div',
                    { className: 'slider-value-container', key: i },
                    React.createElement('i', {
                        className: 'fas fa-chevron-left slider-btn',
                        onClick: () => handleTransformArrow(type, i, -1)
                    }),
                    React.createElement('input', {
                        type: 'text',
                        className: 'slider-value',
                        style: { width: '40px' },
                        value: transformState[type][i],
                        onChange: (e) => {
                            const val = e.target.value; // just update display
                            setTransformState(prev => {
                                const arr = [...prev[type]];
                                arr[i] = val;
                                return { ...prev, [type]: arr };
                            });
                        },
                        onBlur: (e) => handleTransformCommit(type, i, e.target.value),
                        onKeyDown: (e) => { if (e.key === 'Enter') { e.target.blur(); } }
                    }),
                    React.createElement('i', {
                        className: 'fas fa-chevron-right slider-btn',
                        onClick: () => handleTransformArrow(type, i, 1)
                    })
                )
            );

        return React.createElement(
            'div',
            { className: 'transform-panel' },
            React.createElement(
                'div',
                { className: 'transform-row', style: { display: 'flex', alignItems: 'center', marginBottom: '10px' } },
                React.createElement(
                    'label',
                    { style: { marginRight: '0.5em', fontWeight: 'bold' } },
                    'T'
                ),
                React.createElement(
                    'div',
                    { className: 'vector-fields', style: { display: 'flex', gap: '10px' } },
                    ...fields('position')
                )
            ),
            React.createElement(
                'div',
                { className: 'transform-row', style: { display: 'flex', alignItems: 'center', marginBottom: '10px' } },
                React.createElement(
                    'label',
                    { style: { marginRight: '0.5em', fontWeight: 'bold'} },
                    'R'
                ),
                React.createElement(
                    'div',
                    { className: 'vector-fields', style: { display: 'flex', gap: '10px' } },
                    ...fields('rotation')
                )
            ),
            React.createElement(
                'div',
                { className: 'transform-row', style: { display: 'flex', alignItems: 'center', marginBottom: '10px' } },
                React.createElement(
                    'label',
                    { style: { marginRight: '0.5em', fontWeight: 'bold'} },
                    'S'
                ),
                React.createElement(
                    'div',
                    { className: 'vector-fields', style: { display: 'flex', gap: '10px' } },
                    ...fields('scale')
                )
            ),
            React.createElement(
                'div',
                { className: 'transform-lock-reset' },
                React.createElement(
                    'button',
                    { className: 'lock-btn tooltip', onClick: toggleScaleLock, 'data-tooltip': transformState.lockScale ? 'Unlock aspect ratio' : 'Lock aspect ratio' },
                    React.createElement('i', { className: transformState.lockScale ? 'fas fa-lock' : 'fas fa-lock-open' })
                ),
                React.createElement(
                    'button',
                    { className: 'reset-btn', onClick: resetTransform },
                    'Reset'
                )
            )
        );
    };
    
    // Loading Overlay
    const renderLoadingOverlay = () => {
        if (!isLoading) return null;
        
        return React.createElement(
            'div',
            { className: 'loading-overlay' },
            React.createElement('div', { className: 'spinner' })
        );
    };
    
    // Info Bar
    const renderInfoBar = () => {
        if (!selectedObject) {
            return React.createElement(
                'div',
                { className: 'info-bar' },
                React.createElement('span', null, 'No object selected. Click on an object to view details.')
            );
        }
        
        const { type, data } = selectedObject;
        
        let details = [];
        
        // Add common details
        details.push(`Name: ${data.id}`);
        details.push(`Type: ${type}`);
        
        // Add type-specific details
        if (type === 'mesh') {
            const vertexCount = data.vertices ? data.vertices.length : 0;
            const faceCount = data.faces ? Math.floor(data.faces.length / 3) : 0;
            details.push(`Vertices: ${vertexCount}`);
            details.push(`Faces: ${faceCount}`);
        } else if (type === 'animated_mesh') {
            const frameCount = data.vertices ? data.vertices.length : 0;
            const vertexCount = data.vertices && data.vertices[0] ? data.vertices[0].length : 0;
            const faceCount = data.faces ? Math.floor(data.faces.length / 3) : 0;
            details.push(`Frames: ${frameCount}`);
            details.push(`Vertices: ${vertexCount}`);
            details.push(`Faces: ${faceCount}`);
            details.push(`Framerate: ${data.framerate} fps`);
            details.push(`Playing: ${data.is_playing ? 'Yes' : 'No'}`);
        } else if (type === 'points') {
            const pointCount = data.points ? data.points.length : 0;
            details.push(`Points: ${pointCount}`);
        } else if (type === 'arrows') {
            const arrowCount = data.starts ? data.starts.length : 0;
            details.push(`Arrows: ${arrowCount}`);
        }
        
        return React.createElement(
            'div',
            { className: 'info-bar' },
            details.map((detail, index) => 
                React.createElement('span', { key: index, className: 'info-item' }, detail)
            )
        );
    };
    
    // Render Layers Panel
    const renderLayersPanel = () =>
        layersPanel(sceneObjects, selectedObject, setSelectedObject, sceneManagerRef, updateSceneObjectsList);

    const renderConsoleWindow = () => {
        if (!showConsole) return null;
        return React.createElement(
            'div',
            {
                className: 'console-window',
                style: { 
                    left: consolePos.x,
                    top: consolePos.y,
                    resize: 'both',
                    overflow: 'auto',
                    width: '300px',
                    height: '200px'
                }
            },
            React.createElement(
                'div',
                { className: 'console-header', onMouseDown: handleConsoleMouseDown },
                React.createElement('span', null, 'Console'),
                React.createElement(
                    'button',
                    { className: 'console-close', onClick: toggleConsole },
                    '×'
                )
            ),
            React.createElement('pre', { className: 'console-content', ref: consoleRef }, consoleLines.join(''))
        );
    };
    
    return React.createElement(
        'div',
        { className: "viewer-container" },
        React.createElement(
            'div',
            {
                className: "scene-container",
                ref: sceneRef
            },
            renderSceneToolbar(),
            renderRenderToolbar(),
            // renderLightingToolbar(),
            renderTransformPanel(),
            renderInfoBar(),
            renderLayersPanel(),
            renderConsoleWindow()
        ),
        // React.createElement(
        //     'button',
        //     {
        //         className: 'toggle-panel',
        //         onClick: togglePanelCollapse,
        //         title: isPanelCollapsed ? 'Show Panel' : 'Hide Panel',
        //         style: { left: isPanelCollapsed ? '16px' : '336px' }
        //     },
        //     React.createElement('i', { 
        //         className: isPanelCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left' 
        //     })
        // ),
        React.createElement(
            'div',
            { 
                className: `ui-panel ${isPanelCollapsed ? 'panel-collapsed' : ''}` 
            },
            React.createElement(
                'div',
                { className: 'ui-panel-header' },
                React.createElement('h2', null, "")
            ),
            React.createElement(
                'div',
                { className: 'ui-panel-content' },
                controls.length > 0 
                    ? controls.map(renderControl)
                    : React.createElement('p', null, "No controls available.")
            )
        ),
        // Render Modal
        showRenderModal && React.createElement(
            'div',
            { className: 'modal-overlay', onClick: discardImage },
            React.createElement(
                'div',
                { 
                    className: 'modal-content',
                    onClick: (e) => e.stopPropagation()
                },
                React.createElement('h3', null, 'Rendered View'),
                React.createElement('img', {
                    src: capturedImage,
                    alt: 'Rendered view',
                    style: { maxWidth: '100%', maxHeight: '400px' }
                }),
                React.createElement(
                    'div',
                    { className: 'modal-buttons' },
                    React.createElement(
                        'button',
                        { 
                            className: 'modal-btn save-btn',
                            onClick: saveImage
                        },
                        'Save As'
                    ),
                    React.createElement(
                        'button',
                        { 
                            className: 'modal-btn discard-btn',
                            onClick: discardImage
                        },
                        'Discard'
                    )
                )
            )
        )
    );
};

ReactDOM.render(
    React.createElement(App),
    document.getElementById('app')
);

initTooltips();

