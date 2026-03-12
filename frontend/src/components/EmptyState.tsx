import { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  iconClassName?: string
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  iconClassName = 'text-gray-400',
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 md:py-16 px-4 text-center animate-slide-up">
      <div className="w-16 h-16 md:w-20 md:h-20 bg-gray-50 dark:bg-gray-800 rounded-2xl md:rounded-3xl flex items-center justify-center mb-4 md:mb-6">
        <Icon className={`w-8 h-8 md:w-10 md:h-10 ${iconClassName}`} strokeWidth={1.5} />
      </div>
      <h3 className="text-lg md:text-xl font-bold text-[#191f28] dark:text-white mb-2" style={{ letterSpacing: '-0.02em' }}>
        {title}
      </h3>
      <p className="text-sm md:text-[15px] text-[#4e5968] dark:text-gray-400 leading-relaxed max-w-md mb-6">
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 active:bg-primary-700 transition-all font-bold shadow-sm hover:shadow-md active:scale-95 min-h-[44px]"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
