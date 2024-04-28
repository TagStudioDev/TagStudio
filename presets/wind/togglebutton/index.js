export default {
    root: {
        class: [
            'relative',

            // Alignment
            'inline-flex',
            'align-bottom',

            // Misc
            'cursor-pointer',
            'select-none'
        ]
    },
    box: ({ props }) => ({
        class: [
            // Alignments
            'items-center inline-flex flex-1 text-center align-bottom justify-center',

            // Sizes & Spacing
            'px-2.5 py-1.5',
            'text-sm',

            // Shapes
            'rounded-md shadow-sm',

            // Colors
            'text-surface-700 dark:text-white/80',
            'ring-1',
            { 'ring-surface-200 dark:ring-surface-700': !props.invalid },
            {
                'bg-surface-0 dark:bg-surface-900 ': !props.modelValue,
                'bg-surface-100 dark:bg-surface-700': props.modelValue
            },

            // Invalid State
            { 'ring-red-500 dark:ring-red-400': props.invalid },

            // States
            'peer-hover:bg-surface-200 dark:peer-hover:bg-surface-600/80',
            {
                'peer-focus-visible:ring-2 peer-focus-visible:ring-inset peer-focus-visible:ring-primary-500 dark:peer-focus-visible:ring-primary-400': !props.disabled
            },

            // Transitions
            'transition-all duration-200',

            // Misc
            { 'cursor-pointer': !props.disabled, 'opacity-60 select-none pointer-events-none cursor-default': props.disabled }
        ]
    }),
    label: {
        class: 'font-semibold text-center w-full'
    },
    input: {
        class: [
            'peer',

            // Size
            'w-full ',
            'h-full',

            // Position
            'absolute',
            'top-0 left-0',
            'z-10',

            // Spacing
            'p-0',
            'm-0',

            // Shape
            'opacity-0',
            'rounded-md',
            'outline-none',
            'border border-surface-200 dark:border-surface-700',

            // Misc
            'appearance-none',
            'cursor-pointer'
        ]
    },
    icon: {
        class: [' mr-2', 'text-surface-700 dark:text-white/80']
    }
};
