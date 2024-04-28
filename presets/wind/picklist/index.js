export default {
    root: {
        class: [
            // Flexbox
            'flex lg:flex-row flex-col'
        ]
    },
    sourcecontrols: {
        class: [
            // Flexbox & Alignment
            'flex lg:flex-col justify-center gap-2',

            // Spacing
            'p-3'
        ]
    },
    sourcemoveupbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    sourcemovetopbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    sourcemovedownbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    sourcemovebottombutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    sourcewrapper: {
        class: 'grow shrink basis-2/4'
    },
    sourceheader: {
        class: [
            'font-semibold',

            // Shape
            'border-b rounded-t-md',

            // Spacing
            'py-3.5 px-3',

            // Color
            'text-surface-800 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-800',
            'border-surface-200 dark:border-surface-700 border-b'
        ]
    },
    sourcelist: {
        class: [
            // Spacing
            'list-none m-0 p-0',

            // Size
            'min-h-[12rem] max-h-[24rem]',

            // Shape
            'rounded-b-md border-0',

            // Color
            'text-surface-600 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-800',
            'border border-surface-200 dark:border-surface-700',

            // Spacing
            'py-3 px-0',

            // Focus & Outline
            'outline-none',

            // Misc
            'overflow-auto'
        ]
    },
    item: ({ context }) => ({
        class: [
            // Position
            'relative',

            // Spacing
            'py-3.5 px-3 m-0',

            // Shape
            'border-b last:border-b-0',

            // Transition
            'transition duration-200',

            // Color
            'text-surface-700 dark:text-white/80',
            'border-surface-200 dark:border-surface-700',
            { 'bg-surface-100 dark:bg-surface-600/30': context.active && !context.focused },
            { 'bg-surface-200 dark:bg-surface-500/30': context.active && context.focused },
            { 'bg-surface-50 dark:bg-surface-700/70': !context.active && context.focused },

            // State
            'hover:bg-surface-100 dark:hover:bg-surface-700',

            // Misc
            'cursor-pointer overflow-hidden'
        ]
    }),
    buttons: {
        class: 'flex lg:flex-col justify-center gap-2 p-3'
    },
    movetotargetbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    movealltotargetbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    movetosourcebutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    movealltosourcebutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    targetcontrols: {
        class: 'flex lg:flex-col justify-center gap-2 p-3'
    },
    targetmoveupbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    targetmovetopbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    targetmovedownbutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    targetmovebottombutton: {
        root: ({ context }) => ({
            class: [
                // Flexbox & Alignment
                'relative inline-flex items-center justify-center',

                // Shape
                'rounded-md',

                // Color
                'text-white dark:text-surface-900',
                'bg-primary-500 dark:bg-primary-400',
                'border border-primary-500 dark:border-primary-400',

                // Spacing & Size
                'text-sm',
                'w-8',
                'm-0',
                'px-2.5 py-1.5 min-w-[2rem]',
                'shadow-sm',

                // Transitions
                'transition duration-200 ease-in-out',

                // State
                'hover:bg-primary-600 dark:hover:bg-primary-300 hover:border-primary-600 dark:hover:border-primary-300',
                'focus:outline-none focus:outline-offset-0 focus:ring-2',
                'focus:ring-primary-500 dark:focus:ring-primary-400',
                { 'cursor-default pointer-events-none opacity-60': context.disabled },

                // Interactivity
                'cursor-pointer user-select-none'
            ]
        }),
        label: {
            class: [
                // Flexbox
                'flex-initial',

                // Size
                'w-0'
            ]
        }
    },
    targetwrapper: {
        class: 'grow shrink basis-2/4'
    },
    targetheader: {
        class: [
            'font-semibold',

            // Shape
            'border-b rounded-t-md',

            // Spacing
            'py-3.5 px-3',

            // Color
            'text-surface-800 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-800',
            'border-surface-200 dark:border-surface-700 border-b'
        ]
    },
    targetlist: {
        class: [
            // Spacing
            'list-none m-0 p-0',

            // Size
            'min-h-[12rem] max-h-[24rem]',

            // Shape
            'rounded-b-md border-0',

            // Color
            'text-surface-600 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-800',
            'border border-surface-200 dark:border-surface-700',

            // Spacing
            'py-3 px-0',

            // Focus & Outline
            'outline-none',

            // Misc
            'overflow-auto'
        ]
    },
    transition: {
        enterFromClass: '!transition-none',
        enterActiveClass: '!transition-none',
        leaveActiveClass: '!transition-none',
        leaveToClass: '!transition-none'
    }
};
