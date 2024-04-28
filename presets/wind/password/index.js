export default {
    root: ({ props }) => ({
        class: [
            'inline-flex relative',
            {
                'opacity-60 select-none pointer-events-none cursor-default': props.disabled
            },
            { '[&>input]:pr-10': props.toggleMask }
        ]
    }),
    panel: {
        class: [
            // Spacing
            'p-3',

            // Shape
            'border-0 dark:border',
            'shadow-md rounded-md',

            // Colors
            'bg-surface-0 dark:bg-surface-900',
            'text-surface-700 dark:text-white/80',
            'dark:border-surface-700'
        ]
    },
    meter: {
        class: [
            // Position and Overflow
            'overflow-hidden',
            'relative',

            // Shape and Size
            'border-0',
            'h-2',
            'rounded-md',

            // Spacing
            'mb-2',

            // Colors
            'bg-surface-100 dark:bg-surface-700'
        ]
    },
    meterlabel: ({ instance }) => ({
        class: [
            // Size
            'h-full',

            // Colors
            {
                'bg-red-500 dark:bg-red-400/50': instance?.meter?.strength == 'weak',
                'bg-orange-500 dark:bg-orange-400/50': instance?.meter?.strength == 'medium',
                'bg-green-500 dark:bg-green-400/50': instance?.meter?.strength == 'strong'
            },

            // Transitions
            'transition-all duration-1000 ease-in-out'
        ]
    }),
    showicon: {
        class: ['absolute top-1/2 right-3 -mt-2 z-10', 'text-surface-600 dark:text-white/70']
    },
    hideicon: {
        class: ['absolute top-1/2 right-3 -mt-2 z-10', 'text-surface-600 dark:text-white/70']
    },
    input: {
        root: ({ props, context, parent }) => ({
            class: [
                // Font
                'font-sans leading-6',

                // Flex
                { 'flex-1 w-[1%]': parent.instance.$name == 'InputGroup' },

                // Spacing
                'm-0',
                {
                    'py-3 px-4 text-lg sm:text-md': props.size == 'large',
                    'py-1 px-2 sm:text-sm': props.size == 'small',
                    'py-1.5 px-3 sm:text-sm': props.size == null
                },
                'w-full',

                // Colors
                'text-surface-900 dark:text-surface-0',
                'placeholder:text-surface-400 dark:placeholder:text-surface-500',
                'bg-surface-0 dark:bg-surface-900',
                'shadow-sm',
                { 'ring-1 ring-inset ring-offset-0': parent.instance.$name !== 'InputGroup' },

                { 'ring-surface-300 dark:ring-surface-700': !parent.props.invalid },

                // Invalid State
                { 'ring-red-500 dark:ring-red-400': parent.props.invalid },

                // Shape
                { 'rounded-md': parent.instance.$name !== 'InputGroup' },
                { 'first:rounded-l-md rounded-none last:rounded-r-md': parent.instance.$name == 'InputGroup' },
                { 'border-0 border-y border-l last:border-r border-surface-300 dark:border-surface-600': parent.instance.$name == 'InputGroup' },
                { 'first:ml-0 -ml-px': parent.instance.$name == 'InputGroup' && !props.showButtons },
                'appearance-none',

                // Interactions
                {
                    'outline-none focus:ring-primary-500 dark:focus:ring-primary-400': !context.disabled,
                    'opacity-60 select-none pointer-events-none cursor-default': context.disabled
                }
            ]
        })
    },
    transition: {
        enterFromClass: 'opacity-0 scale-y-[0.8]',
        enterActiveClass: 'transition-[transform,opacity] duration-[120ms] ease-[cubic-bezier(0,0,0.2,1)]',
        leaveActiveClass: 'transition-opacity duration-100 ease-linear',
        leaveToClass: 'opacity-0'
    }
};
