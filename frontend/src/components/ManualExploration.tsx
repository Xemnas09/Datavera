"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  RefreshCw,
  Info,
  Sliders
} from "lucide-react";
import {
  DatasetProfile,
  ColumnClassification,
  ChartValidationResult,
  reclassifyColumn,
  exploreChart
} from "@/lib/api";
import { EChartViewer } from "./EChartViewer";

interface ManualExplorationProps {
  profile: DatasetProfile;
  onProfileUpdate?: (newProfile: DatasetProfile) => void;
}

const ALL_CHART_TYPES = [
  { id: "bar", label: "Histogramme (Barres)", icon: "📊", roles: [{ key: "x", label: "Catégorie (X)" }, { key: "y", label: "Valeur numérique (Y)" }] },
  { id: "bar_grouped", label: "Barres Groupées", icon: "📊", roles: [{ key: "x", label: "Axe principal (X)" }, { key: "y", label: "Valeur numérique (Y)" }, { key: "color", label: "Sous-groupe (Couleur)" }] },
  { id: "bar_stacked", label: "Barres Empilées", icon: "📊", roles: [{ key: "x", label: "Axe principal (X)" }, { key: "y", label: "Valeur numérique (Y)" }, { key: "color", label: "Sous-groupe (Couleur)" }] },
  { id: "bar_100pct", label: "Barres 100% Empilées", icon: "📊", roles: [{ key: "x", label: "Axe principal (X)" }, { key: "y", label: "Valeur numérique (Y)" }, { key: "color", label: "Sous-groupe (Couleur)" }] },
  { id: "bar_sorted", label: "Barres Triées", icon: "📊", roles: [{ key: "x", label: "Catégorie (X)" }, { key: "y", label: "Valeur numérique (Y)" }] },
  { id: "histogram", label: "Histogramme de Distribution", icon: "📈", roles: [{ key: "x", label: "Variable numérique" }] },
  { id: "box", label: "Boîte à Moustaches (Boxplot)", icon: "📦", roles: [{ key: "y", label: "Variable numérique (Y)" }, { key: "x", label: "Catégorie optionnelle (X)" }] },
  { id: "violin", label: "Graphique en Violon", icon: "🎻", roles: [{ key: "y", label: "Variable numérique (Y)" }, { key: "x", label: "Catégorie optionnelle (X)" }] },
  { id: "density", label: "Courbe de Densité", icon: "🌊", roles: [{ key: "x", label: "Variable numérique" }] },
  { id: "scatter", label: "Nuage de Points (Scatter)", icon: "🔮", roles: [{ key: "x", label: "Axe X (Numérique)" }, { key: "y", label: "Axe Y (Numérique)" }] },
  { id: "bubble", label: "Graphique à Bulles", icon: "🫧", roles: [{ key: "x", label: "Axe X (Numérique)" }, { key: "y", label: "Axe Y (Numérique)" }, { key: "size", label: "Taille bulle (Numérique)" }] },
  { id: "correlation_heatmap", label: "Matrice de Corrélation", icon: "🔥", roles: [{ key: "v1", label: "Variable 1" }, { key: "v2", label: "Variable 2" }] },
  { id: "line", label: "Courbe (Série Temporelle)", icon: "📈", roles: [{ key: "x", label: "Axe Temps / Ordinal (X)" }, { key: "y", label: "Valeur numérique (Y)" }] },
  { id: "area", label: "Graphique en Aire", icon: "🏔️", roles: [{ key: "x", label: "Axe Temps / Ordinal (X)" }, { key: "y", label: "Valeur numérique (Y)" }] },
  { id: "area_stacked", label: "Aire Empilée", icon: "⛰️", roles: [{ key: "x", label: "Axe Temps / Ordinal (X)" }, { key: "y", label: "Valeur numérique (Y)" }, { key: "color", label: "Sous-groupe (Couleur)" }] },
  { id: "pie", label: "Camembert (Pie)", icon: "🥧", roles: [{ key: "category", label: "Catégorie" }, { key: "value", label: "Valeur numérique" }] },
  { id: "donut", label: "Beignet (Donut)", icon: "🍩", roles: [{ key: "category", label: "Catégorie" }, { key: "value", label: "Valeur numérique" }] },
  { id: "treemap", label: "Carte Proportionnelle (Treemap)", icon: "🗺️", roles: [{ key: "category", label: "Catégorie" }, { key: "value", label: "Valeur numérique" }] },
];

