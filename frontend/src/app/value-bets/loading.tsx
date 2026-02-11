export default function Loading() {
    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="h-9 w-48 bg-gray-800 rounded-lg animate-pulse mb-2" />
            <div className="h-5 w-80 bg-gray-800/60 rounded animate-pulse mb-8" />
            <div className="grid gap-4 lg:grid-cols-2">
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="card animate-pulse">
                        <div className="h-5 w-48 bg-gray-800 rounded mb-3" />
                        <div className="h-4 w-32 bg-gray-800/60 rounded mb-4" />
                        <div className="grid grid-cols-3 gap-4">
                            <div className="h-8 bg-gray-800 rounded" />
                            <div className="h-8 bg-gray-800 rounded" />
                            <div className="h-8 bg-gray-800 rounded" />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
