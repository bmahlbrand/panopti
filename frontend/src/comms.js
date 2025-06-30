import { io } from 'socket.io-client';
import { marked } from 'marked';
import { cameraData } from './utils.js';

export function initComms(sceneManagerRef, { setIsLoading, setControls, setConsoleLines } = {}) {
    const opts = window.viewerId ? { query: { viewer_id: window.viewerId } } : {};
    const socket = io(opts);

    socket.on('connect', () => {
        if (window.viewerId) {
        socket.emit('register_viewer', { viewer_id: window.viewerId });
        }
        const req = {};
        if (window.viewerId) req.viewer_id = window.viewerId;
        socket.emit('request_state', req);
        if (setIsLoading) setTimeout(() => setIsLoading(false), 500);
    });

    socket.on('disconnect', () => {
        if (setIsLoading) setIsLoading(true);
    });

    socket.on('add_control', data => {
        setControls && setControls(prev => [...prev.filter(c => c.id !== data.id), data]);
    });

    socket.on('update_label', data => {
        setControls && setControls(prev => prev.map(c => c.id === data.id ? { ...c, text: marked.parse(data.text) } : c));
    });

    socket.on('delete_control', data => {
        setControls && setControls(prev => prev.filter(c => c.id !== data.id));
    });

    socket.on('console_output', data => {
        if (data.viewer_id && window.viewerId && data.viewer_id !== window.viewerId) return;
        setConsoleLines && setConsoleLines(prev => [...prev, data.text]);
    });

    // Handlers for simple state requests -- should follow "request_{eventName} pattern:
    const queryHandlers = {
        request_camera_info: () => {
            const cam = cameraData(sceneManagerRef.current.camera, sceneManagerRef.current.controls);
            return { data: cam };
        },
        request_selected_object: () => {
            const obj = sceneManagerRef.current.getSelectedObject();
            return { data: obj ? obj.data.id : null };
        }
    };
    Object.entries(queryHandlers).forEach(([reqEvent, handler]) => {
        const resEvent = reqEvent.replace('request_', '');
        console.log('registering query handler', reqEvent, '->', resEvent);
        socket.on(reqEvent, data => {
            console.log('received request for', reqEvent, 'with data', data);
            if (data.viewer_id && window.viewerId && data.viewer_id !== window.viewerId) return;
            if (!sceneManagerRef.current) return;
            // const payload = handler();
            const payload = { ...handler(), event: reqEvent };
            if (window.viewerId) payload.viewer_id = window.viewerId;
            console.log('emitting response for', reqEvent, '->', resEvent, payload);
            socket.emit(resEvent, payload);
        });
    });
    // ---------

    return socket;
}

