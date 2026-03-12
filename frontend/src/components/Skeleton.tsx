interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string
  height?: string
  animation?: 'pulse' | 'wave'
}

export default function Skeleton({
  className = '',
  variant = 'rectangular',
  width,
  height,
  animation = 'pulse',
}: SkeletonProps) {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700'
  
  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  }

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700',
  }

  const style: React.CSSProperties = {}
  if (width) style.width = width
  if (height) style.height = height

  return (
    <div
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${animationClasses[animation]}
        ${className}
      `}
      style={style}
      aria-label="로딩 중"
    />
  )
}

export function DocumentListSkeleton() {
  return (
    <div className="divide-y divide-gray-100 dark:divide-gray-800">
      {[1, 2, 3].map((i) => (
        <div key={i} className="px-4 md:px-6 py-4 md:py-5">
          <div className="flex items-center gap-3 md:gap-4">
            <Skeleton variant="rectangular" width="48px" height="48px" className="flex-shrink-0" />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" height="20px" width="60%" />
              <Skeleton variant="text" height="16px" width="40%" />
            </div>
            <Skeleton variant="rectangular" width="80px" height="36px" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function KnowledgeCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-start justify-between mb-3">
        <Skeleton variant="text" height="20px" width="70%" />
        <div className="flex gap-1">
          <Skeleton variant="rectangular" width="32px" height="32px" />
          <Skeleton variant="rectangular" width="32px" height="32px" />
        </div>
      </div>
      <div className="space-y-2 mb-3">
        <Skeleton variant="text" height="24px" width="40%" />
        <Skeleton variant="text" height="16px" width="30%" />
      </div>
      <div className="flex gap-2 mb-3">
        <Skeleton variant="rectangular" height="24px" width="60px" />
        <Skeleton variant="rectangular" height="24px" width="60px" />
      </div>
      <Skeleton variant="text" height="16px" width="50%" />
    </div>
  )
}

export function ConversationListSkeleton() {
  return (
    <div className="space-y-1">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="px-4 py-2.5">
          <div className="flex items-center gap-2">
            <Skeleton variant="rectangular" width="14px" height="14px" />
            <Skeleton variant="text" height="16px" className="flex-1" />
          </div>
        </div>
      ))}
    </div>
  )
}
