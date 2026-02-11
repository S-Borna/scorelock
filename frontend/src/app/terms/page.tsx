import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Användarvillkor — ScoreLock",
    description: "Villkor för användning av ScoreLock-plattformen.",
};

export default function TermsPage() {
    return (
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold mb-2">Användarvillkor</h1>
            <p className="text-gray-500 text-sm mb-8">Senast uppdaterad: 11 februari 2026</p>

            <div className="prose prose-invert prose-sm max-w-none space-y-6">
                <section>
                    <h2 className="text-xl font-semibold mb-3">1. Tjänsten</h2>
                    <p className="text-gray-400">
                        ScoreLock (&quot;tjänsten&quot;) är en AI-driven analysplattform för fotboll.
                        Vi erbjuder matchprediktioner, sentimentanalys, artiklar och
                        value-bet-identifiering. Tjänsten drivs av Said Borna.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">2. Inte spelrådgivning</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>
                            ScoreLock tillhandahåller <strong className="text-white">statistik och
                                analys</strong> — inte spelrådgivning. All information presenteras
                            i informationssyfte. Vi garanterar <strong className="text-white">inga
                                vinster</strong>.
                        </p>
                        <p>
                            Eventuella beslut om spel fattas helt och hållet av användaren.
                            ScoreLock ansvarar inte för ekonomiska förluster till följd av
                            användning av tjänsten.
                        </p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">3. Konto</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>Du måste vara minst <strong className="text-white">18 år</strong> för att skapa ett konto.</p>
                        <p>Du ansvarar för att hålla dina inloggningsuppgifter säkra.</p>
                        <p>Vi förbehåller oss rätten att stänga av konton som bryter mot dessa villkor.</p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">4. Prenumerationer & betalning</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>Free-planen är kostnadsfri. Pro och Elite kräver månatlig betalning via Stripe.</p>
                        <p>Prenumerationer förnyas automatiskt. Du kan avbryta när som helst via dina kontoinställningar.</p>
                        <p>Återbetalning sker enligt konsumentköplagen (14 dagars ångerrätt vid förstagångsköp).</p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">5. Affiliate-länkar</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>
                            Tjänsten innehåller <strong className="text-white">reklamlänkar</strong> till
                            licensierade bettingoperatörer. Dessa är tydligt märkta. ScoreLock kan
                            erhålla ersättning vid registrering via dessa länkar.
                        </p>
                        <p>
                            Alla länkade operatörer har licens från Spelinspektionen eller
                            motsvarande EU-tillsynsmyndighet.
                        </p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">6. AI-genererat innehåll</h2>
                    <p className="text-gray-400">
                        Artiklar, analyser och matchrapporter genereras av AI (LLM). Innehållet
                        granskas inte manuellt. Vi strävar efter hög kvalitet men kan inte garantera
                        att allt innehåll är korrekt vid alla tidpunkter.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">7. Immaterialrätt</h2>
                    <p className="text-gray-400">
                        Allt innehåll, design, och källkod ägs av ScoreLock. Dina tips och
                        prediktioner tillhör dig. Genom att använda tjänsten ger du oss rätt att
                        visa ditt visningsnamn och poäng på leaderboards.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">8. Ansvarsbegränsning</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>Tjänsten tillhandahålls &quot;i befintligt skick&quot;. Vi garanterar inte:</p>
                        <p>• Oavbruten tillgänglighet</p>
                        <p>• Korrektheten i prediktioner eller analyser</p>
                        <p>• Ekonomiska resultat baserade på vår information</p>
                        <p>
                            Vårt ansvar är begränsat till det belopp du betalat för tjänsten de
                            senaste 12 månaderna.
                        </p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">9. Ansvarigt spelande</h2>
                    <p className="text-gray-400">
                        Vi uppmuntrar ansvarigt spelande. Om du behöver hjälp, kontakta{" "}
                        <strong className="text-white">Stödlinjen: 020-819 100</strong> eller
                        besök{" "}
                        <a
                            href="https://www.spelpaus.se"
                            className="text-scorelock-400 hover:underline"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Spelpaus.se
                        </a>.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">10. Ändringar</h2>
                    <p className="text-gray-400">
                        Vi kan uppdatera dessa villkor. Väsentliga ändringar meddelas via
                        e-post minst 30 dagar i förväg. Fortsatt användning efter meddelande
                        innebär godkännande.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">11. Tillämplig lag</h2>
                    <p className="text-gray-400">
                        Dessa villkor regleras av svensk lag. Tvister avgörs av allmän
                        domstol i Sverige.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">12. Kontakt</h2>
                    <p className="text-gray-400">
                        Frågor om villkoren? Kontakta oss på{" "}
                        <a href="mailto:hello@scorelock.se" className="text-scorelock-400 hover:underline">
                            hello@scorelock.se
                        </a>
                    </p>
                </section>
            </div>
        </div>
    );
}
