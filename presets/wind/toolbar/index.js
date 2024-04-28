export default {
    root: {
        class: [
            // Flex & Alignment
            'flex items-center justify-between flex-wrap',
            'gap-6',

            // Spacing
            'px-6 py-2',
            'min-h-[4rem]',

            // Shape
            'rounded-md',
            'shadow-md',

            // Color
            'bg-surface-0 dark:bg-surface-900',
            'ring-1 ring-surface-100 dark:ring-surface-700'
        ]
    },
    start: {
        class: 'flex items-center'
    },
    center: {
        class: 'flex items-center'
    },
    end: {
        class: 'flex items-center'
    }
};
