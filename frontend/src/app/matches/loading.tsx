import { MatchCardSkeleton } from "@/components/skeleton";

export default function Loading() {
    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="h-9 w-48 bg-gray-800 rounded-lg animate-pulse mb-8" />
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                    <MatchCardSkeleton key={i} />
                ))}
            </div>
        </div>
    );
}
