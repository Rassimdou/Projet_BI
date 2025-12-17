// ============================================================================
// CHART CONFIGURATION & THEME
// ============================================================================

const CHART_THEME = {
    colors: [
        '#6366F1', // Indigo 500
        '#EC4899', // Pink 500
        '#10B981', // Emerald 500
        '#F59E0B', // Amber 500
        '#8B5CF6', // Violet 500
        '#06B6D4', // Cyan 500
        '#F43F5E', // Rose 500
        '#84CC16', // Lime 500
        '#3B82F6', // Blue 500
        '#A855F7', // Purple 500
    ],
    font: {
        family: 'Inter, sans-serif',
        color: '#94a3b8' // Slate 400
    },
    grid: {
        color: '#334155' // Slate 700
    },
    background: 'rgba(0,0,0,0)' // Transparent
};

const COMMON_LAYOUT_OPTIONS = {
    plot_bgcolor: CHART_THEME.background,
    paper_bgcolor: CHART_THEME.background,
    font: CHART_THEME.font,
    margin: { l: 20, r: 20, t: 20, b: 40 },
    showlegend: false
};

// ... existing code ...
