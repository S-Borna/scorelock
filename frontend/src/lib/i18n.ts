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

        // ── Match intelligence (Phase 5) ──
        "intelligence.title": "AI-analys",
        "intelligence.pre_match": "Inför matchen",
        "intelligence.in_match": "Under matchen",
        "intelligence.post_match": "Efter matchen",
        "intelligence.minute_short": "min",
        "intelligence.model_label": "Modell",
        "intelligence.empty": "Ingen AI-analys publicerad ännu",

        // ── Fantasy / Tipsligan 2.0 (T1) ──
        "fantasy.title": "Tipsligan",
        "fantasy.subtitle": "Sätt ihop ditt drömlag, jämför mot AI:n, vinn mot vänner.",
        "fantasy.no_seasons": "Inga aktiva säsonger ännu",
        "fantasy.season.scope.demo": "Demo",
        "fantasy.season.scope.single_league": "Enkel liga",
        "fantasy.season.scope.cross_european": "Cross-Europa",
        "fantasy.season.scope.world_cup": "VM",
        "fantasy.season.budget": "Budget",
        "fantasy.season.gameweeks": "Omgångar",
        "fantasy.season.start_to_end": "Säsong",
        "fantasy.season.view_market": "Se spelarmarknad →",
        "fantasy.season.detail_title": "Säsongsöversikt",
        "fantasy.gameweek.label": "Omgång",
        "fantasy.gameweek.deadline": "Deadline",
        "fantasy.gameweek.kickoff_first": "Första avspark",
        "fantasy.gameweek.finalized": "Slutförd",
        "fantasy.gameweek.upcoming": "Kommande",
        "fantasy.gameweek.next_label": "Nästa omgång",
        "fantasy.market.title": "Spelarmarknad",
        "fantasy.market.filter_position": "Position",
        "fantasy.market.filter_max_price": "Max pris",
        "fantasy.market.sort.price_desc": "Pris (högst först)",
        "fantasy.market.sort.price_asc": "Pris (lägst först)",
        "fantasy.market.sort.points_desc": "Mest poäng",
        "fantasy.market.sort.ownership_desc": "Mest valda",
        "fantasy.market.position.GK": "Målvakt",
        "fantasy.market.position.DEF": "Försvar",
        "fantasy.market.position.MID": "Mittfält",
        "fantasy.market.position.FWD": "Anfall",
        "fantasy.market.position.all": "Alla",
        "fantasy.market.price": "Pris",
        "fantasy.market.points": "Poäng",
        "fantasy.market.ownership": "Valda av",
        "fantasy.market.empty": "Inga spelare matchar filtret",
        "fantasy.market.total_count": "spelare",
        "fantasy.budget_unit": "M",
        "fantasy.team.title": "Mitt lag",
        "fantasy.team.no_team": "Du har inget lag på denna säsong",
        "fantasy.team.create_cta": "Skapa lag",
        "fantasy.team.must_login": "Logga in för att se ditt lag",
        "fantasy.team.go_login": "Logga in →",
        "fantasy.team.captain_short": "K",
        "fantasy.team.vice_short": "V",
        "fantasy.team.bank": "I banken",
        "fantasy.team.squad_value": "Truppvärde",
        "fantasy.team.total_points": "Totalt poäng",
        "fantasy.team.free_transfers": "Fria byten",
        "fantasy.team.transfers_made": "Byten gjorda",
        "fantasy.team.formation": "Formation",
        "fantasy.team.starting_xi": "Startelva",
        "fantasy.team.bench": "Avbytarbänk",
        "fantasy.team.set_captain": "Sätt kapten",
        "fantasy.team.set_vice": "Sätt vice",
        "fantasy.team.captain_label": "Kapten",
        "fantasy.team.vice_label": "Vice-kapten",
        "fantasy.team.market_link": "Spelarmarknaden →",
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

        // ── Match intelligence (Phase 5) ──
        "intelligence.title": "AI analysis",
        "intelligence.pre_match": "Pre-match",
        "intelligence.in_match": "Live",
        "intelligence.post_match": "Post-match",
        "intelligence.minute_short": "min",
        "intelligence.model_label": "Model",
        "intelligence.empty": "No AI analysis published yet",

        // ── Fantasy / Tipsligan 2.0 (T1) ──
        "fantasy.title": "Fantasy League",
        "fantasy.subtitle": "Build your dream team, beat the AI, win against friends.",
        "fantasy.no_seasons": "No active seasons yet",
        "fantasy.season.scope.demo": "Demo",
        "fantasy.season.scope.single_league": "Single league",
        "fantasy.season.scope.cross_european": "Cross-European",
        "fantasy.season.scope.world_cup": "World Cup",
        "fantasy.season.budget": "Budget",
        "fantasy.season.gameweeks": "Gameweeks",
        "fantasy.season.start_to_end": "Season",
        "fantasy.season.view_market": "View player market →",
        "fantasy.season.detail_title": "Season overview",
        "fantasy.gameweek.label": "Gameweek",
        "fantasy.gameweek.deadline": "Deadline",
        "fantasy.gameweek.kickoff_first": "First kickoff",
        "fantasy.gameweek.finalized": "Finalized",
        "fantasy.gameweek.upcoming": "Upcoming",
        "fantasy.gameweek.next_label": "Next gameweek",
        "fantasy.market.title": "Player market",
        "fantasy.market.filter_position": "Position",
        "fantasy.market.filter_max_price": "Max price",
        "fantasy.market.sort.price_desc": "Price (high to low)",
        "fantasy.market.sort.price_asc": "Price (low to high)",
        "fantasy.market.sort.points_desc": "Most points",
        "fantasy.market.sort.ownership_desc": "Most owned",
        "fantasy.market.position.GK": "Goalkeeper",
        "fantasy.market.position.DEF": "Defender",
        "fantasy.market.position.MID": "Midfielder",
        "fantasy.market.position.FWD": "Forward",
        "fantasy.market.position.all": "All",
        "fantasy.market.price": "Price",
        "fantasy.market.points": "Points",
        "fantasy.market.ownership": "Owned by",
        "fantasy.market.empty": "No players match the filter",
        "fantasy.market.total_count": "players",
        "fantasy.budget_unit": "M",
        "fantasy.team.title": "My team",
        "fantasy.team.no_team": "You have no team this season",
        "fantasy.team.create_cta": "Create team",
        "fantasy.team.must_login": "Sign in to view your team",
        "fantasy.team.go_login": "Sign in →",
        "fantasy.team.captain_short": "C",
        "fantasy.team.vice_short": "V",
        "fantasy.team.bank": "In bank",
        "fantasy.team.squad_value": "Squad value",
        "fantasy.team.total_points": "Total points",
        "fantasy.team.free_transfers": "Free transfers",
        "fantasy.team.transfers_made": "Transfers made",
        "fantasy.team.formation": "Formation",
        "fantasy.team.starting_xi": "Starting XI",
        "fantasy.team.bench": "Bench",
        "fantasy.team.set_captain": "Set captain",
        "fantasy.team.set_vice": "Set vice",
        "fantasy.team.captain_label": "Captain",
        "fantasy.team.vice_label": "Vice-captain",
        "fantasy.team.market_link": "Player market →",
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
