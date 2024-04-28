export default {
    root: ({ props }) => ({
        class: [
            'relative',

            // Flexbox
            'flex',

            // Spacing
            'min-h-[4rem]',

            // Shape
            'rounded-md',
            'shadow-md',

            // Color
            'bg-surface-0 dark:bg-surface-900',
            'ring-1 ring-inset ring-surface-100 dark:ring-surface-800 ring-offset-0',

            { 'items-center px-2 sm:px-6': props.orientation == 'horizontal', 'flex-col justify-center sm:justify-start sm:w-48 px-2': props.orientation !== 'horizontal' }
        ]
    }),
    menu: ({ props }) => ({
        class: [
            // Flexbox
            'sm:flex sm:row-gap-2 sm:col-gap-4',
            'items-center',
            'flex-wrap',
            'flex-col sm:flex-row',
            { hidden: !props?.mobileActive, flex: props?.mobileActive },

            // Position
            'absolute sm:relative',
            'top-full left-0',
            'sm:top-auto sm:left-auto',

            // Size
            'w-full sm:w-auto',

            // Spacing
            'm-0 ',
            'py-2 px-1.5 sm:py-0 sm:p-0 sm:py-1.5',
            'list-none',

            // Shape
            'shadow-md sm:shadow-none',
            'border-0',
            'sm:rounded-none rounded-md',

            // Color
            'bg-surface-0 dark:bg-surface-900 sm:bg-transparent dark:sm:bg-transparent',

            // Misc
            'outline-none'
        ]
    }),
    menuitem: ({ props }) => ({
        class: [
            'sm:relative static',
            {
                'sm:w-auto w-full': props.horizontal,
                'w-full': !props.horizontal
            }
        ]
    }),
    content: ({ props, context }) => ({
        class: [
            // Shape
            { 'rounded-md': props.level < 1 },

            //  Colors
            {
                'text-surface-500 dark:text-white/70': !context.focused && !context.active,
                'text-surface-500 dark:text-white/70 bg-surface-200 dark:bg-black/70': context.focused && !context.active,
                'text-surface-900 dark:text-surface-0/80 bg-surface-50 dark:bg-black/70': context.focused && context.active,
                'text-surface-900 dark:text-surface-0/80 bg-surface-50 dark:bg-black/70': !context.focused && context.active
            },

            // Hover States
            {
                'hover:bg-surface-50 dark:hover:bg-surface-800': !context.active,
                'hover:bg-surface-100 dark:hover:bg-black/40 text-surface-900 dark:text-surface-0/80': context.active
            },

            // Transitions
            'transition-all',
            'duration-200'
        ]
    }),
    action: {
        class: [
            'relative',

            // Font
            'sm:text-sm font-medium',

            // Flexbox
            'flex',
            'items-center',

            // Spacing
            'py-2',
            'px-3',
            'my-1 sm:my-0',

            // Misc
            'select-none',
            'cursor-pointer',
            'no-underline ',
            'overflow-hidden'
        ]
    },
    icon: {
        class: 'mr-2'
    },
    submenuicon: ({ props }) => ({
        class: [
            {
                'ml-auto sm:ml-2': props.horizontal,
                'ml-auto': !props.horizontal
            }
        ]
    }),
    panel: ({ props }) => ({
        class: [
            // Size
            'w-auto',

            // Spacing
            'py-1',
            'm-0 mx-2',

            // Shape
            'shadow-none sm:shadow-md',
            'border-0',

            // Color
            'bg-surface-0 dark:bg-surface-900',

            // Position
            'static sm:absolute',
            'z-10',
            {
                'sm:left-full top-0': !props.horizontal
            }
        ]
    }),
    grid: {
        class: 'flex flex-wrap sm:flex-nowrap'
    },
    column: {
        class: 'w-full sm:w-1/2'
    },
    submenu: {
        class: ['m-0 list-none', 'py-1 px-2 w-full sm:min-w-[14rem]']
    },
    submenuheader: {
        class: [
            'font-medium',
            'sm:text-md',

            // Spacing
            'py-2.5 px-2',
            'm-0',

            // Shape
            'border-b border-surface-200 dark:border-surface-700',

            // Color
            'text-surface-700 dark:text-white/80',
            'bg-surface-0 dark:bg-surface-900'
        ]
    },
    separator: {
        class: 'border-t border-surface-200 dark:border-surface-600 my-1'
    },
    menubutton: {
        class: [
            // Flexbox
            'flex sm:hidden',
            'items-center justify-center',

            // Size
            'w-8',
            'h-8',

            // Shape
            'rounded-full',
            // Color
            'text-surface-500 dark:text-white/80',

            // States
            'hover:text-surface-600 dark:hover:text-white/60',
            'hover:bg-surface-50 dark:hover:bg-surface-800/80',
            'focus:outline-none focus:outline-offset-0',
            'focus:ring-2 focus:ring-inset focus:ring-primary-500 dark:focus:ring-primary-400',

            // Transitions
            'transition duration-200 ease-in-out',

            // Misc
            'cursor-pointer',
            'no-underline'
        ]
    },
    end: {
        class: 'ml-auto self-center'
    }
};
