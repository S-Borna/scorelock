import { PredictionBar } from "@/components/prediction-bar";
import { fetchApi } from "@/lib/api";
import type { FixtureDetail } from "@/lib/types";
import { formatKickoff, getStatusClass } from "@/lib/utils";
import { notFound } from "next/navigation";

interface PageProps {
  params: { id: string };
}

export default async function MatchDetailPage({ params }: PageProps) {
  let fixture: FixtureDetail;

  try {
    fixture = await fetchApi<FixtureDetail>(`/api/v1/fixtures/${params.id}`);
  } catch {
    notFound();
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-500">
            {fixture.league.name} · {fixture.round}
          </span>
          <span className={getStatusClass(fixture.status)}>
            {fixture.status.toUpperCase()}
          </span>
        </div>

        <div className="flex items-center justify-between py-6">
          <TeamDisplay
            name={fixture.home_team.name}
            logoUrl={fixture.home_team.logo_url}
          />
          <div className="text-center">
            {fixture.home_goals !== null && fixture.away_goals !== null ? (
              <div className="text-4xl font-bold font-mono">
                {fixture.home_goals} – {fixture.away_goals}
              </div>
            ) : (
              <div className="text-2xl text-gray-500">vs</div>
            )}
            <div className="text-xs text-gray-500 mt-2">
              {formatKickoff(fixture.kickoff)}
            </div>
          </div>
          <TeamDisplay
            name={fixture.away_team.name}
            logoUrl={fixture.away_team.logo_url}
          />
        </div>
      </div>

      {/* Prediction */}
      {fixture.prediction && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">🤖 ML Prediction</h2>
          <PredictionBar prediction={fixture.prediction} />
          <p className="text-xs text-gray-600 mt-3">
            Model: {fixture.prediction.model_version}
          </p>
        </div>
      )}

      {/* Odds */}
      {fixture.odds.length > 0 && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">📊 Odds</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 border-b border-gray-800">
                  <th className="text-left py-2">Bookmaker</th>
                  <th className="text-center py-2">Home</th>
                  <th className="text-center py-2">Draw</th>
                  <th className="text-center py-2">Away</th>
                </tr>
              </thead>
              <tbody>
                {fixture.odds
                  .filter((o) => o.market === "1X2")
                  .map((o, i) => (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-2">{o.bookmaker}</td>
                      <td className="text-center font-mono">
                        {o.home_odds?.toFixed(2)}
                      </td>
                      <td className="text-center font-mono">
                        {o.draw_odds?.toFixed(2)}
                      </td>
                      <td className="text-center font-mono">
                        {o.away_odds?.toFixed(2)}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Match Stats */}
      {fixture.stats && Object.keys(fixture.stats).length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">📈 Match Statistics</h2>
          <pre className="text-xs text-gray-400 overflow-auto">
            {JSON.stringify(fixture.stats, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function TeamDisplay({
  name,
  logoUrl,
}: {
  name: string;
  logoUrl: string | null;
}) {
  return (
    <div className="flex flex-col items-center gap-2 w-32">
      {logoUrl ? (
        <img src={logoUrl} alt={name} className="w-16 h-16 object-contain" />
      ) : (
        <div className="w-16 h-16 bg-gray-800 rounded-full" />
      )}
      <span className="text-sm font-medium text-center">{name}</span>
    </div>
  );
}
