export default {
    listbutton: ({ props }) => ({
        class: [
            // Font
            'leading-none',

            // Flex Alignment
            'inline-flex items-center align-bottom text-center',

            // Shape
            'border rounded-md rounded-r-none',

            // Spacing
            'px-4 py-3',

            // Color
            props.modelValue === 'list'
                ? 'bg-primary-500 dark:bg-primary-400 border-primary-500 dark:border-primary-400 text-white dark:text-surface-900'
                : 'bg-surface-0 dark:bg-surface-900 border-surface-200 dark:border-surface-700 text-surface-700 dark:text-white/80',

            // States
            'focus:outline-none focus:outline-offset-0 focus:ring focus:ring-primary-400/50 dark:focus:ring-primary-300/50',
            props.modelValue === 'list' ? 'hover:bg-primary-600 dark:hover:bg-primary-300' : 'hover:bg-surface-50 dark:hover:bg-surface-800/80',

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
            'border rounded-md rounded-l-none',

            // Spacing
            'px-4 py-3',

            // Color
            props.modelValue === 'grid'
                ? 'bg-primary-500 dark:bg-primary-400 border-primary-500 dark:border-primary-400 text-white dark:text-surface-900'
                : 'bg-surface-0 dark:bg-surface-900 border-surface-200 dark:border-surface-700 text-surface-700 dark:text-white/80',

            // States
            'focus:outline-none focus:outline-offset-0 focus:ring focus:ring-primary-400/50 dark:focus:ring-primary-300/50',
            props.modelValue === 'grid' ? 'hover:bg-primary-600 dark:hover:bg-primary-300' : 'hover:bg-surface-50 dark:hover:bg-surface-800/80',

            // Transition
            'transition duration-200',

            // Misc
            'cursor-pointer select-none overflow-hidden'
        ]
    })
};
