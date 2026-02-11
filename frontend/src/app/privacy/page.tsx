import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Integritetspolicy — ScoreLock",
    description: "ScoreLocks integritetspolicy. Så hanterar vi dina personuppgifter.",
};

export default function PrivacyPage() {
    return (
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
            <h1 className="text-display-md mb-2">Integritetspolicy</h1>
            <p className="text-gray-500 text-sm mb-8">Senast uppdaterad: 11 februari 2026</p>

            <div className="prose prose-invert prose-sm max-w-none space-y-6">
                <section>
                    <h2 className="text-xl font-semibold mb-3">1. Ansvarig</h2>
                    <p className="text-gray-400">
                        ScoreLock drivs av Said Borna (&quot;vi&quot;, &quot;oss&quot;). Vi är
                        personuppgiftsansvarig för behandlingen av dina personuppgifter i
                        enlighet med EU:s dataskyddsförordning (GDPR).
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">2. Vilka uppgifter samlar vi in?</h2>
                    <div className="text-gray-400 space-y-2">
                        <p><strong className="text-white">Kontoinformation:</strong> E-postadress och valfritt visningsnamn vid registrering.</p>
                        <p><strong className="text-white">Användningsdata:</strong> Tips, prediktioner, och leaderboard-poäng kopplade till ditt konto.</p>
                        <p><strong className="text-white">Affiliate-klick:</strong> SHA256-hashad IP-adress, user agent, tidpunkt. Vi lagrar aldrig din faktiska IP-adress.</p>
                        <p><strong className="text-white">Teknisk data:</strong> Anonymiserad felrapportering via Sentry (inga personuppgifter ingår).</p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">3. Varför behandlar vi dina uppgifter?</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>• <strong className="text-white">Tillhandahålla tjänsten:</strong> Login, sparade tips, leaderboard (rättslig grund: avtal).</p>
                        <p>• <strong className="text-white">Förbättra produkten:</strong> Anonymiserad feltrekning och prestandaövervakning (rättslig grund: berättigat intresse).</p>
                        <p>• <strong className="text-white">Affiliate-uppföljning:</strong> Aggregerad klickstatistik för att mäta intäkter (rättslig grund: berättigat intresse).</p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">4. Cookies</h2>
                    <p className="text-gray-400">
                        Vi använder <strong className="text-white">enbart nödvändiga cookies</strong> för
                        inloggningssession och cookiesamtycke. Inga tredjepartscookies, spårning eller
                        annonscookies.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">5. Delning med tredje part</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>Vi säljer <strong className="text-white">aldrig</strong> dina personuppgifter.</p>
                        <p>Data delas enbart med:</p>
                        <p>• <strong className="text-white">Sentry</strong> — anonymiserad felrapportering (EU-servrar)</p>
                        <p>• <strong className="text-white">Stripe</strong> — betalningsbehandling (PCI DSS-certifierat)</p>
                        <p>• <strong className="text-white">Railway/Vercel</strong> — hosting (USA, med standardavtalsklausuler)</p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">6. Lagring</h2>
                    <p className="text-gray-400">
                        Kontoinformation lagras så länge du har ett konto. Du kan när som helst
                        begära radering. Affiliate-klickdata anonymiseras och raderas efter 12 månader.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">7. Dina rättigheter</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>Enligt GDPR har du rätt att:</p>
                        <p>• Begära <strong className="text-white">tillgång</strong> till dina uppgifter</p>
                        <p>• Begära <strong className="text-white">rättelse</strong> av felaktiga uppgifter</p>
                        <p>• Begära <strong className="text-white">radering</strong> av ditt konto och alla uppgifter</p>
                        <p>• <strong className="text-white">Exportera</strong> dina uppgifter i maskinläsbart format</p>
                        <p>• <strong className="text-white">Invända</strong> mot behandling baserad på berättigat intresse</p>
                        <p>• Lämna klagomål till <strong className="text-white">Integritetsskyddsmyndigheten (IMY)</strong></p>
                    </div>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">8. Kontakt</h2>
                    <p className="text-gray-400">
                        Frågor om din integritet? Kontakta oss på{" "}
                        <a href="mailto:privacy@scorelock.se" className="text-scorelock-400 hover:underline">
                            privacy@scorelock.se
                        </a>
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-3">9. Ansvarigt spelande</h2>
                    <div className="text-gray-400 space-y-2">
                        <p>
                            ScoreLock erbjuder analys och statistik — <strong className="text-white">inte
                                spelrådgivning</strong>. Affiliate-länkar till bettingsidor är märkta med
                            &quot;Reklamlänk&quot; i enlighet med svensk marknadsföringslagstiftning.
                        </p>
                        <p>
                            Om du eller någon du känner har problem med spel, kontakta{" "}
                            <strong className="text-white">Stödlinjen: 020-819 100</strong> eller
                            besök <a href="https://www.spelpaus.se" className="text-scorelock-400 hover:underline" target="_blank" rel="noopener noreferrer">Spelpaus.se</a>.
                        </p>
                    </div>
                </section>
            </div>
        </div>
    );
}
