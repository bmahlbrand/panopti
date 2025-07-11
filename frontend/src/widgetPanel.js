import React from 'react';

const WidgetPanel = ({
    showWidget,
    widgetId,
    widgetTitle,
    widgetContent,
    widgetPos,
    setWidgetPos,
    onMinimize,
    dragRef
}) => {
    if (!showWidget) return null;

    const handleWidgetMouseDown = (e) => {
        e.stopPropagation();
        dragRef.current = { x: e.clientX, y: e.clientY, start: widgetPos };
        document.addEventListener('mousemove', handleWidgetMouseMove);
        document.addEventListener('mouseup', handleWidgetMouseUp);
    };

    const handleWidgetMouseMove = (e) => {
        if (!dragRef.current) return;
        const dx = e.clientX - dragRef.current.x;
        const dy = e.clientY - dragRef.current.y;
        setWidgetPos({ x: dragRef.current.start.x + dx, y: dragRef.current.start.y + dy });
    };

    const handleWidgetMouseUp = () => {
        dragRef.current = null;
        document.removeEventListener('mousemove', handleWidgetMouseMove);
        document.removeEventListener('mouseup', handleWidgetMouseUp);
    };

    return React.createElement(
        'div',
        {
            className: 'widget-window',
            style: {
                left: widgetPos.x,
                top: widgetPos.y,
            },
        },
        React.createElement(
            'div',
            { className: 'widget-header', onMouseDown: handleWidgetMouseDown },
            React.createElement('span', null, widgetTitle),
            React.createElement('div', { className: 'widget-header-buttons' },
                React.createElement(
                    'button',
                    { 
                        className: 'widget-minimize', 
                        onClick: (e) => { 
                            e.stopPropagation(); 
                            onMinimize(widgetId); 
                        }, 
                        title: 'Minimize widget' 
                    },
                    '−'
                )
            ),
        ),
        React.createElement('div', { className: 'widget-content' }, widgetContent)
    );
};

export default WidgetPanel;
