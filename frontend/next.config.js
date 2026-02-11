/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    turbopack: {},
    images: {
        remotePatterns: [
            {
                protocol: "https",
                hostname: "media.api-sports.io",
            },
        ],
    },
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
