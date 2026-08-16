"use client";

import React, { useState } from "react";
import { UploadResponse, reconfigureIngestion } from "@/lib/api";
import { AlertTriangle, Check, FileSpreadsheet, Table, HelpCircle } from "lucide-react";

interface IngestionConfigModalProps {
  uploadData: UploadResponse;
  onConfigApplied: (newUploadData: UploadResponse) => void;
  onCancel: () => void;
}

export const IngestionConfigModal: React.FC<IngestionConfigModalProps> = ({
  uploadData,
  onConfigApplied,
  onCancel,
}) => {
  const [selectedSheet, setSelectedSheet] = useState<string>(
    uploadData.selected_sheet || (uploadData.available_sheets[0] || "")
  );
  const [selectedIndex, setSelectedIndex] = useState<number>(
    uploadData.detected_header_index
  );
  const [selectedDelimiter, setSelectedDelimiter] = useState<string>(",");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleApply = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const res = await reconfigureIngestion({
        sheet_name: selectedSheet || undefined,
        header_index: selectedIndex,
        delimiter: selectedDelimiter,
      });
      onConfigApplied(res);
    } catch (err: any) {
      setError(err.message || "Erreur de configuration.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-4xl w-full p-6 space-y-6 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-amber-100 text-amber-700 rounded-xl">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">
                Configuration de l'importation de fichier
              </h3>
              <p className="text-xs text-slate-500">
                L'analyse automatique requiert votre confirmation sur la feuille ou la ligne d'en-tête (confiance : {Math.round(uploadData.confidence_score * 100)}%).
              </p>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-red-50 text-red-700 border border-red-200 rounded-xl text-xs">
            {error}
          </div>
        )}

        {/* Configuration Options */}
        <div className="space-y-4 text-xs sm:text-sm">
          {/* Sheet Selector */}
          {uploadData.available_sheets.length > 1 && (
            <div className="space-y-1.5">
              <label className="font-semibold text-slate-800 flex items-center space-x-2">
                <FileSpreadsheet className="w-4 h-4 text-sky-600" />
                <span>Sélectionner la feuille Excel à analyser :</span>
              </label>
              <select
                value={selectedSheet}
                onChange={(e) => setSelectedSheet(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-xl bg-slate-50 text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {uploadData.available_sheets.map((s, idx) => (
                  <option key={idx} value={s}>
                    Feuille : {s}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Header Row Selector Prompt */}
          <div className="space-y-2">
            <label className="font-semibold text-slate-800 flex items-center space-x-2">
              <Table className="w-4 h-4 text-indigo-600" />
              <span>Cliquez sur la ligne contenant les noms de colonnes (en-têtes) :</span>
            </label>

            {/* Raw Preview Table */}
            <div className="border border-slate-200 rounded-xl overflow-x-auto max-h-60 bg-slate-50/50">
              <table className="w-full text-left text-xs text-slate-700 divide-y divide-slate-200">
                <tbody>
                  {uploadData.raw_preview_rows.map((row, rIdx) => {
                    const isSelected = rIdx === selectedIndex;
                    return (
                      <tr
                        key={rIdx}
                        onClick={() => setSelectedIndex(rIdx)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-sky-100/80 font-semibold text-sky-900 border-l-4 border-sky-600"
                            : "hover:bg-slate-100"
                        }`}
                      >
                        <td className="px-3 py-2 text-slate-400 font-mono text-[10px] w-12 text-center bg-slate-100">
                          Ligne {rIdx + 1}
                        </td>
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} className="px-3 py-2 max-w-xs truncate border-r border-slate-200">
                            {cell || <span className="text-slate-300 italic">vide</span>}
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-slate-500">
              Ligne {selectedIndex + 1} actuellement sélectionnée comme en-tête.
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
          <button
            onClick={onCancel}
            className="px-4 py-2.5 border border-slate-300 text-slate-700 hover:bg-slate-100 rounded-xl font-medium text-xs transition-colors"
          >
            Conserver la détection automatique
          </button>
          <button
            onClick={handleApply}
            disabled={submitting}
            className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-medium text-xs transition-all disabled:opacity-50 flex items-center space-x-2"
          >
            {submitting ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
            <span>Valider et appliquer l'analyse</span>
          </button>
        </div>
      </div>
    </div>
  );
};
