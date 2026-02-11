import Link from "next/link";
import type { Article } from "@/lib/types";
import { ARTICLE_TYPE_META, timeAgo } from "@/lib/utils";

interface ArticleCardProps {
    article: Article;
    featured?: boolean;
}

export function ArticleCard({ article, featured = false }: ArticleCardProps) {
    const meta = ARTICLE_TYPE_META[article.type] || {
        label: article.type,
        icon: "📄",
        color: "text-gray-400",
    };

    return (
        <Link
            href={`/articles/${article.slug}`}
            className={`card-interactive block group ${featured ? "md:col-span-2 lg:col-span-2" : ""}`}
        >
            {/* Type badge + time */}
            <div className="flex items-center justify-between mb-3">
                <span className={`badge bg-white/[0.04] border-white/[0.06] ${meta.color}`}>
                    {meta.icon} {meta.label}
                </span>
                {article.published_at && (
                    <span className="text-xs text-gray-500">
                        {timeAgo(article.published_at)}
                    </span>
                )}
            </div>

            {/* Title */}
            <h3
                className={`font-semibold text-white group-hover:text-scorelock-400 transition-colors duration-200 mb-2 leading-snug ${
                    featured ? "text-xl lg:text-2xl" : "text-base"
                }`}
            >
                {article.title}
            </h3>

            {/* Summary */}
            {article.summary && (
                <p className={`text-gray-400 text-sm leading-relaxed line-clamp-2 ${featured ? "line-clamp-3" : ""}`}>
                    {article.summary}
                </p>
            )}

            {/* Tags */}
            {article.tags && article.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-4">
                    {article.tags.slice(0, 4).map((tag) => (
                        <span
                            key={tag}
                            className="text-xs text-gray-500 bg-white/[0.03] px-2 py-0.5 rounded-md"
                        >
                            {tag}
                        </span>
                    ))}
                </div>
            )}
        </Link>
    );
}
