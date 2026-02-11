import { TableRowSkeleton } from "@/components/skeleton";

export default function Loading() {
    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="h-9 w-48 bg-gray-800 rounded-lg animate-pulse mb-8" />
            <div className="card overflow-hidden p-0">
                <div className="px-6 py-4 border-b border-gray-800">
                    <div className="h-6 w-40 bg-gray-800 rounded animate-pulse" />
                </div>
                <div className="px-4 py-2 space-y-1">
                    {Array.from({ length: 10 }).map((_, i) => (
                        <TableRowSkeleton key={i} />
                    ))}
                </div>
            </div>
        </div>
    );
}
