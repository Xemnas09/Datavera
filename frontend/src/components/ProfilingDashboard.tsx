"use client";

import React, { useState } from "react";
import { DatasetProfile } from "@/lib/api";
import { DataTable } from "./DataTable";
import { FileSpreadsheet, BarChart2, Table as TableIcon, Layers, Info, AlertTriangle } from "lucide-react";

interface ProfilingDashboardProps {
  profile: DatasetProfile;
}

export const ProfilingDashboard: React.FC<ProfilingDashboardProps> = ({ profile }) => {
  const [activeTab, setActiveTab] = useState<"columns" | "sample">("columns");

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Octets";
    const k = 1024;
    const sizes = ["Octets", "Ko", "Mo", "Go"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const sampleColumns = profile.columns.map((c) => c.name);

  return (
    <div className="space-y-6">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 bg-sky-100 text-sky-700 rounded-xl">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium">Fichier</span>
            <p className="text-sm font-bold text-slate-900 truncate max-w-[120px] sm:max-w-[160px]">
              {profile.filename}
            </p>
            <span className="text-[10px] text-slate-400">{formatBytes(profile.file_size_bytes)}</span>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-100 text-indigo-700 rounded-xl">
            <BarChart2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium">Lignes</span>
            <p className="text-lg font-extrabold text-slate-900">
              {profile.row_count.toLocaleString("fr-FR")}
            </p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-xl">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium">Colonnes</span>
            <p className="text-lg font-extrabold text-slate-900">
              {profile.column_count}
            </p>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex items-center space-x-3">
          <div className="p-2.5 bg-amber-100 text-amber-700 rounded-xl">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-medium">Instance DuckDB</span>
            <p className="text-sm font-bold text-slate-900 truncate">
              {profile.table_name}
            </p>
            <span className="text-[10px] text-emerald-600 font-medium">● Connecté</span>
          </div>
        </div>
      </div>

      {/* Tabs Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-4">
        <div className="flex border-b border-slate-200 space-x-4">
          <button
            onClick={() => setActiveTab("columns")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "columns"
                ? "border-sky-600 text-sky-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Profilage des colonnes ({profile.columns.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("sample")}
            className={`pb-3 text-sm font-semibold flex items-center space-x-2 border-b-2 transition-colors ${
              activeTab === "sample"
                ? "border-sky-600 text-sky-600"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <TableIcon className="w-4 h-4" />
            <span>Aperçu des données ({profile.sample_rows.length} lignes)</span>
          </button>
        </div>

        {/* Tab 1: Column Profiling */}
        {activeTab === "columns" && (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm text-slate-700">
              <thead className="bg-slate-50 text-slate-800 font-bold uppercase text-[11px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3">Nom colonne</th>
                  <th className="px-4 py-3">Type DuckDB</th>
                  <th className="px-4 py-3">Valeurs nulles</th>
                  <th className="px-4 py-3">Valeurs uniques</th>
                  <th className="px-4 py-3">Échantillons</th>
                  <th className="px-4 py-3">Statistiques</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {profile.columns.map((col, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3 font-semibold text-slate-900">{col.name}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs font-mono">
                        {col.data_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {col.null_count > 0 ? (
                        <span className="inline-flex items-center text-amber-700 font-medium">
                          <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                          {col.null_count} ({col.null_percentage}%)
                        </span>
                      ) : (
                        <span className="text-slate-400">0 (0%)</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium">{col.unique_count}</td>
                    <td className="px-4 py-3 text-slate-500 max-w-xs truncate">
                      {col.sample_values.join(", ") || "-"}
                    </td>
                    <td className="px-4 py-3 text-xs space-y-0.5">
                      {col.stats ? (
                        <div className="grid grid-cols-2 gap-x-2 text-[11px]">
                          <div><span className="text-slate-400">Min:</span> {col.stats.min}</div>
                          <div><span className="text-slate-400">Max:</span> {col.stats.max}</div>
                          <div><span className="text-slate-400">Moy:</span> {col.stats.avg}</div>
                          <div><span className="text-slate-400">Méd:</span> {col.stats.median}</div>
                        </div>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 2: Sample Rows Preview */}
        {activeTab === "sample" && (
          <DataTable columns={sampleColumns} data={profile.sample_rows} pageSize={10} />
        )}
      </div>
    </div>
  );
};
