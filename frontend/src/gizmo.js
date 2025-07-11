import * as THREE from 'three';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { throttle } from './utils.js';
import * as CONSTANTS from './constants.js';

export class Gizmo {
    constructor(scene, camera, renderer, orbitControls, socket) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        this.orbitControls = orbitControls;
        this.socket = socket;
        this.selectedObject = null;
        
        this.transformControls = new TransformControls(camera, renderer.domElement);
        this.transformControls.addEventListener('change', this.onTransformChange.bind(this));
        this.transformControls.addEventListener('dragging-changed', this.onDraggingChanged.bind(this));
        this.transformControls.addEventListener('objectChange', this.onObjectChange.bind(this));
        
        this.scene.add(this.transformControls);
        this.transformControls.visible = false;
        
        // State
        this.enabled = false;
        this.attachedObject = null;
        this.currentMode = 'translate'; // 'translate', 'rotate', 'scale'
        this.prevTransform = null; // Store transform state before dragging

        this.onUpdateCallback = null;
        this.onChangeCallback = null;

        this.throttledUpdate = throttle(this.emitUpdate.bind(this), CONSTANTS.DEBOUNCE_TRANSFORM);
        this.throttledGizmoEvent = throttle(this.emitGizmoEvent.bind(this), CONSTANTS.DEBOUNCE_TRANSFORM);
        this.setupKeyboardShortcuts();
    }
    
    setupKeyboardShortcuts() {
        // Handle keyboard shortcuts for mode switching
        this.keydownHandler = (event) => {
            if (!this.enabled || !this.attachedObject) return;
            
            switch (event.code) {
                case 'KeyE':
                    this.setMode('translate');
                    break;
                case 'KeyR':
                    this.setMode('rotate');
                    break;
                case 'KeyT':
                    this.setMode('scale');
                    break;
                case 'KeyQ':
                    // Toggle coordinate space (local/world)
                    this.transformControls.setSpace(
                        this.transformControls.space === 'local' ? 'world' : 'local'
                    );
                    break;
                case 'Escape':
                    this.detach();
                    break;
            }
        };
        
        // Snapping with Ctrl key
        this.keydownSnapHandler = (event) => {
            if (!this.enabled || !this.attachedObject) return;
            
            if (event.ctrlKey || event.metaKey) {
                this.transformControls.setTranslationSnap(1);
                this.transformControls.setRotationSnap(THREE.MathUtils.degToRad(15));
                this.transformControls.setScaleSnap(0.25);
            }
        };
        
        this.keyupSnapHandler = (event) => {
            if (!this.enabled || !this.attachedObject) return;
            
            if (!event.ctrlKey && !event.metaKey) {
                this.transformControls.setTranslationSnap(null);
                this.transformControls.setRotationSnap(null);
                this.transformControls.setScaleSnap(null);
            }
        };
        
        document.addEventListener('keydown', this.keydownHandler);
        document.addEventListener('keydown', this.keydownSnapHandler);
        document.addEventListener('keyup', this.keyupSnapHandler);
    }
    
    setEnabled(enabled) {
        this.enabled = enabled;
        this.transformControls.visible = enabled && this.attachedObject !== null;
        
        if (!enabled) {
            this.detach();
        }
    }
    
    isEnabled() {
        return this.enabled;
    }
    
    attach(object) {
        if (!this.enabled) return;
        this.attachedObject = object;
        this.transformControls.attach(object);
        this.transformControls.visible = true;
        this.transformControls.setMode(this.currentMode);
    }
    
    detach() {
        if (this.attachedObject) {
            this.transformControls.detach();
            this.attachedObject = null;
        }
        this.transformControls.visible = false;
    }
    
    setMode(mode) {
        if (['translate', 'rotate', 'scale'].includes(mode)) {
            this.currentMode = mode;
            if (this.attachedObject) {
                this.transformControls.setMode(mode);
            }
        }
    }
    
    getMode() {
        return this.currentMode;
    }
    
    setUpdateCallback(callback) {
        this.onUpdateCallback = callback;
    }
    
    setChangeCallback(callback) {
        this.onChangeCallback = callback;
    }
    
    onTransformChange() {
        if (this.onChangeCallback) {
            this.onChangeCallback();
        }
    }
    
    onDraggingChanged(event) {
        // Disable/enable orbit controls during dragging
        this.orbitControls.enabled = !event.value;
        
        if (event.value && this.attachedObject) {
            // Dragging started, capture previous transform state
            this.prevTransform = {
                position: this.attachedObject.position.toArray(),
                rotation: this.attachedObject.rotation.toArray().slice(0, 3),
                scale: this.attachedObject.scale.toArray()
            };
        } else if (!event.value && this.attachedObject) {
            // Dragging ended, emit final update
            this.emitUpdate();
            this.prevTransform = null;
        }
    }
    
    onObjectChange() {
        // Called when object transforms are applied
        if (this.attachedObject) {
            this.throttledUpdate();
            
            // Emit throttled gizmo event during dragging
            if (this.prevTransform && this.transformControls.dragging) {
                const currentTransform = {
                    position: this.attachedObject.position.toArray(),
                    rotation: this.attachedObject.rotation.toArray().slice(0, 3),
                    scale: this.attachedObject.scale.toArray()
                };
                this.throttledGizmoEvent('transform', this.prevTransform, currentTransform);
            }
        }
    }
    
    emitUpdate() {
        if (!this.attachedObject || !this.onUpdateCallback) return;
        
        const position = this.attachedObject.position.toArray();
        const rotation = this.attachedObject.rotation.toArray().slice(0, 3); // Remove order
        const scale = this.attachedObject.scale.toArray();
        
        this.onUpdateCallback({
            position,
            rotation,
            scale
        });
    }
    
    update() {
        if (this.transformControls) {
            this.transformControls.updateMatrixWorld();
        }
    }
    
    dispose() {
        document.removeEventListener('keydown', this.keydownHandler);
        document.removeEventListener('keydown', this.keydownSnapHandler);
        document.removeEventListener('keyup', this.keyupSnapHandler);
        
        this.detach();
        if (this.transformControls && this.scene) {
            this.scene.remove(this.transformControls);
        }
        
        if (this.transformControls) {
            this.transformControls.dispose();
        }
    }
    
    // Get the object currently attached to the gizmo
    getAttachedObject() {
        return this.attachedObject;
    }
    
    // Check if gizmo is currently being dragged
    isDragging() {
        return this.transformControls.dragging;
    }
    
    // Set coordinate space (world/local)
    setSpace(space) {
        this.transformControls.setSpace(space);
    }
    
    getSpace() {
        return this.transformControls.space;
    }
    
    // Set transform controls size
    setSize(size) {
        this.transformControls.setSize(size);
    }

    // Update the selected object reference
    setSelectedObject(selectedObject) {
        this.selectedObject = selectedObject;
    }

    emitGizmoEvent(eventType, prevTrans, trans) {
        if (!this.socket || !this.selectedObject) return;
        const payload = { gizmo: {
            object_name: this.selectedObject.data.id,
            object_type: this.selectedObject.data.type,
            trans: trans,
            prev_trans: prevTrans
        } }
        if (window.viewerId) payload.viewer_id = window.viewerId;
        this.socket.emit('events.gizmo', payload);
    }
}
