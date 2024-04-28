export default {
    listbutton: ({ props }) => ({
        class: [
            // Font
            'leading-none',

            // Flex Alignment
            'inline-flex items-center align-bottom text-center',

            // Shape
            'rounded-md rounded-r-none',

            // Spacing
            'px-2.5 py-1.5',

            // Color
            'ring-1 ring-surface-200 dark:ring-surface-700',
            props.modelValue === 'list' ? 'bg-surface-100 dark:bg-surface-700 text-surface-700 dark:text-surface-0' : 'bg-surface-0 dark:bg-surface-900 text-surface-700 dark:text-white/80',

            // States
            'focus:outline-none focus:outline-offset-0 focus:ring-primary-500 dark:focus:ring-primary-400',
            'hover:bg-surface-200 dark:hover:bg-surface-600/80',

            // Transition
            'transition duration-200',

            // Misc
            'cursor-pointer select-none overflow-hidden'
        ]
    }),
    gridbutton: ({ props }) => ({
        class: [
            // Font
            'leading-none',

            // Flex Alignment
            'inline-flex items-center align-bottom text-center',

            // Shape
            'rounded-md rounded-l-none',

            // Spacing
            'px-2.5 py-1.5',

            // Color
            'ring-1 ring-surface-200 dark:ring-surface-700',
            props.modelValue === 'grid' ? 'bg-surface-100 dark:bg-surface-700 text-surface-700 dark:text-surface-0' : 'bg-surface-0 dark:bg-surface-900 text-surface-700 dark:text-white/80',

            // States
            'focus:outline-none focus:outline-offset-0 focus:ring-primary-500 dark:focus:ring-primary-400',
            'hover:bg-surface-200 dark:hover:bg-surface-600/80',

            // Transition
            'transition duration-200',

            // Misc
            'cursor-pointer select-none overflow-hidden'
        ]
    })
};
