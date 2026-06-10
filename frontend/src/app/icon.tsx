import { ImageResponse } from "next/og";

/**
 * Favicon — genereras av Next vid build (löser 404 på /favicon.ico-fallback
 * genom att injicera <link rel="icon"> i alla sidor).
 */
export const size = { width: 64, height: 64 };
export const contentType = "image/png";

export default function Icon() {
    return new ImageResponse(
        (
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "linear-gradient(135deg, #064e3b 0%, #09090f 70%)",
                    borderRadius: 14,
                }}
            >
                <span
                    style={{
                        fontSize: 40,
                        fontWeight: 700,
                        color: "#09ce5f",
                        fontFamily: "serif",
                    }}
                >
                    S
                </span>
            </div>
        ),
        { ...size },
    );
}
