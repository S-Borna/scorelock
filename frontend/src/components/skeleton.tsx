/**
 * Skeleton loader placeholder for loading states.
 * Uses shimmer animation for premium feel.
 */

export function Skeleton({ className = "" }: { className?: string }) {
    return (
        <div className={`skeleton-shimmer ${className}`} />
    );
}

export function ArticleCardSkeleton() {
    return (
        <div className="card space-y-3">
            <div className="flex items-center gap-2">
                <Skeleton className="w-20 h-6 rounded-lg" />
                <Skeleton className="w-16 h-4 rounded-md" />
            </div>
            <Skeleton className="w-full h-6 rounded-md" />
            <Skeleton className="w-3/4 h-4 rounded-md" />
            <Skeleton className="w-1/2 h-4 rounded-md" />
            <div className="flex gap-2 pt-2">
                <Skeleton className="w-16 h-5 rounded-md" />
                <Skeleton className="w-16 h-5 rounded-md" />
            </div>
        </div>
    );
}

export function MatchCardSkeleton() {
    return (
        <div className="card space-y-3">
            <div className="flex justify-between">
                <Skeleton className="w-28 h-4 rounded-md" />
                <Skeleton className="w-14 h-6 rounded-lg" />
            </div>
            <div className="space-y-3">
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <Skeleton className="w-7 h-7 rounded-full" />
                        <Skeleton className="w-32 h-5 rounded-md" />
                    </div>
                    <Skeleton className="w-6 h-5 rounded-md" />
                </div>
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                        <Skeleton className="w-7 h-7 rounded-full" />
                        <Skeleton className="w-28 h-5 rounded-md" />
                    </div>
                    <Skeleton className="w-6 h-5 rounded-md" />
                </div>
            </div>
            <div className="pt-3 border-t border-white/[0.04]">
                <Skeleton className="w-24 h-3 rounded-md" />
            </div>
        </div>
    );
}

export function TableRowSkeleton({ cols = 6 }: { cols?: number }) {
    return (
        <tr>
            {Array.from({ length: cols }).map((_, i) => (
                <td key={i} className="px-4 py-3">
                    <Skeleton className="w-full h-4 rounded-md" />
                </td>
            ))}
        </tr>
    );
}
