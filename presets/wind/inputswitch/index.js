export default {
    root: ({ props }) => ({
        class: [
            // Alignments
            'inline-flex relative',
            'shrink-0',

            // Shape
            'rounded-2xl',

            // Size
            'h-5 w-9',

            // States
            {
                'opacity-60 select-none pointer-events-none cursor-default': props.disabled
            }
        ]
    }),
    slider: ({ props }) => ({
        class: [
            // Position
            'absolute top-0 left-0 right-0 bottom-0',

            // Shape
            'rounded-2xl',

            // Before:
            'before:absolute before:top-1/2',
            'before:-mt-2',
            'before:h-4 before:w-4',
            'before:rounded-full',
            'before:duration-200 before:transition before:ease-in-out',
            'before:bg-surface-0 before:dark:bg-surface-900',
            'before:shadow',
            { 'before:transform before:translate-x-4': props.modelValue == props.trueValue },

            // Colors
            'border',
            {
                'bg-surface-200 dark:bg-surface-700': !(props.modelValue == props.trueValue),
                'bg-primary-500 dark:bg-primary-400': props.modelValue == props.trueValue
            },

            { 'border-transparent': !props.invalid },

            // Invalid State
            { 'border-red-500 dark:border-red-400': props.invalid },

            // States
            { 'peer-hover:bg-surface-300 dark:peer-hover:bg-surface-600 ': !(props.modelValue == props.trueValue) && !props.disabled },
            { 'peer-hover:bg-primary-600 dark:peer-hover:bg-surface-300 ': props.modelValue == props.trueValue && !props.disabled },
            'peer-focus-visible:ring-2 peer-focus-visible:ring-primary-500 dark:peer-focus-visible:ring-primary-400',

            // Transition
            'transition-colors duration-200',

            // Misc
            'cursor-pointer'
        ]
    }),
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
            'rounded',
            'border',

            // Shape
            'opacity-0',
            'rounded-md',
            'outline-none',
            'border-2 border-surface-300 dark:border-surface-700',

            // Misc
            'appearance-none'
        ]
    }
};
