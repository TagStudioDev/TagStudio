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
        class: 'overflow-hidden flex flex-auto cursor-pointer'
    },
    label: ({ props }) => ({
        class: [
            'block leading-5',

            props.display === 'chip' && props?.modelValue?.length > 0 ? 'py-1 px-3' : 'py-1.5 px-3',

            // Color
            { 'text-surface-800 dark:text-white/80': props.modelValue?.length, 'text-surface-400 dark:text-surface-500': !props.modelValue?.length },
            'placeholder:text-surface-400 dark:placeholder:text-surface-500',

            // Transitions
            'transition duration-200',

            // Misc
            'overflow-hidden whitespace-nowrap cursor-pointer overflow-ellipsis'
        ]
    }),
    token: {
        class: [
            // Flexbox
            'inline-flex items-center',

            // Spacing
            'py-0.5 px-3 mr-2',

            // Shape
            'rounded-[1.14rem]',

            // Colors
            'text-surface-700 dark:text-white/70',
            'bg-surface-200 dark:bg-surface-700'
        ]
    },
    removeTokenIcon: {
        class: [
            // Shape
            'rounded-md leading-6',

            // Spacing
            'ml-2',

            // Size
            'w-4 h-4',

            // Transition
            'transition duration-200 ease-in-out',

            // Misc
            'cursor-pointer'
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
    header: {
        class: [
            'flex items-center justify-between',
            // Spacing
            'py-2 px-4',
            'm-0',

            //Shape
            'border-b',
            'rounded-tl-md',
            'rounded-tr-md',

            // Color
            'text-surface-700 dark:text-white/80',
            'bg-surface-50 dark:bg-surface-800',
            'border-surface-200 dark:border-surface-700'
        ]
    },
    headerCheckboxContainer: {
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
    headerCheckbox: ({ context, state }) => ({
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
                'border-surface-300 bg-surface-0 dark:border-surface-700 dark:bg-surface-900': !context?.selected,
                'border-primary-500 bg-primary-500 dark:border-primary-400 dark:bg-primary-400': context?.selected
            },

            { 'outline-offset-0 ring-1 ring-primary-500 dark:ring-primary-400': state.focused }
        ]
    }),
    headerCheckbox: {
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
        box: ({ props, context }) => ({
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
        },
        icon: {
            class: [
                // Font
                'text-normal',

                // Size
                'w-3',
                'h-3',

                // Colors
                'text-white dark:text-surface-900',

                // Transitions
                'transition-all',
                'duration-200'
            ]
        }
    },
    itemCheckbox: {
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
        box: ({ props, context }) => ({
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
        },
        icon: {
            class: [
                // Font
                'text-normal',

                // Size
                'w-3',
                'h-3',

                // Colors
                'text-white dark:text-surface-900',

                // Transitions
                'transition-all',
                'duration-200'
            ]
        }
    },
    closeButton: {
        class: [
            'relative',

            // Flexbox and Alignment
            'flex items-center justify-center',

            // Size and Spacing
            'mr-2',
            'last:mr-0',
            'w-6 h-6',

            // Shape
            'border-0',
            'rounded-full',

            // Colors
            'text-surface-500',
            'bg-transparent',

            // Transitions
            'transition duration-200 ease-in-out',

            // States
            'hover:text-surface-700 dark:hover:text-white/80',
            'hover:bg-surface-100 dark:hover:bg-surface-800/80',
            'focus:outline-none focus:outline-offset-0 focus:ring-1 focus:ring-inset',
            'focus:ring-primary-500 dark:focus:ring-primary-400',

            // Misc
            'overflow-hidden'
        ]
    },
    closeButtonIcon: {
        class: [
            // Display
            'inline-block',

            // Size
            'w-3',
            'h-3'
        ]
    },
    wrapper: {
        class: [
            // Sizing
            'max-h-[15rem]',

            // Misc
            'overflow-auto'
        ]
    },
    list: {
        class: 'py-1 list-none m-0'
    },
    item: ({ context }) => ({
        class: [
            // Font
            'sm:text-sm',
            'leading-none',
            { 'font-normal': !context.selected, 'font-bold': context.selected },

            // Flexbox
            'flex items-center',

            // Position
            'relative',

            // Shape
            'border-0',
            'rounded-none',

            // Spacing
            'm-0',
            'py-2 px-4',

            // Color
            { 'text-surface-700 dark:text-white/80': !context.focused && !context.selected },
            { 'bg-surface-200 dark:bg-surface-600/60 text-surface-700 dark:text-white/80': context.focused && !context.selected },
            { 'bg-primary-500 dark:bg-primary-400 text-white dark:text-surface-700': context.focused && context.selected },
            { 'bg-transparent text-surface-700 dark:text-white/80': !context.focused && context.selected },

            //States
            'hover:bg-primary-500 dark:hover:bg-primary-400 hover:text-white dark:hover:text-surface-700',

            // Misc
            'cursor-pointer',
            'overflow-hidden',
            'whitespace-nowrap'
        ]
    }),
    itemgroup: {
        class: [
            //Font
            'font-bold',
            'sm:text-sm',

            // Spacing
            'm-0',
            'py-2 px-4',

            // Color
            'text-surface-800 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-600/80',

            // Misc
            'cursor-auto'
        ]
    },
    filtercontainer: {
        class: 'relative w-full mr-2'
    },
    filterinput: {
        class: [
            // Font
            'font-sans',
            'leading-none',
            'sm:text-sm',

            // Sizing
            'py-1.5 px-3',
            'pr-7',
            '-mr-7',
            'w-full',

            //Color
            'text-surface-700 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-900',
            'placeholder:text-surface-400',
            'ring-1 ring-inset ring-surface-300 dark:ring-surface-700',

            // Shape
            'border-0',
            'rounded-md',
            'appearance-none',

            // States
            'focus:ring-2 focus:ring-inset focus:outline-none focus:outline-offset-0',
            'focus:ring-primary-600 dark:focus:ring-primary-500',

            // Misc
            'appearance-none'
        ]
    },
    filtericon: {
        class: ['absolute', 'top-1/2 right-3', '-mt-2']
    },
    clearicon: {
        class: [
            // Color
            'text-surface-500',

            // Position
            'absolute',
            'top-1/2',
            'right-12',

            // Spacing
            '-mt-2'
        ]
    },
    emptymessage: {
        class: [
            // Font
            'leading-none',
            'sm:text-sm',

            // Spacing
            'py-2 px-4',

            // Color
            'text-surface-800 dark:text-white/80',
            'bg-transparent'
        ]
    },
    transition: {
        enterFromClass: 'opacity-0 scale-y-[0.8]',
        enterActiveClass: 'transition-[transform,opacity] duration-[120ms] ease-[cubic-bezier(0,0,0.2,1)]',
        leaveActiveClass: 'transition-opacity duration-100 ease-linear',
        leaveToClass: 'opacity-0'
    }
};