export const ManualExploration: React.FC<ManualExplorationProps> = ({
  profile,
  onProfileUpdate,
}) => {
  const [classifications, setClassifications] = useState<Record<string, ColumnClassification>>(
    profile.classifications || {}
  );
  const [selectedChartType, setSelectedChartType] = useState<string>("bar");
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [chartOptions, setChartOptions] = useState<Record<string, any> | null>(null);
  const [validation, setValidation] = useState<ChartValidationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [reclassifyingCol, setReclassifyingCol] = useState<string | null>(null);

  const currentChartDef = ALL_CHART_TYPES.find((c) => c.id === selectedChartType) || ALL_CHART_TYPES[0];

  // Auto-initialize mapping on chart type change
  useEffect(() => {
    const newMapping: Record<string, string> = {};
    const cols = profile.columns.map((c) => c.name);

    currentChartDef.roles.forEach((role, idx) => {
      if (cols[idx]) {
        newMapping[role.key] = cols[idx];
      }
    });

    setMapping(newMapping);
  }, [selectedChartType, profile.columns]);

  // Request chart evaluation whenever chartType or mapping changes
  useEffect(() => {
    if (Object.keys(mapping).length > 0) {
      evaluateAndRenderChart();
    }
  }, [selectedChartType, mapping]);

  const evaluateAndRenderChart = async () => {
    setLoading(true);
    try {
      const res = await exploreChart(selectedChartType, mapping);
      setValidation(res.validation);
      setChartOptions(res.chart_options || null);
    } catch (err) {
      console.error("Error generating chart:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleReclassify = async (colName: string, targetType: string) => {
    setReclassifyingCol(colName);
    try {
      const updatedCls = await reclassifyColumn(colName, targetType);
      const newClsDict = { ...classifications, [colName]: updatedCls };
      setClassifications(newClsDict);

      if (onProfileUpdate) {
        const updatedCols = profile.columns.map((c) =>
          c.name === colName ? { ...c, classification: updatedCls } : c
        );
        onProfileUpdate({
          ...profile,
          columns: updatedCols,
          classifications: newClsDict,
        });
      }

      // Re-evaluate chart
      evaluateAndRenderChart();
    } catch (err: any) {
      alert(err.message || "Erreur de reclassification");
    } finally {
      setReclassifyingCol(null);
    }
  };

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case "numeric":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "categorical":
        return "bg-sky-50 text-sky-700 border-sky-200";
      case "identifier":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "datetime":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-slate-50 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="space-y-8">
      {/* 1. Column Classification Dashboard */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sliders className="w-5 h-5 text-brand-600" />
              Classification des Colonnes & Audit de Confiance
            </h3>
            <p className="text-sm text-slate-500">
              Détection automatique des rôles statistiques (numérique, catégorielle, identifiant, date).
              Vous pouvez reclassifier manuellement chaque colonne si nécessaire.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profile.columns.map((col) => {
            const cls = classifications[col.name] || col.classification || {
              inferred_type: "categorical",
              confidence: 0.8,
              reasons: ["Défaut"],
            };
            const isLowConfidence = cls.confidence < 0.6;

            return (
              <div
                key={col.name}
                className={`p-4 rounded-lg border text-sm transition-all ${
                  isLowConfidence
                    ? "border-amber-300 bg-amber-50/30"
                    : "border-slate-200 bg-slate-50/50"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="font-semibold text-slate-900 truncate" title={col.name}>
                    {col.name}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-medium border ${getBadgeStyle(
                      cls.inferred_type
                    )}`}
                  >
                    {cls.inferred_type}
                  </span>
                </div>

                <div className="text-xs text-slate-500 space-y-1 mb-3">
                  <div className="flex justify-between items-center">
                    <span>Confiance :</span>
                    <span
                      className={`font-medium ${
                        isLowConfidence ? "text-amber-700" : "text-emerald-600"
                      }`}
                    >
                      {Math.round(cls.confidence * 100)}%
                    </span>
                  </div>

                  {isLowConfidence && (
                    <div className="flex items-center gap-1 text-amber-700 text-xs mt-1">
                      <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>Confiance faible : vérifiez la reclassification</span>
                    </div>
                  )}

                  {cls.reasons && cls.reasons.length > 0 && (
                    <div className="text-slate-500 text-xs italic truncate" title={cls.reasons.join(", ")}>
                      {cls.reasons[0]}
                    </div>
                  )}
                </div>

                {/* Reclassification Switcher */}
                <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-xs">
                  <span className="text-slate-500 font-medium">Reclassifier :</span>
                  <select
                    value={cls.inferred_type}
                    disabled={reclassifyingCol === col.name}
                    onChange={(e) => handleReclassify(col.name, e.target.value)}
                    className="bg-white border border-slate-300 rounded px-2 py-1 text-xs text-slate-700 font-medium focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  >
                    <option value="numeric">Numérique</option>
                    <option value="categorical">Catégorielle</option>
                    <option value="identifier">Identifiant</option>
                    <option value="datetime">Date / Temporel</option>
                  </select>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2. Manual Exploration & Chart Selector */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
        <div>
          <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-brand-600" />
            Exploration Manuelle de Graphiques (16 Types)
          </h3>
          <p className="text-sm text-slate-500">
            Choisissez un type de graphique et associez vos colonnes. Le moteur valide la cohérence statistique avant génération.
          </p>
        </div>

        {/* Chart Type Selector */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {ALL_CHART_TYPES.map((chart) => {
            const isSelected = selectedChartType === chart.id;
            return (
              <button
                key={chart.id}
                onClick={() => setSelectedChartType(chart.id)}
                className={`flex flex-col items-center justify-center p-3 rounded-lg border text-xs font-medium transition-all ${
                  isSelected
                    ? "border-brand-500 bg-brand-50 text-brand-700 shadow-sm ring-2 ring-brand-500/20"
                    : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                <span className="text-xl mb-1">{chart.icon}</span>
                <span className="text-center line-clamp-1">{chart.label}</span>
              </button>
            );
          })}
        </div>

        {/* Column Mapping Controls */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
            Configuration des Axes & Rôles :
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {currentChartDef.roles.map((role) => (
              <div key={role.key} className="space-y-1">
                <label className="text-xs font-medium text-slate-700 flex items-center justify-between">
                  <span>{role.label}</span>
                </label>
                <select
                  value={mapping[role.key] || ""}
                  onChange={(e) => setMapping({ ...mapping, [role.key]: e.target.value })}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                >
                  {profile.columns.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name} ({(classifications[c.name] || c.classification)?.inferred_type || "texte"})
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>

        {/* Validation Feedback & Warnings */}
        {validation && (
          <div className="space-y-3">
            {/* Blocking Errors */}
            {!validation.is_valid && validation.errors.length > 0 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-red-900">
                  <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
                  <span>Configuration invalide :</span>
                </div>
                <ul className="list-disc list-inside space-y-1 text-xs text-red-700">
                  {validation.errors.map((err, idx) => (
                    <li key={idx}>{err}</li>
                  ))}
                </ul>
                {validation.suggestion && (
                  <div className="mt-2 text-xs bg-red-100/60 p-2 rounded text-red-900 font-medium flex items-center gap-1.5">
                    <Info className="w-4 h-4 text-red-700" />
                    <span>Suggestion alternative : {validation.suggestion}</span>
                  </div>
                )}
              </div>
            )}

            {/* Non-blocking Warnings */}
            {validation.warnings.length > 0 && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800 space-y-1">
                <div className="flex items-center gap-2 font-semibold text-amber-900">
                  <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                  <span>Avertissement(s) statistique(s) :</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 text-xs text-amber-700">
                  {validation.warnings.map((warn, idx) => (
                    <li key={idx}>{warn}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Chart Canvas Rendering */}
        <div>
          {loading ? (
            <div className="h-[380px] w-full flex items-center justify-center bg-slate-50 border border-slate-200 rounded-xl text-slate-500 text-sm gap-2">
              <RefreshCw className="w-5 h-5 animate-spin text-brand-600" />
              <span>Génération du graphique...</span>
            </div>
          ) : validation && validation.is_valid && chartOptions ? (
            <EChartViewer options={chartOptions} height="420px" />
          ) : (
            <div className="h-[200px] w-full flex flex-col items-center justify-center bg-slate-50 border border-dashed border-slate-200 rounded-xl text-slate-400 text-sm gap-2">
              <BarChart3 className="w-8 h-8 text-slate-300" />
              <span>
                {!validation?.is_valid
                  ? "Ajustez la configuration des colonnes ci-dessus pour afficher le graphique."
                  : "Sélectionnez les variables pour générer le rendu."}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
