export default {
    wrapper: {
        class: [
            // Size & Position
            'h-full w-full',

            // Layering
            'z-[1]',

            // Spacing
            'overflow-hidden',

            // Misc
            'relative float-left'
        ]
    },
    content: {
        class: [
            // Size & Spacing
            'h-[calc(100%+12px)] w-[calc(100%+12px)] pr-[12px] pb-[12px] pl-0 pt-0',

            // Overflow & Scrollbar
            'overflow-scroll scrollbar-none',

            // Box Model
            'box-border',

            // Position
            'relative',

            // Webkit Specific
            '[&::-webkit-scrollbar]:hidden'
        ]
    },
    barX: {
        class: [
            // Size & Position
            'h-[6px] bottom-0',

            // Appearance
            'bg-surface-100 dark:bg-surface-700 rounded',

            // Interactivity
            'cursor-pointer',

            // Visibility & Layering
            'invisible z-20',

            // Transition
            'transition duration-[250ms] ease-linear',

            // Misc
            'relative'
        ]
    },
    barY: {
        class: [
            // Size & Position
            'w-[6px] top-0',

            // Appearance
            'bg-surface-100 dark:bg-surface-700 rounded',

            // Interactivity
            'cursor-pointer',

            // Visibility & Layering
            'z-20',

            // Transition
            'transition duration-[250ms] ease-linear',

            // Misc
            'relative'
        ]
    }
};
