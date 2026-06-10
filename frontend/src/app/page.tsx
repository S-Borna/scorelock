import { HomeContent } from "@/components/home-content";
import { fetchApi } from "@/lib/api";
import type {
    Article,
    ArticleList,
    Fixture,
    MatchIntelligenceBundle,
    Prediction,
    ValueBet,
    WeeklyTopTipper,
} from "@/lib/types";

export const revalidate = 60;

const SWEDEN_NAME = "Sweden";

export default async function HomePage() {
    let articles: Article[] = [];
    let fixtures: Fixture[] = [];
    let allFixtures: Fixture[] = [];
    let predictions: Prediction[] = [];
    let valueBets: ValueBet[] = [];
    let weeklyTop: WeeklyTopTipper | null = null;

    const [articlesRes, scheduledRes, allFixturesRes, predictionsRes, valueBetsRes, weeklyTopRes] = await Promise.allSettled([
        fetchApi<ArticleList>("/api/v1/articles?limit=9"),
        fetchApi<Fixture[]>("/api/v1/fixtures?status=scheduled&limit=300"),
        fetchApi<Fixture[]>("/api/v1/fixtures?limit=300"),
        fetchApi<Prediction[]>("/api/v1/predictions/today?days_ahead=14"),
        fetchApi<ValueBet[]>("/api/v1/value-bets?min_edge=3"),
        fetchApi<WeeklyTopTipper | null>("/api/v1/tips/weekly-top"),
    ]);

    if (articlesRes.status === "fulfilled") articles = articlesRes.value.articles;
    if (scheduledRes.status === "fulfilled") fixtures = scheduledRes.value;
    if (allFixturesRes.status === "fulfilled") allFixtures = allFixturesRes.value;
    if (predictionsRes.status === "fulfilled") predictions = predictionsRes.value;
    if (valueBetsRes.status === "fulfilled") valueBets = valueBetsRes.value;
    if (weeklyTopRes.status === "fulfilled") weeklyTop = weeklyTopRes.value;

    // AI-showcase: hämta riktig analys för Sveriges nästa match (id via namn —
    // miljöoberoende). Misslyckas tyst → sektionen renderas inte.
    const nextSweden = allFixtures
        .filter(
            (f) =>
                (f.home_team.name === SWEDEN_NAME || f.away_team.name === SWEDEN_NAME) &&
                (f.status === "scheduled" || f.status === "live"),
        )
        .sort((a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime())[0] ?? null;

    let swedenIntelligence: MatchIntelligenceBundle | null = null;
    if (nextSweden) {
        try {
            swedenIntelligence = await fetchApi<MatchIntelligenceBundle>(
                `/api/v1/fixtures/${nextSweden.id}/intelligence`,
            );
        } catch {
            // showcase degraderar tyst
        }
    }

    return (
        <HomeContent
            articles={articles}
            fixtures={fixtures}
            allFixtures={allFixtures}
            predictions={predictions}
            valueBets={valueBets}
            weeklyTop={weeklyTop}
            swedenMatch={nextSweden}
            swedenIntelligence={swedenIntelligence}
        />
    );
}
