import { ArticleCardSkeleton } from "@/components/skeleton";

export default function Loading() {
    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="h-9 w-64 bg-gray-800 rounded-lg animate-pulse mb-2" />
            <div className="h-5 w-96 bg-gray-800/60 rounded animate-pulse mb-8" />
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                    <ArticleCardSkeleton key={i} />
                ))}
            </div>
        </div>
    );
}
