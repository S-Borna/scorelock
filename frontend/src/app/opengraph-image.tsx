import { ImageResponse } from "next/og";

export const alt = "ScoreLock — VM 2026 · AI-driven fotbollsanalys";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Fraunces (site-wide display-serif) hämtas vid request-time. Failar hämtningen
// renderas bilden med default-typsnittet istället för att svara 500 — delningen
// får alltid en bild.
async function loadFraunces(): Promise<ArrayBuffer | null> {
    try {
        const css = await fetch(
            "https://fonts.googleapis.com/css2?family=Fraunces:wght@600&display=swap",
        ).then((res) => res.text());
        const match = css.match(/src: url\((.+?)\) format\('(?:opentype|truetype)'\)/);
        if (!match) return null;
        const font = await fetch(match[1]);
        if (!font.ok) return null;
        return font.arrayBuffer();
    } catch {
        return null;
    }
}

export default async function OpenGraphImage() {
    const fraunces = await loadFraunces();
    const serif = fraunces ? "Fraunces" : "Georgia, serif";

    return new ImageResponse(
        (
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    padding: "64px 72px",
                    backgroundColor: "#0b0f1a",
                    position: "relative",
                }}
            >
                {/* Sverige-glow: blå övre vänster → gul nedre höger */}
                <div
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "1200px",
                        height: "630px",
                        background:
                            "radial-gradient(720px 520px at 16% 4%, rgba(30, 64, 175, 0.50), transparent 68%)",
                    }}
                />
                <div
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "1200px",
                        height: "630px",
                        background:
                            "radial-gradient(640px 460px at 92% 100%, rgba(250, 204, 21, 0.20), transparent 66%)",
                    }}
                />
                {/* Tunn inre ram — editorial finish */}
                <div
                    style={{
                        position: "absolute",
                        top: 24,
                        left: 24,
                        right: 24,
                        bottom: 24,
                        border: "1px solid rgba(255, 255, 255, 0.08)",
                        borderRadius: 24,
                    }}
                />

                {/* Wordmark */}
                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                    <div
                        style={{
                            fontFamily: serif,
                            fontSize: 44,
                            fontWeight: 600,
                            color: "#edf0f7",
                            letterSpacing: "-0.02em",
                        }}
                    >
                        ScoreLock
                    </div>
                    <div
                        style={{
                            width: 12,
                            height: 12,
                            borderRadius: 12,
                            backgroundColor: "#facc15",
                            marginTop: 14,
                        }}
                    />
                </div>

                {/* Hero-ropet */}
                <div style={{ display: "flex", flexDirection: "column" }}>
                    <div
                        style={{
                            fontFamily: serif,
                            fontSize: 138,
                            fontWeight: 600,
                            lineHeight: 1,
                            letterSpacing: "-0.03em",
                            color: "#edf0f7",
                        }}
                    >
                        KOM IGEN
                    </div>
                    <div
                        style={{
                            fontFamily: serif,
                            fontSize: 138,
                            fontWeight: 600,
                            lineHeight: 1,
                            letterSpacing: "-0.03em",
                            color: "#fde047",
                        }}
                    >
                        SVERIGE
                    </div>
                </div>

                {/* Tagline */}
                <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                    <div
                        style={{
                            width: 48,
                            height: 2,
                            backgroundColor: "rgba(250, 204, 21, 0.6)",
                        }}
                    />
                    <div
                        style={{
                            fontSize: 26,
                            fontWeight: 500,
                            letterSpacing: "0.18em",
                            color: "rgba(237, 240, 247, 0.75)",
                        }}
                    >
                        VM 2026 · AI-DRIVEN FOTBOLLSANALYS
                    </div>
                </div>
            </div>
        ),
        {
            ...size,
            fonts: fraunces
                ? [{ name: "Fraunces", data: fraunces, style: "normal" as const, weight: 600 as const }]
                : undefined,
        },
    );
}
