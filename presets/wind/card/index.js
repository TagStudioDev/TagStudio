export default {
    root: {
        class: [
            //Shape
            'rounded-lg',
            'shadow-md',

            //Color
            'bg-surface-0 dark:bg-surface-900',
            'text-surface-700 dark:text-surface-0/80'
        ]
    },
    header: {
        class: ['border-b border-surface-200 dark:border-surface-700']
    },
    body: {
        class: 'py-5'
    },
    title: {
        class: 'text-lg font-medium mb-2 px-5 md:px-6'
    },
    subtitle: {
        class: [
            //Spacing
            'mb-1 px-5 md:px-6',

            //Color
            'text-surface-600 dark:text-surface-0/60'
        ]
    },
    content: {
        class: 'py-6 px-5 md:px-6'
    },
    footer: {
        class: ['px-5 md:px-6 pt-5 pb-0', 'border-t border-surface-200 dark:border-surface-700']
    }
};
