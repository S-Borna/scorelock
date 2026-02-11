/**
 * Skeleton loader placeholder for loading states.
 */

export function Skeleton({ className = "" }: { className?: string }) {
    return (
        <div
            className={`animate-pulse bg-gray-800 rounded ${className}`}
        />
    );
}

export function ArticleCardSkeleton() {
    return (
        <div className="card space-y-3">
            <div className="flex items-center gap-2">
                <Skeleton className="w-16 h-5 rounded-full" />
                <Skeleton className="w-24 h-4" />
            </div>
            <Skeleton className="w-full h-6" />
            <Skeleton className="w-3/4 h-4" />
            <Skeleton className="w-1/2 h-4" />
            <div className="flex gap-2 pt-2">
                <Skeleton className="w-16 h-5 rounded-full" />
                <Skeleton className="w-16 h-5 rounded-full" />
            </div>
        </div>
    );
}

export function MatchCardSkeleton() {
    return (
        <div className="card space-y-3">
            <div className="flex justify-between">
                <Skeleton className="w-24 h-4" />
                <Skeleton className="w-16 h-5 rounded-full" />
            </div>
            <div className="space-y-2">
                <div className="flex justify-between">
                    <Skeleton className="w-32 h-5" />
                    <Skeleton className="w-6 h-5" />
                </div>
                <div className="flex justify-between">
                    <Skeleton className="w-28 h-5" />
                    <Skeleton className="w-6 h-5" />
                </div>
            </div>
            <Skeleton className="w-20 h-3" />
        </div>
    );
}

export function TableRowSkeleton({ cols = 6 }: { cols?: number }) {
    return (
        <tr>
            {Array.from({ length: cols }).map((_, i) => (
                <td key={i} className="px-4 py-3">
                    <Skeleton className="w-full h-4" />
                </td>
            ))}
        </tr>
    );
}
