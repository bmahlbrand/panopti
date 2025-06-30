export function initTooltips() {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip-floating';
    document.body.appendChild(tooltip);

    function positionTooltip(target) {
        const text = target.getAttribute('data-tooltip');
        if (!text) return;
        tooltip.textContent = text;
        tooltip.classList.add('show');
        const rect = target.getBoundingClientRect();
        tooltip.style.left = '0px';
        tooltip.style.top = '0px';
        tooltip.style.display = 'block';
        const tipRect = tooltip.getBoundingClientRect();
        let left = rect.left + rect.width / 2 - tipRect.width / 2;
        let top = rect.top - tipRect.height - 8;
        const margin = 4;
        if (left < margin) left = margin;
        if (left + tipRect.width > window.innerWidth - margin) {
            left = window.innerWidth - margin - tipRect.width;
        }
        if (top < margin) {
            top = rect.bottom + 8;
            if (top + tipRect.height > window.innerHeight - margin) {
                top = window.innerHeight - margin - tipRect.height;
            }
        }
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    function hideTooltip() {
        tooltip.classList.remove('show');
        tooltip.style.display = 'none';
    }

    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('.tooltip[data-tooltip]');
        if (target) {
            positionTooltip(target);
        }
    });
    document.addEventListener('mouseout', (e) => {
        if (e.target.closest('.tooltip[data-tooltip]')) {
            hideTooltip();
        }
    });
}

