import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Datavera — Analyse de données IA & DuckDB",
  description: "Outil web d'analyse exploratoire de fichiers CSV et Excel en langage naturel, propulsé par DuckDB et l'IA.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="h-full bg-slate-50">
      <body className="h-full flex flex-col antialiased text-slate-900 selection:bg-sky-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
