export default {
    root: ({ props }) => ({
        class: [
            //Size and Shape
            'w-96 rounded-md',

            // Positioning
            { '-translate-x-2/4': props.position == 'top-center' || props.position == 'bottom-center' }
        ]
    }),
    container: ({ props }) => ({
        class: [
            'my-4 rounded-md w-full',

            'shadow-lg',
            'bg-surface-0 dark:bg-surface-800',
            'ring-1 ring-inset ring-surface-200 dark:ring-surface-700 ring-offset-0',
            // Colors
            {
                'text-blue-500 dark:text-blue-300': props.message.severity == 'info',
                'text-green-500 dark:text-green-300': props.message.severity == 'success',
                'text-orange-500 dark:text-orange-300': props.message.severity == 'warn',
                'text-red-500 dark:text-red-300': props.message.severity == 'error'
            }
        ]
    }),
    content: ({ props }) => ({
        class: [
          'flex p-4',
          {
            'items-start': props.message.summary,
            'items-center': !props.message.summary,
          },
        ],
    }),
    icon: {
        class: [
            // Sizing and Spacing
            'w-5 h-5',
            'mr-2 shrink-0'
        ]
    },
    text: {
        class: [
            // Font and Text
            'text-sm leading-none',
            'ml-2',
            'flex-1'
        ]
    },
    summary: {
        class: 'font-medium block'
    },
    detail: ({ props }) => ({
        class: [
          'block',
          'text-surface-600 dark:text-surface-0/70',
          { 'mt-1.5': props.message.summary },
        ],
    }),
    closebutton: {
        class: [
            // Flexbox
            'flex items-center justify-center',

            // Size
            'w-6 h-6',

            // Spacing and Misc
            'ml-auto relative',

            // Shape
            'rounded-full',

            // Colors
            'bg-transparent',
            'text-surface-700 dark:text-surface-0/80',

            // Transitions
            'transition duration-200 ease-in-out',

            // States
            'hover:bg-surface-100 dark:hover:bg-surface-700',
            'outline-none focus:ring-1 focus:ring-inset',
            'focus:ring-primary-500 dark:focus:ring-primary-400',

            // Misc
            'overflow-hidden'
        ]
    },
    closeicon: {
        class: [
            // Sizing and Spacing
            'w-3 h-3',
            'shrink-0'
        ]
    },
    transition: {
        enterFromClass: 'opacity-0 translate-y-2/4',
        enterActiveClass: 'transition-[transform,opacity] duration-300',
        leaveFromClass: 'max-h-[1000px]',
        leaveActiveClass: '!transition-[max-height_.45s_cubic-bezier(0,1,0,1),opacity_.3s,margin-bottom_.3s] overflow-hidden',
        leaveToClass: 'max-h-0 opacity-0 mb-0'
    }
};
