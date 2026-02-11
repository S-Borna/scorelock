"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { type Locale, DEFAULT_LOCALE, t as translate } from "@/lib/i18n";

interface LocaleContextType {
    locale: Locale;
    setLocale: (locale: Locale) => void;
    t: (key: string, params?: Record<string, string | number>) => string;
}

const LocaleContext = createContext<LocaleContextType>({
    locale: DEFAULT_LOCALE,
    setLocale: () => {},
    t: (key) => key,
});

export function LocaleProvider({ children }: { children: React.ReactNode }) {
    const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);

    useEffect(() => {
        const saved = localStorage.getItem("scorelock-locale") as Locale | null;
        if (saved === "en" || saved === "sv") {
            setLocaleState(saved);
            document.documentElement.lang = saved;
        }
    }, []);

    const setLocale = useCallback((newLocale: Locale) => {
        setLocaleState(newLocale);
        localStorage.setItem("scorelock-locale", newLocale);
        document.documentElement.lang = newLocale;
    }, []);

    const t = useCallback(
        (key: string, params?: Record<string, string | number>) => translate(locale, key, params),
        [locale]
    );

    return (
        <LocaleContext.Provider value={{ locale, setLocale, t }}>
            {children}
        </LocaleContext.Provider>
    );
}

export function useLocale() {
    return useContext(LocaleContext);
}
