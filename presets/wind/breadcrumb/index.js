export default {
    menu: {
        class: [
            // Flex & Alignment
            'flex items-center flex-nowrap gap-x-1.5',

            // Spacing
            'm-0 p-0 list-none leading-none'
        ]
    },
    action: {
        class: [
            // Font
            'font-semibold text-decoration-none text-sm',

            // Flex & Alignment
            'flex items-center gap-x-1.5 ',

            // Shape
            'rounded-md',

            // Color
            'text-surface-500 dark:text-white/70',

            // States
            'focus-visible:outline-none focus-visible:outline-offset-0',
            'focus-visible:ring-2 focus-visible:ring-primary-500 dark:focus-visible:ring-primary-400',

            // Transitions
            'transition-shadow duration-200'
        ]
    },
    icon: {
        class: 'text-surface-500 dark:text-white/70'
    },
    separator: {
        class: [
            // Flex & Alignment
            'flex items-center shrink-0',

            // Color
            'text-surface-500 dark:text-white/70'
        ]
    }
};
