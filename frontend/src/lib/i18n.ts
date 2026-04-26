/**
 * ScoreLock i18n — lightweight translation system.
 *
 * Strategy: Swedish first (SEO niche), English toggle for global reach.
 * All keys are flat dot-notation strings.
 */

export type Locale = "sv" | "en";
export const DEFAULT_LOCALE: Locale = "sv";
export const LOCALES: Locale[] = ["sv", "en"];

const translations: Record<Locale, Record<string, string>> = {
    sv: {
        // ── Nav ──
        "nav.matches": "Matcher",
        "nav.valueBets": "Value Bets",
        "nav.standings": "Tabeller",
        "nav.predictions": "Prediktioner",
        "nav.articles": "Artiklar",
        "nav.sentiment": "Sentiment",
        "nav.tipping": "Tipsligan",
        "nav.login": "Logga in",
        "nav.signup": "Skapa konto",

        // ── Hero ──
        "hero.badge": "Driven av maskininlärning",
        "hero.title.prefix": "AI-driven",
        "hero.title.highlight": "fotbollsanalys",
        "hero.subtitle": "Livescore, prediktioner, value bets och matchanalyser — driven av maskininlärning, på svenska.",
        "hero.cta.primary": "Livescore & matcher",
        "hero.cta.secondary": "Value bets",

        // ── Sections ──
        "section.live": "Live nu",
        "section.allMatches": "Alla matcher →",
        "section.allMatchesShort": "Alla matcher",
        "section.valueBetsToday": "{count} value bets idag",
        "section.valueBetsDesc": "AI-identifierad edge mot oddsen",
        "section.seeAll": "Se alla →",
        "section.upcoming": "Kommande matcher",
        "section.upcomingDesc": "Med AI-prediktioner & value bets",
        "section.recentResults": "Senaste resultaten",
        "section.recentResultsDesc": "Avslutade matcher från ligan",
        "section.weeklyTipper": "Veckans tippare",
        "section.latestArticles": "Senaste artiklarna",
        "section.latestArticlesDesc": "AI-genererade analyser och matchreferat",
        "section.noArticles": "Inga artiklar publicerade ännu. Artiklar genereras automatiskt inför och efter matcher.",

        // ── Article filters ──
        "filter.all": "Alla",
        "filter.previews": "Analyser",
        "filter.reports": "Referat",
        "filter.valueBets": "Value Bets",

        // ── Features ──
        "features.title": "Varför ScoreLock?",
        "features.subtitle": "Avancerad AI-analys möter användarvänlig design",
        "features.live.title": "Livescore & matcher",
        "features.live.desc": "Liveresultat, kommande matcher och historik — med AI-prediktioner och value bets markerade inline.",
        "features.ml.title": "ML-prediktioner",
        "features.ml.desc": "XGBoost-modell tränad på 7 600+ matcher med kalibrerade sannolikheter för varje match.",
        "features.value.title": "Value Bet Finder",
        "features.value.desc": "Identifierar edge mellan modellens sannolikheter och bookmakerödds med Kelly Criterion.",

        // ── Footer ──
        "footer.desc": "AI-driven fotbollsanalys. Prediktioner, sentiment och value bets.",
        "footer.matches": "Matcher",
        "footer.livescore": "Livescore",
        "footer.analysis": "Analys",
        "footer.account": "Konto",
        "footer.legal": "Juridik",
        "footer.privacy": "Integritetspolicy",
        "footer.terms": "Användarvillkor",
        "footer.copyright": "© 2026 ScoreLock. Datadriven analysplattform — inte spelrådgivning. 18+.",
        "footer.responsible": "Spela ansvarsfullt · Stödlinjen: 020-819 100",

        // ── Common ──
        "common.aiGenerated": "AI-genererad",
        "common.draw": "Oavgjort",
        "common.tips": "tips",

        // ── Predictions page ──
        "predictions.title": "Dagens prediktioner",
        "predictions.desc": "ML-genererade matchprediktioner med kalibrerade sannolikheter.",
        "predictions.empty": "Inga prediktioner publicerade idag. Prediktioner genereras automatiskt varje morgon för dagens matcher.",

        // ── Matches page ──
        "matches.live": "Live",
        "matches.upcoming": "Kommande",
        "matches.finished": "Avslutade",

        // ── Metadata ──
        "meta.title": "ScoreLock — AI-driven fotbollsanalys",
        "meta.description": "AI-genererade förhandsanalyser, matchreferat, value bets och prediktioner för fotboll. Driven av maskininlärning.",

        // ── Broadcast (Phase 1: Where to Watch) ──
        "broadcast.title": "Var kan jag titta?",
        "broadcast.watch": "Titta nu",

        // ── Event timeline (Phase 2) ──
        "event.timeline_title": "Händelseförlopp",
        "event.assist_label": "ass.",
        "event.sub_in": "in",
        "event.sub_out": "ut",
        "event.empty": "Inga händelser registrerade",

        // ── Stats panel (Phase 3) ──
        "stats.title": "Statistik",
        "stats.possession": "Bollinnehav",
        "stats.shots_total": "Skott",
        "stats.shots_on_target": "På mål",
        "stats.corners": "Hörnor",
        "stats.fouls": "Frisparkar",
        "stats.offsides": "Offside",
        "stats.xg": "xG",
        "stats.passes": "Passningar",
        "stats.pass_accuracy": "Passprecision",
        "stats.tackles": "Tacklingar",

        // ── Lineups + pitch (Phase 4) ──
        "lineup.title": "Startelvor",
        "lineup.formation": "Formation",
        "lineup.coach": "Tränare",
        "lineup.substitutes": "Avbytare",
        "lineup.captain_short": "K",
        "lineup.empty": "Inga uppställningar registrerade",
    },
    en: {
        // ── Nav ──
        "nav.matches": "Matches",
        "nav.valueBets": "Value Bets",
        "nav.standings": "Standings",
        "nav.predictions": "Predictions",
        "nav.articles": "Articles",
        "nav.sentiment": "Sentiment",
        "nav.tipping": "Tipping League",
        "nav.login": "Sign in",
        "nav.signup": "Sign up",

        // ── Hero ──
        "hero.badge": "Powered by machine learning",
        "hero.title.prefix": "AI-powered",
        "hero.title.highlight": "football analytics",
        "hero.subtitle": "Live scores, predictions, value bets and match analysis — powered by machine learning.",
        "hero.cta.primary": "Live scores & matches",
        "hero.cta.secondary": "Value bets",

        // ── Sections ──
        "section.live": "Live now",
        "section.allMatches": "All matches →",
        "section.allMatchesShort": "All matches",
        "section.valueBetsToday": "{count} value bets today",
        "section.valueBetsDesc": "AI-identified edge against the odds",
        "section.seeAll": "See all →",
        "section.upcoming": "Upcoming matches",
        "section.upcomingDesc": "With AI predictions & value bets",
        "section.recentResults": "Recent results",
        "section.recentResultsDesc": "Finished league matches",
        "section.weeklyTipper": "Tipper of the week",
        "section.latestArticles": "Latest articles",
        "section.latestArticlesDesc": "AI-generated analyses and match reports",
        "section.noArticles": "No articles published yet. Articles are generated automatically before and after matches.",

        // ── Article filters ──
        "filter.all": "All",
        "filter.previews": "Previews",
        "filter.reports": "Reports",
        "filter.valueBets": "Value Bets",

        // ── Features ──
        "features.title": "Why ScoreLock?",
        "features.subtitle": "Advanced AI analytics meets intuitive design",
        "features.live.title": "Live scores & matches",
        "features.live.desc": "Live results, upcoming matches and history — with AI predictions and value bets highlighted inline.",
        "features.ml.title": "ML Predictions",
        "features.ml.desc": "XGBoost model trained on 7,600+ matches with calibrated probabilities for every match.",
        "features.value.title": "Value Bet Finder",
        "features.value.desc": "Identifies edge between the model probabilities and bookmaker odds using Kelly Criterion.",

        // ── Footer ──
        "footer.desc": "AI-powered football analytics. Predictions, sentiment and value bets.",
        "footer.matches": "Matches",
        "footer.livescore": "Live scores",
        "footer.analysis": "Analysis",
        "footer.account": "Account",
        "footer.legal": "Legal",
        "footer.privacy": "Privacy Policy",
        "footer.terms": "Terms of Service",
        "footer.copyright": "© 2026 ScoreLock. Data-driven analytics platform — not betting advice. 18+.",
        "footer.responsible": "Please gamble responsibly",

        // ── Common ──
        "common.aiGenerated": "AI-generated",
        "common.draw": "Draw",
        "common.tips": "tips",

        // ── Predictions page ──
        "predictions.title": "Today's predictions",
        "predictions.desc": "ML-generated match predictions with calibrated probabilities.",
        "predictions.empty": "No predictions published today. Predictions are generated automatically every morning for today's matches.",

        // ── Matches page ──
        "matches.live": "Live",
        "matches.upcoming": "Upcoming",
        "matches.finished": "Finished",

        // ── Metadata ──
        "meta.title": "ScoreLock — AI-powered football analytics",
        "meta.description": "AI-generated match previews, reports, value bets and predictions for football. Powered by machine learning.",

        // ── Broadcast (Phase 1: Where to Watch) ──
        "broadcast.title": "Where to watch",
        "broadcast.watch": "Watch now",

        // ── Event timeline (Phase 2) ──
        "event.timeline_title": "Match timeline",
        "event.assist_label": "ast",
        "event.sub_in": "in",
        "event.sub_out": "out",
        "event.empty": "No events recorded",

        // ── Stats panel (Phase 3) ──
        "stats.title": "Statistics",
        "stats.possession": "Possession",
        "stats.shots_total": "Shots",
        "stats.shots_on_target": "On target",
        "stats.corners": "Corners",
        "stats.fouls": "Fouls",
        "stats.offsides": "Offsides",
        "stats.xg": "xG",
        "stats.passes": "Passes",
        "stats.pass_accuracy": "Pass accuracy",
        "stats.tackles": "Tackles",

        // ── Lineups + pitch (Phase 4) ──
        "lineup.title": "Lineups",
        "lineup.formation": "Formation",
        "lineup.coach": "Coach",
        "lineup.substitutes": "Substitutes",
        "lineup.captain_short": "C",
        "lineup.empty": "No lineups registered",
    },
};

/**
 * Get a translated string. Supports {key} interpolation.
 */
export function t(locale: Locale, key: string, params?: Record<string, string | number>): string {
    let str = translations[locale]?.[key] ?? translations.sv[key] ?? key;
    if (params) {
        for (const [k, v] of Object.entries(params)) {
            str = str.replace(`{${k}}`, String(v));
        }
    }
    return str;
}
