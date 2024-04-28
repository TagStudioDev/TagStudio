export default {
    root: ({ props, state }) => ({
        class: [
            // Display and Position
            'inline-flex',
            'relative',

            // Shape
            'rounded-md',
            'shadow-sm',

            // Color and Background
            'bg-surface-0 dark:bg-surface-900',

            // States
            { 'ring-1 ring-inset': !state.focused, 'ring-2 ring-inset ring-primary-500 dark:ring-primary-400': state.focused },

            { 'ring-surface-300 dark:ring-surface-600': !props.invalid && !state.focused },

            // Invalid State
            { 'ring-red-500 dark:ring-red-400': props.invalid && !state.focused },

            // Misc
            'cursor-default',
            'select-none',
            { 'opacity-60': props.disabled, 'pointer-events-none': props.disabled }
        ]
    }),
    labelContainer: {
        class: ['overflow-hidden flex flex-auto cursor-pointer']
    },
    label: {
        class: [
            'block leading-5',

            // Space
            'py-1.5 px-3',

            // Color
            'text-surface-800 dark:text-white/80',

            // Transition
            'transition duration-200',

            // Misc
            'overflow-hidden whitespace-nowrap cursor-pointer overflow-ellipsis'
        ]
    },
    trigger: {
        class: [
            //Font
            'sm:text-sm',

            // Flexbox
            'flex items-center justify-center',
            'shrink-0',

            // Color and Background
            'bg-transparent',
            'text-surface-500',

            // Size
            'w-12',

            // Shape
            'rounded-tr-md',
            'rounded-br-md'
        ]
    },
    panel: {
        class: [
            // Position
            'absolute top-0 left-0',
            'mt-2',

            // Shape
            'border-0',
            'rounded-md',
            'shadow-md',

            // Color
            'bg-surface-0 dark:bg-surface-800',
            'text-surface-800 dark:text-white/80',
            'ring-1 ring-inset ring-surface-300 dark:ring-surface-700'
        ]
    },
    wrapper: {
        class: [
            // Sizing
            'max-h-[200px]',

            // Misc
            'overflow-auto'
        ]
    },
    tree: {
        root: {
            class: [
                'relative',

                // Space
                'p-1.5'
            ]
        },
        wrapper: {
            class: ['overflow-auto']
        },
        container: {
            class: [
                // Spacing
                'm-0 p-0',

                // Misc
                'list-none overflow-auto'
            ]
        },
        node: {
            class: ['p-[2px]', 'rounded-md', 'focus:outline-none focus:outline-offset-0 focus:ring-2 focus:ring-inset focus:ring-primary-500 dark:focus:ring-primary-400']
        },
        content: ({ context, props }) => ({
            class: [
                // Flex and Alignment
                'flex items-center',

                // Shape
                'rounded-md',

                // Spacing
                'p-2',

                // Colors
                'text-surface-700 dark:text-surface-0',
                { 'bg-surface-100 text-primary-500 dark:bg-surface-300/10 dark:text-primary-400': context.selected },

                // States
                { 'hover:bg-surface-200 dark:hover:bg-surface-400/10': props.selectionMode == 'single' || props.selectionMode == 'multiple' },

                // Transition
                'transition-shadow duration-200',

                { 'cursor-pointer select-none': props.selectionMode == 'single' || props.selectionMode == 'multiple' }
            ]
        }),
        toggler: ({ context }) => ({
            class: [
                // Flex and Alignment
                'inline-flex items-center justify-center',

                // Shape
                'border-0 rounded-full',

                // Size and Spacing
                'mr-2',
                'w-6 h-6',

                // Spacing
                'mr-2',

                // Colors
                'text-surface-500',
                'bg-transparent',
                {
                    invisible: context.leaf
                },

                // States
                'hover:text-surface-700 dark:hover:text-white/80',
                'hover:bg-surface-100 dark:hover:bg-surface-800/80',
                'focus:outline-none focus:outline-offset-0 focus:ring-1 focus:ring-inset',
                'focus:ring-primary-500 dark:focus:ring-primary-400',

                // Transition
                'transition duration-200',

                // Misc
                'cursor-pointer select-none'
            ]
        }),
        togglericon: {
            class: [
                // Size
                'w-4 h-4',

                // Color
                'text-surface-500 dark:text-white/70'
            ]
        },
        nodeCheckbox: ({ props, context, instance }) => ({
            root: {
                class: [
                    'relative',

                    // Alignment
                    'inline-flex',
                    'align-bottom',

                    // Size
                    'w-4',
                    'h-4',

                    // Spacing
                    'mr-2',

                    // Misc
                    'cursor-default',
                    'select-none'
                ]
            },
            box: {
                class: [
                    // Alignment
                    'flex',
                    'items-center',
                    'justify-center',

                    // Size
                    'w-4',
                    'h-4',

                    // Shape
                    'rounded',
                    'border',

                    // Colors
                    'text-surface-600',
                    {
                        'border-surface-300 bg-surface-0 dark:border-surface-700 dark:bg-surface-900': !context.checked,
                        'border-primary-500 bg-primary-500 dark:border-primary-400 dark:bg-primary-400': context.checked
                    },

                    {
                        'ring-2 ring-primary-500 dark:ring-primary-400': !props.disabled && context.focused,
                        'cursor-default opacity-60': props.disabled
                    },

                    // States
                    {
                        'peer-focus-visible:ring-2 peer-focus-visible:ring-primary-500 dark:peer-focus-visible:ring-primary-400': !props.disabled,
                        'cursor-default opacity-60': props.disabled
                    },

                    // Transitions
                    'transition-colors',
                    'duration-200'
                ]
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
            },
            icon: {
                class: [
                    // Font
                    'text-normal',

                    // Size
                    'w-3',
                    'h-3',

                    // Colors
                    {
                        'text-white dark:text-surface-900': !instance.partialChecked,
                        'text-gray dark:text-white': instance.partialChecked
                    },

                    // Transitions
                    'transition-all',
                    'duration-200'
                ]
            }
        }),
        nodeicon: {
            class: [
                // Space
                'mr-2',

                // Color
                'text-surface-600 dark:text-white/70'
            ]
        },
        subgroup: {
            class: ['m-0 list-none p-0 pl-2 mt-1']
        },
        filtercontainer: {
            class: [
                'relative block',

                // Space
                'mb-2',

                // Size
                'w-full'
            ]
        },
        input: {
            class: [
                'relative',

                // Font
                'font-sans leading-6',
                'sm:text-sm',

                // Spacing
                'm-0',
                'py-1.5 px-3 pr-10',

                // Size
                'w-full',

                // Shape
                'rounded-md',

                // Colors
                'text-surface-900 dark:text-surface-0',
                'placeholder:text-surface-400 dark:placeholder:text-surface-500',
                'bg-surface-0 dark:bg-surface-900',
                'ring-1 ring-inset ring-surface-300 dark:ring-surface-700 ring-offset-0',

                // States
                'hover:border-primary-500 dark:hover:border-primary-400',
                'focus:outline-none focus:outline-offset-0 focus:ring-2 focus:ring-inset focus:ring-primary-500 dark:focus:ring-primary-400',

                // Transition & Misc
                'appearance-none',
                'transition-colors duration-200'
            ]
        },
        loadingicon: {
            class: ['text-surface-500 dark:text-surface-0/70', 'absolute top-[50%] right-[50%] -mt-2 -mr-2 animate-spin']
        },
        searchicon: {
            class: [
                // Position
                'absolute top-1/2 -mt-2 right-3',

                // Color
                'text-surface-600 dark:hover:text-white/70'
            ]
        }
    },
    transition: {
        enterFromClass: 'opacity-0 scale-y-[0.8]',
        enterActiveClass: 'transition-[transform,opacity] duration-[120ms] ease-[cubic-bezier(0,0,0.2,1)]',
        leaveActiveClass: 'transition-opacity duration-100 ease-linear',
        leaveToClass: 'opacity-0'
    }
};
