export default function Loading() {
    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="h-9 w-56 bg-gray-800 rounded-lg animate-pulse mb-2" />
            <div className="h-5 w-80 bg-gray-800/60 rounded animate-pulse mb-8" />
            <div className="space-y-10">
                {Array.from({ length: 2 }).map((_, i) => (
                    <div key={i}>
                        <div className="h-6 w-40 bg-gray-800 rounded animate-pulse mb-4" />
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            {Array.from({ length: 3 }).map((_, j) => (
                                <div key={j} className="card animate-pulse">
                                    <div className="flex items-center gap-3 mb-3">
                                        <div className="w-8 h-8 bg-gray-800 rounded-full" />
                                        <div className="h-4 w-24 bg-gray-800 rounded" />
                                    </div>
                                    <div className="h-2 w-full bg-gray-800 rounded-full mb-3" />
                                    <div className="h-2 w-3/4 bg-gray-800 rounded-full" />
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
