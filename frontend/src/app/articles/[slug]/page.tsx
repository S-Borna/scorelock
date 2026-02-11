import { fetchApi } from "@/lib/api";
import type { Article, ArticleList, FixtureDetail } from "@/lib/types";
import { ARTICLE_TYPE_META, timeAgo } from "@/lib/utils";
import { ArticleCard } from "@/components/article-card";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import ReactMarkdown from "react-markdown";
import Link from "next/link";

interface PageProps {
    params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
    const { slug } = await params;
    try {
        const article = await fetchApi<Article>(`/api/v1/articles/${slug}`);
        return {
            title: article.title,
            description: article.summary || article.title,
            openGraph: {
                title: article.title,
                description: article.summary || article.title,
                type: "article",
                locale: "sv_SE",
                publishedTime: article.published_at || undefined,
            },
        };
    } catch {
        return { title: "Artikel" };
    }
}

export default async function ArticlePage({ params }: PageProps) {
    const { slug } = await params;
    let article: Article;

    try {
        article = await fetchApi<Article>(`/api/v1/articles/${slug}`);
    } catch {
        notFound();
    }

    const meta = ARTICLE_TYPE_META[article.type] || {
        label: article.type,
        icon: "📄",
        color: "text-gray-400",
    };

    // Fetch related fixture if present
    let fixture: FixtureDetail | null = null;
    if (article.fixture_id) {
        try {
            fixture = await fetchApi<FixtureDetail>(`/api/v1/fixtures/${article.fixture_id}`);
        } catch {
            // Not critical
        }
    }

    // Fetch related articles
    let related: Article[] = [];
    try {
        const res = await fetchApi<ArticleList>(
            `/api/v1/articles?article_type=${article.type}&limit=4`
        );
        related = res.articles.filter((a) => a.id !== article.id).slice(0, 3);
    } catch {
        // Not critical
    }

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Breadcrumb */}
            <nav className="text-sm text-gray-500 mb-6">
                <Link href="/" className="hover:text-gray-300">Hem</Link>
                <span className="mx-2">›</span>
                <span className={meta.color}>{meta.icon} {meta.label}</span>
            </nav>

            {/* Article header */}
            <header className="mb-8">
                <div className="flex items-center gap-3 mb-3">
                    <span className={`badge bg-gray-800 border border-gray-700 ${meta.color}`}>
                        {meta.icon} {meta.label}
                    </span>
                    {article.published_at && (
                        <span className="text-sm text-gray-500">
                            {timeAgo(article.published_at)}
                        </span>
                    )}
                    {article.auto_generated && (
                        <span className="badge bg-scorelock-900/30 text-scorelock-400 border border-scorelock-800 text-xs">
                            🤖 AI-genererad
                        </span>
                    )}
                </div>
                <h1 className="text-3xl sm:text-4xl font-bold leading-tight mb-4">
                    {article.title}
                </h1>
                {article.tags && article.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {article.tags.map((tag) => (
                            <span
                                key={tag}
                                className="text-xs text-gray-400 bg-gray-800 px-2.5 py-1 rounded-full"
                            >
                                {tag}
                            </span>
                        ))}
                    </div>
                )}
            </header>

            {/* Related match card */}
            {fixture && (
                <div className="card mb-8 flex items-center justify-between">
                    <Link
                        href={`/matches/${fixture.id}`}
                        className="flex items-center gap-4 hover:text-scorelock-400 transition-colors"
                    >
                        <span className="text-2xl">⚽</span>
                        <div>
                            <p className="font-semibold">
                                {fixture.home_team.name} vs {fixture.away_team.name}
                            </p>
                            <p className="text-sm text-gray-500">
                                {fixture.league.name} · {fixture.round}
                            </p>
                        </div>
                    </Link>
                    {fixture.home_goals !== null && fixture.away_goals !== null && (
                        <div className="text-2xl font-bold font-mono">
                            {fixture.home_goals} – {fixture.away_goals}
                        </div>
                    )}
                </div>
            )}

            {/* Article body (Markdown) */}
            <article className="prose prose-invert prose-scorelock max-w-none mb-12">
                <ReactMarkdown>{article.body}</ReactMarkdown>
            </article>

            {/* Value bet CTA */}
            {article.type === "VALUE_BET_ALERT" && (
                <div className="card border-green-900/50 bg-green-950/20 mb-8 text-center">
                    <p className="text-green-400 font-semibold mb-2">
                        💰 Fler value bets hittar du på Value Bets-sidan
                    </p>
                    <Link
                        href="/value-bets"
                        className="inline-block bg-green-700 hover:bg-green-600 text-white px-6 py-2 rounded-lg transition-colors text-sm"
                    >
                        Se alla Value Bets →
                    </Link>
                </div>
            )}

            {/* Related articles */}
            {related.length > 0 && (
                <section className="mt-12 pt-8 border-t border-gray-800">
                    <h2 className="text-xl font-semibold mb-6">Relaterade artiklar</h2>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                        {related.map((a) => (
                            <ArticleCard key={a.id} article={a} />
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}
