export default {
    root: {
        class: 'shadow-md rounded-lg'
    },
    header: ({ props }) => ({
        class: [
            // Alignments
            'flex items-center justify-between',

            // Colors
            'text-surface-700 dark:text-surface-0/80',
            'bg-surface-0 dark:bg-surface-900',
            'border-b border-surface-200 dark:border-surface-800',

            //Shape
            'rounded-tl-lg rounded-tr-lg',

            // Conditional Spacing
            { 'px-5 md:px-6 py-5': !props.toggleable, 'py-3 px-5 md:px-6': props.toggleable }
        ]
    }),
    title: {
        class: 'leading-none font-medium'
    },
    toggler: {
        class: [
            // Alignments
            'inline-flex items-center justify-center',

            // Sized
            'w-8 h-8',

            //Shape
            'border-0 rounded-full',

            //Color
            'bg-transparent',
            'text-surface-600 dark:text-surface-100/80',

            // States
            'hover:text-surface-900 dark:hover:text-surface-0/80',
            'hover:bg-surface-50 dark:hover:bg-surface-800/50',
            'focus:outline-none focus:outline-offset-0 focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-inset dark:focus-visible:ring-primary-500',

            // Transitions
            'transition duration-200 ease-in-out',

            // Misc
            'overflow-hidden relative no-underline'
        ]
    },
    togglerIcon: {
        class: 'inline-block'
    },
    content: {
        class: [
            // Spacing
            'py-6 px-5 md:px-6',

            // Shape
            'last:rounded-br-lg last:rounded-bl-lg',

            //Color
            'bg-surface-0 dark:bg-surface-900',
            'text-surface-700 dark:text-surface-0/80'
        ]
    },
    footer: {
        class: [
            // Spacing
            'py-6 px-5 md:px-6',

            //Shape
            'rounded-bl-lg rounded-br-lg',

            // Color
            'bg-surface-0 dark:bg-surface-900',
            'text-surface-600 dark:text-surface-0/70',
            'border-t border-surface-200 dark:border-surface-800'
        ]
    },
    transition: {
        enterFromClass: 'max-h-0',
        enterActiveClass: 'overflow-hidden transition-[max-height] duration-1000 ease-[cubic-bezier(0.42,0,0.58,1)]',
        enterToClass: 'max-h-[1000px]',
        leaveFromClass: 'max-h-[1000px]',
        leaveActiveClass: 'overflow-hidden transition-[max-height] duration-[450ms] ease-[cubic-bezier(0,1,0,1)]',
        leaveToClass: 'max-h-0'
    }
};
