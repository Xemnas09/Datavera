"use client";

import React, { useState, useEffect, useRef } from "react";
import { Upload, FileSpreadsheet, Sparkles, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";
import { uploadFile, fetchSampleDatasets, loadSampleDataset, SampleDatasetInfo, DatasetProfile } from "@/lib/api";

interface UploadSectionProps {
  onProfileLoaded: (profile: DatasetProfile) => void;
}

export const UploadSection: React.FC<UploadSectionProps> = ({ onProfileLoaded }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [samples, setSamples] = useState<SampleDatasetInfo[]>([]);
  const [loadingSampleId, setLoadingSampleId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchSampleDatasets()
      .then(setSamples)
      .catch((err) => console.error("Erreur chargement échantillons", err));
  }, []);

  const handleFileSelect = async (file: File) => {
    setError(null);
    setLoading(true);
    setProgress(0);

    try {
      const res = await uploadFile(file, (p) => setProgress(p));
      onProfileLoaded(res.profile);
    } catch (err: any) {
      setError(err.message || "Erreur lors de l'importation du fichier.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSampleClick = async (sampleId: string) => {
    setError(null);
    setLoadingSampleId(sampleId);
    try {
      const res = await loadSampleDataset(sampleId);
      onProfileLoaded(res.profile);
    } catch (err: any) {
      setError(err.message || "Erreur lors du chargement du jeu d'essai.");
    } finally {
      setLoadingSampleId(null);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Title & Introduction */}
      <div className="text-center space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Analysez vos données en <span className="bg-clip-text text-transparent bg-gradient-to-r from-sky-600 to-indigo-600">langage naturel</span>
        </h1>
        <p className="text-slate-600 max-w-2xl mx-auto text-sm sm:text-base">
          Importez votre fichier CSV ou Excel (jusqu'à 150 Mo). Posez vos questions dans le chat, obtenez des requêtes DuckDB SQL transparentes et des graphiques interactifs.
        </p>
      </div>

      {/* Upload Drag & Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
          isDragging
            ? "border-sky-500 bg-sky-50/80 shadow-lg scale-[1.01]"
            : "border-slate-300 hover:border-sky-400 bg-white hover:bg-slate-50/50 shadow-sm"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.tsv,.xlsx,.xls"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />

        <div className="space-y-4">
          <div className="w-16 h-16 mx-auto bg-sky-100 rounded-2xl flex items-center justify-center text-sky-600 shadow-sm">
            <Upload className="w-8 h-8" />
          </div>

          <div>
            <p className="text-lg font-semibold text-slate-800">
              Déposez votre fichier ici, ou <span className="text-sky-600 hover:underline">parcourez vos fichiers</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Formats supportés : CSV, TSV, Excel (.xlsx, .xls) — jusqu'à 150 Mo
            </p>
          </div>

          {/* Progress Bar */}
          {loading && (
            <div className="max-w-md mx-auto space-y-2 pt-2">
              <div className="flex justify-between text-xs text-slate-600 font-medium">
                <span>Traitement du fichier et analyse DuckDB...</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
                <div
                  className="bg-sky-600 h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Error Message Alert */}
      {error && (
        <div className="flex items-center space-x-3 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Sample Datasets Section */}
      {samples.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-slate-200">
          <div className="flex items-center space-x-2 text-slate-800 font-semibold text-sm">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Pas de fichier sous la main ? Essayez un jeu de données exemple :</span>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            {samples.map((sample) => (
              <div
                key={sample.id}
                onClick={() => handleSampleClick(sample.id)}
                className="group border border-slate-200 rounded-xl p-4 bg-white hover:border-sky-300 hover:shadow-md transition-all cursor-pointer flex justify-between items-center"
              >
                <div className="space-y-1 pr-3">
                  <div className="flex items-center space-x-2">
                    <FileSpreadsheet className="w-4 h-4 text-sky-600" />
                    <span className="font-semibold text-slate-900 text-sm">{sample.title}</span>
                  </div>
                  <p className="text-xs text-slate-500">{sample.description}</p>
                </div>
                <button
                  disabled={loadingSampleId === sample.id}
                  className="p-2 bg-slate-100 group-hover:bg-sky-600 group-hover:text-white rounded-lg transition-colors text-slate-600 flex-shrink-0"
                >
                  {loadingSampleId === sample.id ? (
                    <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <ArrowRight className="w-4 h-4" />
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
