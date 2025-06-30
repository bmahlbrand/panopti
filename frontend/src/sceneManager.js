import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { VertexNormalsHelper } from 'three/addons/helpers/VertexNormalsHelper.js';
import { downloadFileFromBase64, cameraData } from './utils.js';
import { debounce, throttle } from './utils.js';
import * as CONSTANTS from './constants.js';

// Main Three.js scene setup:
export function createSceneManager(container, socket, callbacks = {}, backgroundColor = '#f0f0f0') {
    const { onSelectObject, onSceneObjectsChange } = callbacks;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(backgroundColor);

    // Add directional light
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.7 + 1.5 * 3.0);
    directionalLight.position.set(10, 15, 10);
    directionalLight.castShadow = true;
    directionalLight.shadow.camera.near = 0.1;
    directionalLight.shadow.camera.far = 50;
    directionalLight.shadow.camera.left = -20;
    directionalLight.shadow.camera.right = 20;
    directionalLight.shadow.camera.top = 20;
    directionalLight.shadow.camera.bottom = -20;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    scene.add(directionalLight);
    
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.2 + 2.25);
    scene.add(ambientLight);
    
    const hemiLight = new THREE.HemisphereLight(0x87CEEB, 0x8B7355, 0.0);
    hemiLight.position.set(0, 20, 0);
    scene.add(hemiLight);

    const fillLight = new THREE.DirectionalLight(0xffffff, 4.5);
    fillLight.position.set(-20, 5, -10);
    scene.add(fillLight);

    let lightSettings = {
        ambientColor: '#ffffff',
        ambientIntensity: 0.0,
        directionalColor: '#ffffff',
        directionalIntensity: 0.0,
    };
    
    // Add camera
    const { clientWidth, clientHeight } = container;
    const camera = new THREE.PerspectiveCamera(
        50, clientWidth / clientHeight, 0.1, 1000
    );
    // const camera = new THREE.OrthographicCamera( clientWidth / - 2, clientWidth / 2, clientHeight / 2, clientHeight / - 2, 1, 1000 );
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);
    
    const initialCameraPosition = camera.position.clone();
    const initialCameraTarget = new THREE.Vector3(0, 0, 0);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(clientWidth, clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);
    
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;

    controls.addEventListener('change', throttle(() => {
        if (socket) {
            const camData = cameraData(camera, controls);
            const payload = { camera: camData };
            if (window.viewerId) payload.viewer_id = window.viewerId;
            socket.emit('events.camera', payload);
        }
    }, CONSTANTS.DEBOUNCE_EVENTS_CAMERA));
    

    const gridHelper = new THREE.GridHelper(10, 10);
    scene.add(gridHelper);
    
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
    
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const normalHelpers = {};
    const objects = {};
    
    let renderSettings = {
        wireframe: 0, // 0: normal, 1: wireframe with geometry, 2: pure wireframe
        flatShading: false,
        showNormals: false,
        showGrid: true,
        showAxes: true,
        inspectMode: false
    };
    
    let selectedObject = null;
    
    // Create inspection text overlay
    const inspectionDiv = document.createElement('div');
    inspectionDiv.style.position = 'absolute';
    inspectionDiv.style.background = 'rgba(0, 0, 0, 0.8)';
    inspectionDiv.style.color = 'white';
    inspectionDiv.style.padding = '8px 12px';
    inspectionDiv.style.borderRadius = '4px';
    inspectionDiv.style.fontSize = '12px';
    inspectionDiv.style.fontFamily = 'monospace';
    inspectionDiv.style.pointerEvents = 'none';
    inspectionDiv.style.display = 'none';
    inspectionDiv.style.zIndex = '1000';
    inspectionDiv.style.maxWidth = '200px';
    inspectionDiv.style.whiteSpace = 'pre-line';
    container.appendChild(inspectionDiv);

    const inspectionContent = document.createElement('div');
    inspectionContent.style.pointerEvents = 'none';
    inspectionDiv.appendChild(inspectionContent);

    // Close button for inspection overlay
    const closeBtn = document.createElement('span');
    closeBtn.textContent = '✕';
    closeBtn.style.position = 'absolute';
    closeBtn.style.top = '2px';
    closeBtn.style.right = '4px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.style.pointerEvents = 'auto';
    inspectionDiv.appendChild(closeBtn);
    
    // Visual inspection helpers
    let inspectionHighlight = null;
    let inspectionVertexPoints = null;
    let inspectionPoint = null;
    let inspectionData = null;
    
    // Function to clear inspection highlights
    function clearInspectionHighlights() {
        if (inspectionHighlight) {
            scene.remove(inspectionHighlight);
            if (inspectionHighlight.geometry) inspectionHighlight.geometry.dispose();
            if (inspectionHighlight.material) inspectionHighlight.material.dispose();
            inspectionHighlight = null;
        }
        if (inspectionVertexPoints) {
            scene.remove(inspectionVertexPoints);
            if (inspectionVertexPoints.geometry) inspectionVertexPoints.geometry.dispose();
            if (inspectionVertexPoints.material) inspectionVertexPoints.material.dispose();
            inspectionVertexPoints = null;
        }
        inspectionPoint = null;
        inspectionData = null;
    }

    // Close button handler to hide overlay and clear highlights
    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        inspectionDiv.style.display = 'none';
        clearInspectionHighlights();
    });

    function computeBarycentric(p, a, b, c) {
        const v0 = b.clone().sub(a);
        const v1 = c.clone().sub(a);
        const v2 = p.clone().sub(a);
        const d00 = v0.dot(v0);
        const d01 = v0.dot(v1);
        const d11 = v1.dot(v1);
        const d20 = v2.dot(v0);
        const d21 = v2.dot(v1);
        const denom = d00 * d11 - d01 * d01;
        const v = (d11 * d20 - d01 * d21) / denom;
        const w = (d00 * d21 - d01 * d20) / denom;
        const u = 1 - v - w;
        return { u, v, w };
    }
    
    // Add click event listener for object selection and inspection
    container.addEventListener('click', (event) => {
        const rect = container.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        raycaster.setFromCamera(mouse, camera);
        
        if (renderSettings.inspectMode) {
            raycaster.params.Line.threshold = 0.1;
        }
        
        // Get all selectable objects
        const selectableObjects = Object.values(objects)
            .map(obj => obj.object)
            .filter(obj => obj.visible);
        
        // In inspection mode, we want to intersect with the actual mesh objects, not wireframe overlays
        let intersectTargets = selectableObjects;
        let temporaryMaterials = new Map();
        
        if (renderSettings.inspectMode) {
            // Filter to only mesh objects and ensure we hit the main mesh, not wireframe helpers
            intersectTargets = selectableObjects.filter(obj => {
                return !(obj.material && obj.material.type === 'LineBasicMaterial');
            });
            
            // For wireframe materials, temporarily replace with solid material for raycasting
            intersectTargets.forEach(obj => {
                if (obj.material && obj.material.wireframe === true) {
                    temporaryMaterials.set(obj, obj.material);
                    obj.material = new THREE.MeshBasicMaterial({
                        color: obj.material.color,
                        transparent: true,
                        opacity: 0.01,
                        side: THREE.DoubleSide
                    });
                }
            });
        }
        
        const intersects = raycaster.intersectObjects(intersectTargets, false);
        
        // Restore original materials
        temporaryMaterials.forEach((originalMaterial, obj) => {
            obj.material.dispose();
            obj.material = originalMaterial;
        });
        
        if (intersects.length > 0) {
            const intersection = intersects[0];
            const intersectedObject = intersection.object;
            let topLevelObject = intersectedObject;
            
            // Traverse up the hierarchy if needed
            while (topLevelObject.parent && topLevelObject.parent !== scene) {
                topLevelObject = topLevelObject.parent;
            }
            
            // Find the object data for the intersected object
            let objectData = null;
            for (const [id, obj] of Object.entries(objects)) {
                if (obj.object === topLevelObject) {
                    objectData = obj;
                    break;
                }
            }

            if (renderSettings.inspectMode && objectData && (objectData.type === 'mesh' || objectData.type === 'animated_mesh' || objectData.type === 'points')) {
                clearInspectionHighlights();

                const faceIndex = intersection.faceIndex;
                const targetGeometry = intersectedObject.geometry;

                // Inspection mode: show information depending on object type
                if (objectData.type === 'points' && intersection.instanceId !== undefined) {
                    const pointIndex = intersection.instanceId;

                    // Highlight the selected point
                    const highlightGeom = new THREE.SphereGeometry(objectData.data.size * 1.2, 8, 8);
                    const highlightMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
                    inspectionHighlight = new THREE.Mesh(highlightGeom, highlightMat);
                    inspectionHighlight.position.copy(intersection.point);
                    scene.add(inspectionHighlight);

                    inspectionPoint = intersection.point.clone();

                    inspectionData = {
                        object: intersectedObject,
                        type: objectData.type,
                        index: pointIndex
                    };

                    // Display inspection info
                    inspectionContent.textContent = `Point Index: ${pointIndex}`;
                    inspectionDiv.style.display = 'block';
                    inspectionDiv.style.left = (event.clientX + 10) + 'px';
                    inspectionDiv.style.top = (event.clientY - 10) + 'px';

                    // Emit inspection event to server
                    if (socket) {
                        const payload = {
                            inspection: {
                                object_name: objectData.data.id,
                                object_type: objectData.type,
                                inspect_result: { point_index: pointIndex },
                                world_coords: [intersection.point.x, intersection.point.y, intersection.point.z],
                                screen_coords: [event.clientX - rect.left, event.clientY - rect.top]
                            }
                        };
                        if (window.viewerId) payload.viewer_id = window.viewerId;
                        socket.emit('events.inspect', payload);
                    }
                } else if (faceIndex !== undefined && targetGeometry) {
                    let inspectionText = `Face Index: ${faceIndex}\n`;
                    let vertexIndices = [];

                    if (targetGeometry.index) {
                        // Indexed geometry
                        const a = targetGeometry.index.array[faceIndex * 3];
                        const b = targetGeometry.index.array[faceIndex * 3 + 1];
                        const c = targetGeometry.index.array[faceIndex * 3 + 2];
                        vertexIndices = [a, b, c];
                        inspectionText += `Vertex Indices: ${a}, ${b}, ${c}`;
                    } else {
                        // Non-indexed geometry
                        const a = faceIndex * 3;
                        const b = faceIndex * 3 + 1;
                        const c = faceIndex * 3 + 2;
                        vertexIndices = [a, b, c];
                        inspectionText += `Vertex Indices: ${a}, ${b}, ${c}`;
                    }

                    // Create visual highlights
                    const positionAttribute = targetGeometry.getAttribute('position');
                    if (positionAttribute && vertexIndices.length === 3) {
                        // Create face highlight
                        const faceVertices = [];
                        const localVerts = [];
                        const worldVerts = [];

                        for (let i = 0; i < 3; i++) {
                            const idx = vertexIndices[i];
                            const x = positionAttribute.array[idx * 3];
                            const y = positionAttribute.array[idx * 3 + 1];
                            const z = positionAttribute.array[idx * 3 + 2];
                            faceVertices.push(x, y, z);
                            const lv = new THREE.Vector3(x, y, z);
                            localVerts.push(lv.clone());
                            worldVerts.push(lv);
                        }

                        // Transform vertex positions to world space
                        const worldMatrix = topLevelObject.matrixWorld;
                        worldVerts.forEach(pos => pos.applyMatrix4(worldMatrix));

                        // Compute barycentric coordinates of the intersection
                        const invMatrix = new THREE.Matrix4().copy(worldMatrix).invert();
                        const localHit = intersection.point.clone().applyMatrix4(invMatrix);
                        const bary = computeBarycentric(localHit, localVerts[0], localVerts[1], localVerts[2]);

                        // Create face highlight
                        const faceGeometry = new THREE.BufferGeometry();
                        faceGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(faceVertices), 3));
                        faceGeometry.setIndex([0, 1, 2]);

                        const faceMaterial = new THREE.MeshBasicMaterial({
                            color: 0xff0000,
                            transparent: true,
                            opacity: 0.5,
                            side: THREE.DoubleSide
                        });

                        inspectionHighlight = new THREE.Mesh(faceGeometry, faceMaterial);
                        inspectionHighlight.matrix.copy(worldMatrix);
                        inspectionHighlight.matrixAutoUpdate = false;
                        scene.add(inspectionHighlight);

                        // Create vertex points
                        const pointsGeometry = new THREE.BufferGeometry();
                        const pointPositions = [];
                        worldVerts.forEach(pos => {
                            pointPositions.push(pos.x, pos.y, pos.z);
                        });
                        pointsGeometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pointPositions), 3));

                        const pointsMaterial = new THREE.PointsMaterial({
                            color: 0x00ff00,
                            size: 8,
                            sizeAttenuation: false
                        });

                        inspectionVertexPoints = new THREE.Points(pointsGeometry, pointsMaterial);
                        scene.add(inspectionVertexPoints);

                        // Store inspection data for animated meshes
                        inspectionData = {
                            object: topLevelObject,
                            type: objectData.type,
                            vertexIndices: vertexIndices,
                            barycentric: bary
                        };
                    }

                    inspectionPoint = intersection.point.clone();

                    // Display inspection information
                    inspectionContent.textContent = inspectionText;
                    inspectionDiv.style.display = 'block';
                    inspectionDiv.style.left = (event.clientX + 10) + 'px';
                    inspectionDiv.style.top = (event.clientY - 10) + 'px';

                    if (socket) {
                        const payload = {
                            inspection: {
                                object_name: objectData.data.id,
                                object_type: objectData.type,
                                inspect_result: {
                                    face_index: faceIndex,
                                    vertex_indices: vertexIndices
                                },
                                world_coords: [intersection.point.x, intersection.point.y, intersection.point.z],
                                screen_coords: [event.clientX - rect.left, event.clientY - rect.top]
                            }
                        };
                        if (window.viewerId) payload.viewer_id = window.viewerId;
                        socket.emit('events.inspect', payload);
                    }
                }
            } else {
                // Regular selection mode
                if (objectData) {
                    selectedObject = { ...objectData };
                    
                    // Notify React component about selection
                    if (typeof onSelectObject === 'function') {
                        onSelectObject(null);
                        onSelectObject({ type: objectData.type, data: objectData.data });
                        event_select_object(objectData.data.id);
                    }
                }
            }
        } else {
            // Clicked empty space; only deselect if the click originated on the canvas
            // TODO check how we are absorbing clicks here:
            // if (!renderSettings.inspectMode && event.composedPath().includes(renderer.domElement)) {
            //     selectedObject = null;
            //     if (typeof onSelectObject === 'function') {
            //         console.log('Deselected object');
            //         onSelectObject(null);
            //     }
            // }
            
            // Keep inspection overlay visible in inspection mode
        }
    });
    
    // Socket event handlers
    socket.on('add_mesh', (data) => {
        addMesh(data);
        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    });
    
    socket.on('add_animated_mesh', (data) => {
        addAnimatedMesh(data);
        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    });
    
    socket.on('add_points', (data) => {
        addPoints(data);
        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    });
    
    socket.on('add_arrows', (data) => {
        addArrows(data);
        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    });
    
    socket.on('update_object', (data) => {
        // check what index the current object is in the layers panel:
        const layerIndex = Object.keys(objects).findIndex(id => id === data.id);
        const _selectedObject = selectedObject ? { ...selectedObject } : null;

        updateObject(data.id, data.updates);

        if (objects[data.id]) {
            const objType = objects[data.id].type;
            const objData = { ...objects[data.id].data, ...data.updates };
            
            if (objType === 'mesh') {
                addMesh(objData);
            } else if (objType === 'points') {
                addPoints(objData);
            } else if (objType === 'arrows') {
                addArrows(objData);
            }
            
            // Retainn the layer panel's ordering:
            const updatedObject = objects[data.id];
            const remainingKeys = Object.keys(objects).filter(key => key !== data.id);
            remainingKeys.splice(layerIndex, 0, data.id);
            const newOrder = {};
            remainingKeys.forEach(key => newOrder[key] = key === data.id ? updatedObject : objects[key]);
            for (const key in objects) {
                delete objects[key];
            }
            Object.assign(objects, newOrder);

            // Check if the updated object is currently selected, preserve selection:
            const isSelected = _selectedObject && _selectedObject.data.id === data.id;
            if (isSelected && typeof onSelectObject === 'function') {
                console.log('Retaining selection for updated object:', data.id);
                onSelectObject({ type: _selectedObject.type, data: objData });
            }

        }

        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    });
    
    socket.on('delete_object', (data) => {
        deleteObject(data.id);
        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    });

    socket.on('download_file', (data) => {
        if (data.viewer_id && window.viewerId && data.viewer_id !== window.viewerId) {
            return;
        }
        downloadFileFromBase64(data.filename, data.data);
    });

    socket.on('http_event', (info) => {
        if (info.viewer_id && window.viewerId && info.viewer_id !== window.viewerId) {
            return;
        }
        fetch(info.url)
            .then(resp => resp.json())
            .then(data => {
                switch (info.event) {
                    case 'add_mesh':
                        addMesh(data);
                        break;
                    case 'add_animated_mesh':
                        addAnimatedMesh(data);
                        break;
                    case 'add_points':
                        addPoints(data);
                        break;
                    case 'add_arrows':
                        addArrows(data);
                        break;
                    case 'update_object':
                        updateObject(data.id, data.updates);
                        break;
                    case 'download_file':
                        downloadFileFromBase64(data.filename, data.data);
                        break;
                }
                if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
            });
    });
    
    // Scene management functions
    function addMesh(data) {
        if (objects[data.id]) {
            deleteObject(data.id);
        }
        
        let geometry = new THREE.BufferGeometry();
        
        const vertices = new Float32Array(data.vertices.flat());
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        
        if (data.faces && data.faces.length > 0) {
            const indices = new Uint32Array(data.faces.flat());
            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        }
        
        let vcolors = false;
        let fcolors = false;
        if (data.vertex_colors) {
            const colors = new Float32Array(data.vertex_colors.flat());
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            vcolors = true;
        }else if (data.face_colors) {
            geometry = geometry.toNonIndexed();
            const colors = [];
            for (let i = 0; i < data.face_colors.length; i++) {
                colors.push(...data.face_colors[i]);
                colors.push(...data.face_colors[i]);
                colors.push(...data.face_colors[i]);
            }
            geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
            fcolors = true;
        }
        
        let material;
        const wireframeMode = data.wireframe ? 2 : renderSettings.wireframe;
        if (wireframeMode === 2) {
            material = new THREE.MeshBasicMaterial({
                color: new THREE.Color(data.color[0], data.color[1], data.color[2]),
                wireframe: true
            });
        } else {
            material = new THREE.MeshPhongMaterial({
                color: new THREE.Color(data.color[0], data.color[1], data.color[2]),
                vertexColors: vcolors || fcolors,
                transparent: data.opacity < 1.0,
                opacity: data.opacity,
                flatShading: renderSettings.flatShading,
                shininess: 30
            });
        }
        
        let wireframeHelper = null;
        if (wireframeMode === 1) {
            const wireGeometry = new THREE.WireframeGeometry(geometry);
            wireframeHelper = new THREE.LineSegments(wireGeometry);
            wireframeHelper.material.depthTest = false;
            wireframeHelper.material.opacity = 0.25;
            wireframeHelper.material.transparent = true;
            wireframeHelper.material.color = new THREE.Color(0, 0, 0);
        }
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.position.set(data.position[0], data.position[1], data.position[2]);
        mesh.rotation.set(data.rotation[0], data.rotation[1], data.rotation[2]);
        mesh.scale.set(data.scale[0], data.scale[1], data.scale[2]);
        
        if (wireframeMode !== 2 && !geometry.attributes.normal) {
            geometry.computeVertexNormals();
        }
        
        mesh.visible = data.visible;
        scene.add(mesh);
        
        if (wireframeHelper) {
            mesh.add(wireframeHelper);
            mesh.userData.wireframeHelper = wireframeHelper;
        }
        
        if (renderSettings.showNormals) {
            const normalHelper = new VertexNormalsHelper(mesh, 0.2, 0x00ff00, 1);
            scene.add(normalHelper);
            normalHelpers[data.id] = normalHelper;
        }
        
        objects[data.id] = {
            object: mesh,
            type: 'mesh',
            data: data
        };
    }
    
    function addAnimatedMesh(data) {
        if (objects[data.id]) {
            deleteObject(data.id);
        }
        
        // Validate vertices format - should be 3D array (frames, vertices, 3)
        if (!data.vertices || data.vertices.length === 0 || !Array.isArray(data.vertices[0]) || !Array.isArray(data.vertices[0][0])) {
            console.error('Invalid animated mesh vertices format. Expected (frames, vertices, 3)');
            return;
        }
        
        const numFrames = data.vertices.length;
        const numVertices = data.vertices[0].length;
        
        let geometry = new THREE.BufferGeometry();
        
        const initialVertices = new Float32Array(data.vertices[0].flat());
        geometry.setAttribute('position', new THREE.BufferAttribute(initialVertices, 3));
        
        if (data.faces && data.faces.length > 0) {
            const indices = new Uint32Array(data.faces.flat());
            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        }
        
        // Set vertex colors if available (using first frame)
        let vcolors = false;
        let fcolors = false;
        if (data.vertex_colors) {
            const colors = new Float32Array(data.vertex_colors.flat());
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            vcolors = true;
        } else if (data.face_colors) {
            geometry = geometry.toNonIndexed();
            const colors = [];
            for (let i = 0; i < data.face_colors.length; i++) {
                colors.push(...data.face_colors[i]);
                colors.push(...data.face_colors[i]);
                colors.push(...data.face_colors[i]);
            }
            geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
            fcolors = true;
        }
        
        let material;
        const wireframeMode = data.wireframe ? 2 : renderSettings.wireframe;
        
        if (wireframeMode === 2) {
            material = new THREE.MeshBasicMaterial({
                color: new THREE.Color(data.color[0], data.color[1], data.color[2]),
                wireframe: true
            });
        } else {
            material = new THREE.MeshPhongMaterial({
                color: new THREE.Color(data.color[0], data.color[1], data.color[2]),
                vertexColors: vcolors || fcolors,
                transparent: data.opacity < 1.0,
                opacity: data.opacity,
                flatShading: renderSettings.flatShading,
                shininess: 30
            });
        }
        
        let wireframeHelper = null;
        if (wireframeMode === 1) {
            const wireGeometry = new THREE.WireframeGeometry(geometry);
            wireframeHelper = new THREE.LineSegments(wireGeometry);
            wireframeHelper.material.depthTest = false;
            wireframeHelper.material.opacity = 0.25;
            wireframeHelper.material.transparent = true;
            wireframeHelper.material.color = new THREE.Color(0, 0, 0);
        }
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.position.set(data.position[0], data.position[1], data.position[2]);
        mesh.rotation.set(data.rotation[0], data.rotation[1], data.rotation[2]);
        mesh.scale.set(data.scale[0], data.scale[1], data.scale[2]);
        
        if (wireframeMode !== 2 && !geometry.attributes.normal) {
            geometry.computeVertexNormals();
        }
        
        mesh.visible = data.visible;
        scene.add(mesh);
        
        if (wireframeHelper) {
            mesh.add(wireframeHelper);
            mesh.userData.wireframeHelper = wireframeHelper;
        }
        
        if (renderSettings.showNormals) {
            const normalHelper = new VertexNormalsHelper(mesh, 0.2, 0x00ff00, 1);
            scene.add(normalHelper);
            normalHelpers[data.id] = normalHelper;
        }
        
        const animationData = {
            vertices: data.vertices,
            framerate: data.framerate,
            currentFrame: data.current_frame || 0,
            isPlaying: data.is_playing || false,
            startTime: data.is_playing ? Date.now() / 1000 : null,
            numFrames: numFrames
        };
        
        objects[data.id] = {
            object: mesh,
            type: 'animated_mesh',
            data: data,
            animation: animationData
        };
    }
    
    function addPoints(data) {
        if (objects[data.id]) {
            deleteObject(data.id);
        }

        const count = data.points.length;

        // Base sphere geometry with few segments for performance
        const geometry = new THREE.SphereGeometry(data.size, 6, 6);

        let material;
        const usePerColor = Array.isArray(data.colors[0]);
        if (usePerColor) {
            material = new THREE.MeshStandardMaterial({
                color: new THREE.Color(0.9, 0.9, 0.9) // temporary color, will override with setColorAt
            });
        } else {
            material = new THREE.MeshStandardMaterial({
                color: new THREE.Color(data.colors[0], data.colors[1], data.colors[2])
            });
        }

        const spheres = new THREE.InstancedMesh(geometry, material, count);
        const dummy = new THREE.Object3D();
        for (let i = 0; i < count; i++) {
            const p = data.points[i];
            dummy.position.set(p[0], p[1], p[2]);
            dummy.updateMatrix();
            spheres.setMatrixAt(i, dummy.matrix);

            if (usePerColor) {
                const c = data.colors[i];
                spheres.setColorAt(i, new THREE.Color(c[0], c[1], c[2]));
            }
        }

        if (usePerColor && spheres.instanceColor) {
            spheres.instanceColor.needsUpdate = true;
        }

        spheres.castShadow = true;
        spheres.receiveShadow = true;
        spheres.visible = data.visible;
        scene.add(spheres);

        objects[data.id] = {
            object: spheres,
            type: 'points',
            data: data
        };
    }
    
    const ARROW_BODY = new THREE.CylinderGeometry( 1, 1, 1, 12 ).rotateX( Math.PI/2).translate( 0, 0, 0.5 );
    const ARROW_HEAD = new THREE.ConeGeometry( 1, 1, 12 ).rotateX( Math.PI/2).translate( 0, 0, -0.5 );
    function customArrow( fx, fy, fz, ix, iy, iz, color, data) {
        // borrowed from: https://discourse.threejs.org/t/how-do-you-make-a-custom-arrow/55401/9
        let thickness = data.width;
        let transparent = data.opacity < 1.0;
        let opacity = data.opacity;
        var material = new THREE.MeshPhongMaterial( { color: color, flatShading: false, transparent: transparent, opacity: opacity} );
        var length = Math.sqrt( (ix-fx)**2 + (iy-fy)**2 + (iz-fz)**2 );
        var body = new THREE.Mesh( ARROW_BODY, material );
            body.scale.set( thickness, thickness, length-10*thickness );
        var head = new THREE.Mesh( ARROW_HEAD, material );
            head.position.set( 0, 0, length );
            head.scale.set( 3*thickness, 3*thickness, 10*thickness );
        var arrow = new THREE.Group( );
            arrow.position.set( ix, iy, iz );
            arrow.lookAt( fx, fy, fz );	
            arrow.add( body, head );
        return arrow;
    }

    function addArrows(data) {
        if (objects[data.id]) {
            deleteObject(data.id);
        }    
        
        const group = new THREE.Group();
        const starts = data.starts;
        const ends = data.ends;
        for (let i = 0; i < starts.length; i++) {
            let col = Array.isArray(data.color[0]) ? new THREE.Color(data.color[i][0], data.color[i][1], data.color[i][2]) : new THREE.Color(data.color[0], data.color[1], data.color[2]);
            const arrowHelper = customArrow(
                starts[i][0], starts[i][1], starts[i][2],
                ends[i][0], ends[i][1], ends[i][2],
                col,
                data
            );
            group.add(arrowHelper);
        }
        
        group.visible = data.visible !== undefined ? data.visible : true;
        scene.add(group);
        
        objects[data.id] = {
            object: group,
            type: 'arrows',
            data: data
        };
    }
    
    function updateObject(id, updates) {
        const objData = objects[id];
        if (!objData) return;

        const newUpdates = { ...updates };

        if (objData.type === 'mesh' || objData.type === 'points' || objData.type === 'animated_mesh') {
            if (updates.visible !== undefined) {
                objData.object.visible = updates.visible;
                objData.data.visible = updates.visible;
            }

            if (updates.opacity !== undefined && objData.object.material) {
                objData.data.opacity = updates.opacity;
                objData.object.material.opacity = updates.opacity;
                objData.object.material.transparent = updates.opacity < 1.0;
            }
        } else if (objData.type === 'arrows') {
            if (updates.visible !== undefined) {
                objData.object.visible = updates.visible;
                objData.data.visible = updates.visible;
            }
        }

        if (updates.position) {
            objData.object.position.set(updates.position[0], updates.position[1], updates.position[2]);
            objData.data.position = updates.position;
        }

        if (updates.rotation) {
            objData.object.rotation.set(updates.rotation[0], updates.rotation[1], updates.rotation[2]);
            objData.data.rotation = updates.rotation;
        }

        if (updates.scale) {
            objData.object.scale.set(updates.scale[0], updates.scale[1], updates.scale[2]);
            objData.data.scale = updates.scale;
        }

        // Store any additional fields
        for (const [key, value] of Object.entries(updates)) {
            if (!['visible', 'opacity', 'position', 'rotation', 'scale'].includes(key)) {
                objData.data[key] = value;
            }
        }

        return objData;
    }
    
    function deleteObject(id) {
        const objData = objects[id];
        if (!objData) return;
        
        const { object } = objData;
        
        scene.remove(object);
        
        if (normalHelpers[id]) {
            scene.remove(normalHelpers[id]);
            if (normalHelpers[id].geometry) {
                normalHelpers[id].geometry.dispose();
            }
            if (normalHelpers[id].material) {
                normalHelpers[id].material.dispose();
            }
            delete normalHelpers[id];
        }
        
        if (object.geometry) {
            object.geometry.dispose();
        }
        
        if (object.material) {
            if (Array.isArray(object.material)) {
                object.material.forEach(material => material.dispose());
            } else {
                object.material.dispose();
            }
        }
        
        delete objects[id];
        
        if (selectedObject && selectedObject.data.id === id) {
            selectedObject = null;
            if (typeof onSelectObject === 'function') {
                onSelectObject(null);
            }
        }
    }
    
    function onWindowResize(width, height) {
        if (!width || !height) {
            const containerRect = container.getBoundingClientRect();
            width = containerRect.width;
            height = containerRect.height;
        }
        
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        renderer.setSize(width, height, true);
        renderer.setPixelRatio(window.devicePixelRatio);
    }
    
    function update() {
        controls.update();
        
        // Update animated meshes
        const currentTime = Date.now() / 1000;
        for (const [id, objData] of Object.entries(objects)) {
            if (objData.type === 'animated_mesh' && objData.animation.isPlaying) {
                const animation = objData.animation;
                const elapsed = currentTime - animation.startTime;
                const frameFloat = (elapsed * animation.framerate) % animation.numFrames;
                const currentFrame = Math.floor(frameFloat);
                const nextFrame = (currentFrame + 1) % animation.numFrames;
                const t = frameFloat - currentFrame;
                
                // Interpolate between current and next frame
                const currentVertices = animation.vertices[currentFrame];
                const nextVertices = animation.vertices[nextFrame];
                const interpolatedVertices = [];
                
                for (let i = 0; i < currentVertices.length; i++) {
                    const current = currentVertices[i];
                    const next = nextVertices[i];
                    interpolatedVertices.push([
                        current[0] + t * (next[0] - current[0]),
                        current[1] + t * (next[1] - current[1]),
                        current[2] + t * (next[2] - current[2])
                    ]);
                }
                
                // Update geometry
                const vertices = new Float32Array(interpolatedVertices.flat());
                objData.object.geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
                objData.object.geometry.attributes.position.needsUpdate = true;
                
                // Recompute normals if needed
                if (!objData.data.wireframe) {
                    objData.object.geometry.computeVertexNormals();
                }
                
                animation.currentFrame = currentFrame;
            }
        }
        
        // Update normal helpers if they exist
        if (renderSettings.showNormals) {
            for (const [id, helper] of Object.entries(normalHelpers)) {
                if (helper && helper.update) {
                    helper.update();
                }
            }
        }

        // Update inspection highlight for moving objects
        if (inspectionData && (inspectionData.type === 'mesh' || inspectionData.type === 'animated_mesh')) {
            const obj = inspectionData.object;
            const geom = obj.geometry;
            const posAttr = geom.getAttribute('position');
            if (posAttr) {
                const ai = inspectionData.vertexIndices[0];
                const bi = inspectionData.vertexIndices[1];
                const ci = inspectionData.vertexIndices[2];
                const v0 = new THREE.Vector3(posAttr.array[ai * 3], posAttr.array[ai * 3 + 1], posAttr.array[ai * 3 + 2]);
                const v1 = new THREE.Vector3(posAttr.array[bi * 3], posAttr.array[bi * 3 + 1], posAttr.array[bi * 3 + 2]);
                const v2 = new THREE.Vector3(posAttr.array[ci * 3], posAttr.array[ci * 3 + 1], posAttr.array[ci * 3 + 2]);

                const worldMatrix = obj.matrixWorld;
                const w0 = v0.clone().applyMatrix4(worldMatrix);
                const w1 = v1.clone().applyMatrix4(worldMatrix);
                const w2 = v2.clone().applyMatrix4(worldMatrix);

                if (inspectionHighlight) {
                    const arr = inspectionHighlight.geometry.getAttribute('position').array;
                    arr[0] = v0.x; arr[1] = v0.y; arr[2] = v0.z;
                    arr[3] = v1.x; arr[4] = v1.y; arr[5] = v1.z;
                    arr[6] = v2.x; arr[7] = v2.y; arr[8] = v2.z;
                    inspectionHighlight.geometry.attributes.position.needsUpdate = true;
                    inspectionHighlight.matrix.copy(worldMatrix);
                }

                if (inspectionVertexPoints) {
                    const arr = inspectionVertexPoints.geometry.getAttribute('position').array;
                    arr[0] = w0.x; arr[1] = w0.y; arr[2] = w0.z;
                    arr[3] = w1.x; arr[4] = w1.y; arr[5] = w1.z;
                    arr[6] = w2.x; arr[7] = w2.y; arr[8] = w2.z;
                    inspectionVertexPoints.geometry.attributes.position.needsUpdate = true;
                }

                const bary = inspectionData.barycentric;
                const localPoint = v0.clone().multiplyScalar(bary.u)
                    .add(v1.clone().multiplyScalar(bary.v))
                    .add(v2.clone().multiplyScalar(bary.w));
                inspectionPoint.copy(localPoint.applyMatrix4(worldMatrix));
            }
        }

        // Reposition inspection overlay if active
        if (inspectionDiv.style.display !== 'none' && inspectionPoint) {
            const vector = inspectionPoint.clone().project(camera);
            const rect = container.getBoundingClientRect();
            const x = rect.left + (vector.x + 1) / 2 * rect.width;
            const y = rect.top + (-vector.y + 1) / 2 * rect.height;
            inspectionDiv.style.left = (x + 10) + 'px';
            inspectionDiv.style.top = (y - 10) + 'px';
        }

        renderer.render(scene, camera);
    }
    
    function resetCamera() {
        camera.position.copy(initialCameraPosition);
        controls.target.copy(initialCameraTarget);
        controls.update();
    }
    
    function setBackgroundColor(colorHex) {
        scene.background = new THREE.Color(colorHex);
    }
    
    function clearAllObjects() {
        Object.keys(objects).forEach(deleteObject);
        if (typeof onSceneObjectsChange === 'function') {
            onSceneObjectsChange();
        }
    }
    
    function dispose() {
        clearAllObjects();
        clearInspectionHighlights();
        if (container.contains(inspectionDiv)) {
            container.removeChild(inspectionDiv);
        }
        
        if (renderer) {
            renderer.dispose();
            if (container.contains(renderer.domElement)) {
                container.removeChild(renderer.domElement);
            }
        }
    }
    
    function applyRenderSettings(settings) {
        renderSettings = { ...settings };
        
        for (const [id, objData] of Object.entries(objects)) {
            if (objData.type === 'mesh') {
                const { object, data } = objData;

                if (object.material && !Array.isArray(object.material)) {
                    const wireframeMode = renderSettings.wireframe;

                    if (object.userData.wireframeHelper) {
                        object.remove(object.userData.wireframeHelper);
                        if (object.userData.wireframeHelper.geometry) {
                            object.userData.wireframeHelper.geometry.dispose();
                        }
                        if (object.userData.wireframeHelper.material) {
                            object.userData.wireframeHelper.material.dispose();
                        }
                        object.userData.wireframeHelper = null;
                    }
                    
                    // Apply appropriate material based on wireframe mode
                    if (wireframeMode === 2) {
                        // Mode 2: Pure wireframe
                        if (object.material.type !== 'MeshBasicMaterial' || !object.material.wireframe) {
                            // Replace with wireframe material
                            const wireframeMaterial = new THREE.MeshBasicMaterial({
                                color: object.material.color,
                                wireframe: true
                            });
                            object.material.dispose();
                            object.material = wireframeMaterial;
                        }
                    } else if (wireframeMode === 0 || wireframeMode === 1) {
                        // Mode 0: Normal or Mode 1: Wireframe with geometry
                        if (object.material.type !== 'MeshPhongMaterial' && !data.wireframe) {
                            // Replace with phong material
                            const phongMaterial = new THREE.MeshPhongMaterial({
                                color: object.material.color,
                                flatShading: renderSettings.flatShading,
                                vertexColors: data.vertex_colors ? true : false,
                                transparent: data.opacity < 1.0,
                                opacity: data.opacity,
                                shininess: 30
                            });
                            object.material.dispose();
                            object.material = phongMaterial;
                        } else if (object.material.type === 'MeshPhongMaterial') {
                            // Update flat shading
                            object.material.flatShading = renderSettings.flatShading;
                            object.material.needsUpdate = true;
                        }
                        
                        // Add wireframe overlay for Mode 1
                        if (wireframeMode === 1) {
                            const wireGeometry = new THREE.WireframeGeometry(object.geometry);
                            const wireframeHelper = new THREE.LineSegments(wireGeometry);
                            wireframeHelper.material.depthTest = true;
                            wireframeHelper.material.opacity = 0.0;
                            wireframeHelper.material.transparent = false;
                            wireframeHelper.material.color = new THREE.Color(0, 0, 0);
                            object.add(wireframeHelper);
                            object.userData.wireframeHelper = wireframeHelper;
                        }
                    }
                }
                
                // Handle normals visibility
                if (renderSettings.showNormals) {
                    if (!normalHelpers[id]) {
                        const normalHelper = new VertexNormalsHelper(object, 0.2, 0x00ff00, 1);
                        scene.add(normalHelper);
                        normalHelpers[id] = normalHelper;
                    }
                } else {
                    if (normalHelpers[id]) {
                        scene.remove(normalHelpers[id]);
                        if (normalHelpers[id].geometry) {
                            normalHelpers[id].geometry.dispose();
                        }
                        if (normalHelpers[id].material) {
                            normalHelpers[id].material.dispose();
                        }
                        delete normalHelpers[id];
                    }
                }
            }
        }
        
        gridHelper.visible = renderSettings.showGrid;
        axesHelper.visible = renderSettings.showAxes;
        return selectedObject;
    }
    
    function applyLightSettings(settings) {
        return;
        // Update internal light settings
        lightSettings = { ...settings };
        
        // Update ambient light
        if (lightSettings.ambientColor !== undefined && lightSettings.ambientIntensity !== undefined) {
            ambientLight.color.set(lightSettings.ambientColor);
            ambientLight.intensity = lightSettings.ambientIntensity;
        }
        
        // Update directional light
        if (lightSettings.directionalColor !== undefined && lightSettings.directionalIntensity !== undefined) {
            directionalLight.color.set(lightSettings.directionalColor);
            directionalLight.intensity = lightSettings.directionalIntensity;
        }
    }
    
    // Get the currently selected object
    function getSelectedObject() {
        return selectedObject;
    }
    
    // Get all objects in the scene
    function getAllObjects() {
        return Object.entries(objects).map(([id, obj]) => ({
            id,
            type: obj.type,
            visible: obj.object.visible,
            data: obj.data
        }));
    }

    // Allow external components to programmatically select/deselect an object
    function selectObject(id) {
        if (id === null) {
            selectedObject = null;
            if (typeof onSelectObject === 'function') {
                onSelectObject(null);
            }
            event_select_object(null);
            return;
        }
        const objData = objects[id];
        if (objData) {
            selectedObject = { ...objData };
            if (typeof onSelectObject === 'function') {
                onSelectObject(selectedObject);
            }
            event_select_object(id);
        }
    }
    
    // Toggle animated mesh playback method
    function toggleAnimatedMeshPlayback(objectId) {
        const objData = objects[objectId];
        if (objData && objData.type === 'animated_mesh') {
            const isCurrentlyPlaying = objData.animation.isPlaying;
            
            // Update local animation state
            objData.animation.isPlaying = !isCurrentlyPlaying;
            if (objData.animation.isPlaying) {
                objData.animation.startTime = Date.now() / 1000;
            } else {
                objData.animation.startTime = null;
            }
            
            // Update data for UI
            objData.data.is_playing = objData.animation.isPlaying;
        }
    }

    function event_select_object(id) {
        const payload = { selected_object: id };
        if (window.viewerId) payload.viewer_id = window.viewerId;
        console.log('Emitting events.selected_object with payload:', payload);
        socket.emit('events.select_object', payload);
    }
    
    return {
        update,
        onWindowResize,
        resetCamera,
        setBackgroundColor,
        clearAllObjects,
        dispose,
        applyRenderSettings,
        applyLightSettings,
        getSelectedObject,
        getAllObjects,
        selectObject,
        updateObject,
        toggleAnimatedMeshPlayback,
        renderer,
        scene,
        camera,
        controls
    };
}
