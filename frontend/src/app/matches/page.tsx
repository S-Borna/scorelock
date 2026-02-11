import { MatchCard } from "@/components/match-card";
import { fetchApi } from "@/lib/api";
import type { Fixture } from "@/lib/types";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Matcher",
    description: "Dagens och kommande fotbollsmatcher med ML-prediktioner inline.",
};

export const revalidate = 60;

export default async function MatchesPage() {
    let fixtures: Fixture[] = [];

    try {
        fixtures = await fetchApi<Fixture[]>("/api/v1/fixtures");
    } catch {
        // Handled in UI
    }

    const live = fixtures.filter((f) => f.status === "live" || f.status === "halftime");
    const scheduled = fixtures.filter((f) => f.status === "scheduled");
    const finished = fixtures.filter((f) => f.status === "finished");

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold mb-2">Matcher</h1>
            <p className="text-gray-500 mb-8">
                Live, kommande och avslutade matcher med prediktioner.
            </p>

            {live.length > 0 && (
                <Section title="🔴 Live">
                    {live.map((f) => (
                        <MatchCard key={f.id} fixture={f} />
                    ))}
                </Section>
            )}

            <Section title="Kommande">
                {scheduled.length > 0 ? (
                    scheduled.map((f) => <MatchCard key={f.id} fixture={f} />)
                ) : (
                    <p className="text-gray-500 col-span-full text-center py-8">
                        Inga kommande matcher just nu.
                    </p>
                )}
            </Section>

            <Section title="Avslutade">
                {finished.length > 0 ? (
                    finished.slice(0, 12).map((f) => <MatchCard key={f.id} fixture={f} />)
                ) : (
                    <p className="text-gray-500 col-span-full text-center py-8">
                        Inga avslutade matcher.
                    </p>
                )}
            </Section>
        </div>
    );
}

function Section({
    title,
    children,
}: {
    title: string;
    children: React.ReactNode;
}) {
    return (
        <section className="mb-10">
            <h2 className="text-xl font-semibold mb-4">{title}</h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{children}</div>
        </section>
    );
}
