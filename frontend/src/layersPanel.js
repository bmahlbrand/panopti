import React from 'react';

export function exportObject(objectId) {
    const link = document.createElement('a');
    const vid = window.viewerId || '';
    link.href = `/export/${vid}/${objectId}`;
    console.log(`Exporting object ${objectId} from ${link.href}`);
    link.download = `${objectId}.obj`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

export function toggleObjectVisibility(sceneManagerRef, sceneObjects, objectId, updateSceneObjectsList) {
    if (!sceneManagerRef.current) return;
    const obj = sceneObjects.find(o => o.id === objectId);
    if (!obj) return;
    let newVisibility = 'visible';
    let opacity = 1.0;
    if (obj.visible && obj.data.opacity === 1.0) {
        newVisibility = 'semi';
        opacity = 0.3;
    } else if (obj.visible && obj.data.opacity < 1.0) {
        newVisibility = 'hidden';
    } else {
        newVisibility = 'visible';
        opacity = 1.0;
    }
    let thisObject = sceneObjects.find(o => o.id === objectId);
    if (thisObject.type === 'arrows' && newVisibility === 'semi') {
        // For arrows we will just have visible / hidden, no opacity mode
        newVisibility = 'hidden';
    }
    const updates = { visible: newVisibility !== 'hidden', opacity };
    const updatedObj = sceneManagerRef.current.updateObject(objectId, updates);
    if (
        updatedObj &&
        (updatedObj.type === 'mesh' || updatedObj.type === 'points' || updatedObj.type == 'arrows' || updatedObj.type == 'animated_mesh') &&
        updatedObj.object.material
    ) {
        updatedObj.object.material.opacity = opacity;
        updatedObj.object.material.transparent = opacity < 1.0;
        updatedObj.object.material.needsUpdate = true;
    }
    updateSceneObjectsList();
}

export function toggleAnimatedMeshPlayback(sceneManagerRef, objectId, updateSceneObjectsList) {
    if (sceneManagerRef.current) {
        sceneManagerRef.current.toggleAnimatedMeshPlayback(objectId);
        updateSceneObjectsList();
    }
}

export function getObjectIcon(type) {
    switch (type) {
        case 'mesh':
            return 'mdi mdi-cube-outline mdi-24px';
        case 'animated_mesh':
            return 'mdi mdi-cube-send mdi-24px';
        case 'points':
            return 'mdi mdi-dots-triangle mdi-24px';
        case 'arrows':
            return 'mdi mdi-arrow-expand mdi-24px';
        default:
            return 'mdi mdi-help-circle-outline mdi-24px';
    }
}

export function getVisibilityIconClass(obj) {
    if (!obj.visible) {
        return 'fas fa-eye-slash visibility-hidden';
    } else if (obj.data.opacity < 1.0) {
        return 'fas fa-eye-low-vision visibility-semi';
    } else {
        return 'fas fa-eye visibility-visible';
    }
}

export function renderLayersPanel(sceneObjects, selectedObject, setSelectedObject, sceneManagerRef, updateSceneObjectsList) {
    return React.createElement(
        'div',
        { className: 'layers-panel' },
        React.createElement(
            'div',
            { className: 'layers-panel-header' },
            React.createElement('h3', null, 'Layers')
        ),
        React.createElement(
            'div',
            { className: 'layers-panel-content' },
            sceneObjects.length > 0
                ? sceneObjects.map(obj =>
                    React.createElement(
                        'div',
                        {
                            key: obj.id,
                            className: `layer-item ${selectedObject && selectedObject.data.id === obj.id ? 'selected' : ''} ${obj.data.warnings && obj.data.warnings.length > 0 ? 'warning' : ''}`,
                            onClick: () => {
                                const sceneObj = sceneManagerRef.current.getSelectedObject();
                                if (sceneObj && sceneObj.data.id === obj.id) {
                                    setSelectedObject(null);
                                    sceneManagerRef.current.selectObject(null);
                                } else {
                                    const objData = sceneManagerRef.current.getAllObjects().find(o => o.id === obj.id);
                                    if (objData) {
                                        setSelectedObject({ type: objData.type, data: objData.data });
                                        sceneManagerRef.current.selectObject(obj.id);
                                    }
                                }
                            }
                        },
                        React.createElement('i', { className: getObjectIcon(obj.type) }),
                        React.createElement('span', { className: 'layer-name' }, obj.id),
                        obj.data.warnings && obj.data.warnings.length > 0 &&
                            React.createElement('span', {
                                className: 'warning-icon tooltip',
                                'data-tooltip': obj.data.warnings.join('\n')
                            }, React.createElement('i', { className: 'fas fa-exclamation-circle' })),
                        React.createElement(
                            'div',
                            { className: 'layer-controls' },
                            obj.type === 'mesh' && React.createElement(
                                'button',
                                {
                                    className: 'export-button tooltip',
                                    'data-tooltip': 'Export as OBJ',
                                    onClick: (e) => {
                                        e.stopPropagation();
                                        exportObject(obj.id);
                                    }
                                },
                                React.createElement('i', { className: 'fas fa-download' })
                            ),
                            obj.type === 'animated_mesh' && React.createElement(
                                'button',
                                {
                                    className: 'play-pause-button tooltip',
                                    'data-tooltip': obj.data.is_playing ? 'Pause Animation' : 'Play Animation',
                                    onClick: (e) => {
                                        e.stopPropagation();
                                        toggleAnimatedMeshPlayback(sceneManagerRef, obj.id, updateSceneObjectsList);
                                    }
                                },
                                React.createElement('i', { className: obj.data.is_playing ? 'fas fa-pause' : 'fas fa-play' })
                            ),
                            (obj.type === 'animated_mesh' || obj.type === 'points') && React.createElement(
                                'button',
                                {
                                    className: 'export-button tooltip',
                                    'data-tooltip': 'Export as NPZ',
                                    onClick: (e) => {
                                        e.stopPropagation();
                                        exportObject(obj.id);
                                    }
                                },
                                React.createElement('i', { className: 'fas fa-download' })
                            ),
                            React.createElement(
                                'button',
                                {
                                    className: 'visibility-toggle',
                                    onClick: (e) => {
                                        e.stopPropagation();
                                        toggleObjectVisibility(sceneManagerRef, sceneObjects, obj.id, updateSceneObjectsList);
                                    }
                                },
                                React.createElement('i', { className: getVisibilityIconClass(obj) })
                            )
                        )
                    )
                )
                : React.createElement('p', { className: 'no-layers' }, 'No objects in scene')
        )
    );
}
