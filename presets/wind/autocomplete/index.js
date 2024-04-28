export default {
    root: ({ props }) => ({
        class: [
            'relative',

            // Flex
            'inline-flex',

            // Size
            { 'w-full': props.multiple },

            // Color
            'text-surface-900 dark:text-surface-0',

            //States
            {
                'opacity-60 select-none pointer-events-none cursor-default': props.disabled
            }
        ]
    }),
    container: ({ props, state }) => ({
        class: [
            // Font
            'font-sans sm:text-sm leading-none',

            // Flex
            'flex items-center flex-wrap',
            'gap-1',

            // Spacing
            'm-0 list-none',
            'px-3 py-1',
            { 'px-3 py-1.5': !props.multiple, 'px-3 py-1': props.multiple },
            // Size
            'w-full',

            // Shape
            'appearance-none rounded-md',

            // Color
            'text-surface-900 dark:text-surface-0',
            'bg-surface-0 dark:bg-surface-900',
            'placeholder:text-surface-400 dark:placeholder:text-surface-500',
            'shadow-sm',

            // States
            'focus:outline-none focus:outline-offset-0',
            // States
            { 'ring-1 ring-inset': !state.focused, 'ring-2 ring-inset ring-primary-500 dark:ring-primary-400': state.focused },

            { 'ring-surface-300 dark:ring-surface-600': !props.invalid && !state.focused },

            // Invalid State
            { 'ring-red-500 dark:ring-red-400': props.invalid && !state.focused },

            // Transition
            'transition duration-200 ease-in-out',

            // Misc
            'cursor-text overflow-hidden'
        ]
    }),
    inputtoken: ({ props }) => ({
        class: [{ 'py-1.5 px-0': !props.multiple, 'p-0.5': props.multiple }, , 'inline-flex flex-auto']
    }),
    input: ({ props }) => ({
        class: [
            // Font
            'font-sans sm:text-sm leading-none',

            // Shape
            'appearance-none rounded-md',
            { 'rounded-tr-none rounded-br-none': props.dropdown },
            { 'outline-none shadow-none rounded-none': props.multiple },

            // Size
            { 'w-full': props.multiple },

            // Spacing
            'm-0',
            { 'py-1.5 px-3': !props.multiple, 'p-0': props.multiple },

            // Colors
            'text-surface-700 dark:text-white/80',
            'border',
            {
                'bg-surface-0 dark:bg-surface-900': !props.multiple,
                'border-surface-300 dark:border-surface-700': !props.multiple && !props.invalid,
                'border-0 bg-transparent': props.multiple
            },

            // Invalid State
            { 'border-red-500 dark:border-red-400': props.invalid },

            // States
            { 'focus:outline-none focus:outline-offset-0 focus:ring-inset focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400': !props.multiple },

            // Transition
            'transition-colors duration-200'
        ]
    }),
    token: {
        class: [
            // Flexbox
            'inline-flex items-center',

            // Spacing
            'py-0.5 px-3',

            // Shape
            'rounded-[1.14rem]',

            // Colors
            'text-surface-700 dark:text-white/70',
            'bg-surface-200 dark:bg-surface-700'
        ]
    },
    label: {
        class: 'leading-5'
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
    dropdownbutton: {
        root: {
            class: [
                'relative text-sm leading-none',

                // Alignments
                'items-center inline-flex text-center align-bottom',

                // Shape
                'rounded-r-md',

                // Size
                'px-2.5 py-1.5',
                '-ml-px',

                // Colors
                'text-surface-600 dark:text-surface-100',
                'bg-surface-100 dark:bg-surface-800',
                'ring-1 ring-inset ring-surface-300 dark:ring-surface-700',

                // States
                'hover:bg-surface-200 dark:hover:bg-surface-700',
                'focus:outline-none focus:outline-offset-0 focus:ring-1',
                'focus:ring-primary-500 dark:focus:ring-primary-400'
            ]
        }
    },
    loadingicon: {
        class: ['text-sm leading-none text-surface-500 dark:text-surface-0/70', 'absolute top-[50%] right-[0.5rem] -mt-2 animate-spin']
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
            'max-h-[15rem]',
            'overflow-auto',

            // Color
            'bg-surface-0 dark:bg-surface-800',
            'text-surface-800 dark:text-white/80',
            'ring-1 ring-inset ring-surface-300 dark:ring-surface-700'
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
