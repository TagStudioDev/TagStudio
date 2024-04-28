export default {
    root: ({ props }) => ({
        class: [
            // Position and Overflow
            'relative overflow-hidden',

            // Shape and Size
            'border-0',
            'rounded-md',
            { 'h-7 pt-5': props.mode !== 'indeterminate' && props.showValue },
            { 'h-2 bg-surface-100 dark:bg-surface-700 ': props.mode == 'indeterminate' || !props.showValue },

            // Before & After (!indeterminate)
            { 'before:absolute before:w-full before:rounded-md before:h-2 before:top-[1.25rem] before:left-0 before:bottom-0 before:bg-surface-100 dark:before:bg-surface-700': props.mode !== 'indeterminate' }
        ]
    }),
    value: ({ props }) => ({
        class: [
            // Flexbox & Overflow & Position
            { 'absolute flex items-center justify-center': props.mode !== 'indeterminate' },

            // Colors
            'bg-primary-500 dark:bg-primary-400',

            // Spacing & Sizing
            'm-0',
            { 'h-2 w-0': props.mode !== 'indeterminate' },

            // Shape
            'border-0 rounded-md',

            // Transitions
            {
                'transition-width duration-1000 ease-in-out': props.mode !== 'indeterminate',
                'progressbar-value-animate': props.mode == 'indeterminate'
            },

            // Before & After (indeterminate)
            {
                'before:absolute before:top-0 before:left-0 before:bottom-0 before:bg-inherit ': props.mode == 'indeterminate',
                'after:absolute after:top-0 after:left-0 after:bottom-0 after:bg-inherit after:delay-1000': props.mode == 'indeterminate'
            }
        ]
    }),
    label: {
        class: [
            // Flexbox
            'inline-flex justify-end',
            'absolute inset-0 mr-1 -top-[1.15rem]',

            // Font and Text
            'text-sm text-surface-600 dark:text-surface-0/60',
            'leading-none'
        ]
    }
};
