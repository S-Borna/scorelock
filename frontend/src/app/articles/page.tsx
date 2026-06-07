import { fetchApi } from "@/lib/api";
import type { ArticleList } from "@/lib/types";
import { ArticleCard } from "@/components/article-card";
import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Artiklar — AI-genererad analys & VM-content",
    description: "Senaste artiklarna från ScoreLock: AI-genererade matchpreviews, value bets och VM-bevakning.",
};

export const revalidate = 60;

export default async function ArticlesPage() {
    let articles: ArticleList["articles"] = [];
    let total = 0;

    try {
        const res = await fetchApi<ArticleList>("/api/v1/articles?limit=20");
        articles = res.articles;
        total = res.total;
    } catch {
        // Tom-state visas nedan
    }

    return (
        <div className="container-main py-10">
            <header className="mb-10">
                <h1 className="font-display text-display-lg sm:text-display-xl leading-tight mb-3">
                    Artiklar
                </h1>
                <p className="text-gray-400 text-base sm:text-lg max-w-2xl">
                    AI-genererade matchpreviews, value bets och VM-bevakning. Uppdateras flera gånger om dagen.
                </p>
                {total > 0 && (
                    <p className="text-xs text-gray-500 mt-3">
                        {total} {total === 1 ? "artikel" : "artiklar"} publicerade
                    </p>
                )}
            </header>

            {articles.length === 0 ? (
                <div className="card text-center py-16">
                    <div className="text-4xl mb-4">📰</div>
                    <p className="text-gray-300 text-lg mb-2">
                        Inga artiklar publicerade ännu.
                    </p>
                    <p className="text-gray-500 text-sm">
                        AI-genererad VM-content kommer 9 juni.
                    </p>
                </div>
            ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {articles.map((article, idx) => (
                        <ArticleCard
                            key={article.id}
                            article={article}
                            featured={idx === 0}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
