"use client";

import React from "react";
import { Database, Sparkles, RefreshCw } from "lucide-react";

interface NavbarProps {
  datasetName?: string;
  rowCount?: number;
  onResetSession?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  datasetName,
  rowCount,
  onResetSession,
}) => {
  return (
    <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="bg-gradient-to-tr from-sky-600 to-indigo-600 p-2.5 rounded-xl shadow-md text-white">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xl tracking-tight text-slate-900">Datavera</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-sky-100 text-sky-800">
                <Sparkles className="w-3 h-3 mr-1" /> IA & DuckDB
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Analyse exploratoire de données en langage naturel
            </p>
          </div>
        </div>

        {datasetName && (
          <div className="flex items-center space-x-3">
            <div className="hidden md:flex flex-col text-right">
              <span className="text-sm font-medium text-slate-800 truncate max-w-[200px]">
                {datasetName}
              </span>
              <span className="text-xs text-slate-500">
                {rowCount?.toLocaleString("fr-FR")} lignes chargées
              </span>
            </div>

            {onResetSession && (
              <button
                onClick={onResetSession}
                className="inline-flex items-center px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                title="Changer de fichier / Réinitialiser la session"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
                Nouveau fichier
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
