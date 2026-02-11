import { HomeContent } from "@/components/home-content";
import { fetchApi } from "@/lib/api";
import type { Article, ArticleList, Fixture, Prediction, ValueBet, WeeklyTopTipper } from "@/lib/types";

export const revalidate = 60;

export default async function HomePage() {
    let articles: Article[] = [];
    let fixtures: Fixture[] = [];
    let allFixtures: Fixture[] = [];
    let predictions: Prediction[] = [];
    let valueBets: ValueBet[] = [];
    let weeklyTop: WeeklyTopTipper | null = null;

    const [articlesRes, scheduledRes, allFixturesRes, predictionsRes, valueBetsRes, weeklyTopRes] = await Promise.allSettled([
        fetchApi<ArticleList>("/api/v1/articles?limit=9"),
        fetchApi<Fixture[]>("/api/v1/fixtures?status=scheduled"),
        fetchApi<Fixture[]>("/api/v1/fixtures"),
        fetchApi<Prediction[]>("/api/v1/predictions/today"),
        fetchApi<ValueBet[]>("/api/v1/value-bets?min_edge=3"),
        fetchApi<WeeklyTopTipper | null>("/api/v1/tips/weekly-top"),
    ]);

    if (articlesRes.status === "fulfilled") articles = articlesRes.value.articles;
    if (scheduledRes.status === "fulfilled") fixtures = scheduledRes.value;
    if (allFixturesRes.status === "fulfilled") allFixtures = allFixturesRes.value;
    if (predictionsRes.status === "fulfilled") predictions = predictionsRes.value;
    if (valueBetsRes.status === "fulfilled") valueBets = valueBetsRes.value;
    if (weeklyTopRes.status === "fulfilled") weeklyTop = weeklyTopRes.value;

    return (
        <HomeContent
            articles={articles}
            fixtures={fixtures}
            allFixtures={allFixtures}
            predictions={predictions}
            valueBets={valueBets}
            weeklyTop={weeklyTop}
        />
    );
}
