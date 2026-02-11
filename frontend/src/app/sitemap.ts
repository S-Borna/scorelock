import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://scorelock.se";

export default function sitemap(): MetadataRoute.Sitemap {
    const now = new Date();

    return [
        {
            url: BASE_URL,
            lastModified: now,
            changeFrequency: "hourly",
            priority: 1,
        },
        {
            url: `${BASE_URL}/matches`,
            lastModified: now,
            changeFrequency: "hourly",
            priority: 0.9,
        },
        {
            url: `${BASE_URL}/predictions`,
            lastModified: now,
            changeFrequency: "daily",
            priority: 0.8,
        },
        {
            url: `${BASE_URL}/value-bets`,
            lastModified: now,
            changeFrequency: "daily",
            priority: 0.8,
        },
        {
            url: `${BASE_URL}/standings`,
            lastModified: now,
            changeFrequency: "daily",
            priority: 0.7,
        },
        {
            url: `${BASE_URL}/sentiment`,
            lastModified: now,
            changeFrequency: "daily",
            priority: 0.6,
        },
    ];
}
