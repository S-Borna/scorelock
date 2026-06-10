"use client";

import { useEffect, useRef } from "react";

/**
 * Scroll-reveal: barnen får .reveal-klassen och togglas till .in-view när de
 * når viewporten. CSS:en (globals.css) sköter transition — komponenten är bara
 * en lätt IntersectionObserver-ö. Respekterar prefers-reduced-motion via CSS.
 */
export function Reveal({
    children,
    className = "",
    delay = 0,
}: {
    children: React.ReactNode;
    className?: string;
    delay?: number;
}) {
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const io = new IntersectionObserver(
            (entries) => {
                for (const e of entries) {
                    if (e.isIntersecting) {
                        el.classList.add("in-view");
                        io.disconnect();
                        break;
                    }
                }
            },
            { threshold: 0.15, rootMargin: "0px 0px -40px 0px" },
        );
        io.observe(el);
        return () => io.disconnect();
    }, []);

    return (
        <div
            ref={ref}
            className={`reveal ${className}`}
            style={delay ? { transitionDelay: `${delay}ms` } : undefined}
        >
            {children}
        </div>
    );
}
