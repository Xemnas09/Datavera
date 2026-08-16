"""
Datavera — Module de classification de colonnes et validation de graphiques.

Objectif :
1. Classifier chaque colonne d'un DataFrame en : numeric | categorical | identifier | datetime
2. Fournir un score de confiance (pas une décision binaire silencieuse)
3. Valider une configuration de graphique (type + colonnes choisies) avant génération

Ce module ne prend aucune décision irréversible seul : il retourne des scores et des
raisons explicites, à afficher côté frontend pour permettre une correction manuelle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# 1. Classification de colonnes
# ---------------------------------------------------------------------------

IDENTIFIER_KEYWORDS = [
    "id", "code", "num", "numero", "n°", "ref", "reference",
    "matricule", "siret", "siren", "zip", "cp", "postal",
]

@dataclass
class ColumnClassification:
    name: str
    dtype_pandas: str
    inferred_type: str          # "numeric" | "categorical" | "identifier" | "datetime"
    confidence: float           # 0.0 à 1.0
    reasons: list[str] = field(default_factory=list)
    cardinality: int = 0
    cardinality_ratio: float = 0.0


def _keyword_signal(col_name: str) -> bool:
    normalized = col_name.lower().strip()
    return any(kw in normalized for kw in IDENTIFIER_KEYWORDS)


def _sequence_signal(series: pd.Series) -> float:
    """Renvoie la proportion d'écarts consécutifs égaux à 1 après tri."""
    numeric_series = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if len(numeric_series) < 5:
        return 0.0
    diffs = numeric_series.sort_values().diff().dropna()
    if len(diffs) == 0:
        return 0.0
    return float((diffs == 1).mean())


def _order_correlation_signal(series: pd.Series) -> float:
    """Corrélation entre la colonne et l'ordre d'apparition dans le fichier."""
    numeric_series = pd.to_numeric(series, errors="coerce")
    valid = numeric_series.dropna()
    if len(valid) < 5:
        return 0.0
    order = pd.Series(range(len(valid)), index=valid.index)
    corr = valid.corr(order)
    return abs(corr) if pd.notna(corr) else 0.0


def _digit_homogeneity_signal(series: pd.Series) -> bool:
    """True si toutes les valeurs ont le même nombre de chiffres (hors NaN)."""
    as_str = series.dropna().astype(str).str.replace(r"\.0$", "", regex=True)
    lengths = as_str.str.len()
    if len(lengths) == 0:
        return False
    return lengths.nunique() == 1


def score_is_identifier(series: pd.Series, col_name: str) -> tuple[float, list[str]]:
    """
    Combine plusieurs signaux faibles en un score composite (0 à 1).
    Retourne le score ET la liste des raisons ayant contribué, pour transparence.
    """
    score = 0.0
    reasons = []

    seq_ratio = _sequence_signal(series)
    if seq_ratio > 0.9:
        score += 0.4
        reasons.append(f"séquence quasi continue détectée ({seq_ratio:.0%} d'écarts de 1)")

    order_corr = _order_correlation_signal(series)
    if order_corr > 0.9:
        score += 0.2
        reasons.append(f"forte corrélation avec l'ordre des lignes ({order_corr:.2f})")

    if _digit_homogeneity_signal(series):
        score += 0.2
        reasons.append("nombre de chiffres identique sur toutes les valeurs")

    ratio = series.nunique(dropna=True) / max(len(series), 1)
    if ratio > 0.7:
        score += 0.1
        reasons.append(f"cardinalité relative élevée ({ratio:.0%})")

    if _keyword_signal(col_name):
        score += 0.1
        reasons.append("mot-clé suspect dans le nom de colonne")

    return min(score, 1.0), reasons


def classify_column(series: pd.Series, col_name: str,
                     low_cardinality_threshold: int = 20) -> ColumnClassification:
    """
    Classifie une colonne en numeric / categorical / identifier / datetime.
    Ne tranche jamais avec une confiance de 1.0 sur les cas ambigus :
    le champ `confidence` doit être utilisé côté frontend pour proposer
    une correction manuelle quand il est bas (ex. < 0.6).
    """
    dtype_str = str(series.dtype)
    n = len(series)
    cardinality = series.nunique(dropna=True)
    cardinality_ratio = cardinality / max(n, 1)

    # --- Datetime : détection explicite en premier ---
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnClassification(
            name=col_name, dtype_pandas=dtype_str, inferred_type="datetime",
            confidence=1.0, reasons=["type datetime natif"],
            cardinality=cardinality, cardinality_ratio=cardinality_ratio,
        )

    # Tentative de parsing datetime sur colonnes texte (ex. "2024-01-15")
    if dtype_str == "object":
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        if parsed.notna().mean() > 0.9:
            return ColumnClassification(
                name=col_name, dtype_pandas=dtype_str, inferred_type="datetime",
                confidence=0.85, reasons=["colonne texte convertible en date à >90%"],
                cardinality=cardinality, cardinality_ratio=cardinality_ratio,
            )

    # --- Colonnes non numériques : catégorielle par défaut, sauf si quasi-unique ---
    if not pd.api.types.is_numeric_dtype(series):
        if cardinality_ratio > 0.9 and n > 20:
            return ColumnClassification(
                name=col_name, dtype_pandas=dtype_str, inferred_type="identifier",
                confidence=0.75,
                reasons=[f"cardinalité quasi unique sur du texte ({cardinality_ratio:.0%})"],
                cardinality=cardinality, cardinality_ratio=cardinality_ratio,
            )
        return ColumnClassification(
            name=col_name, dtype_pandas=dtype_str, inferred_type="categorical",
            confidence=0.9, reasons=["type texte, cardinalité raisonnable"],
            cardinality=cardinality, cardinality_ratio=cardinality_ratio,
        )

    # --- Colonnes numériques : le cas ambigu (identifiant déguisé ?) ---
    id_score, id_reasons = score_is_identifier(series, col_name)

    if id_score >= 0.5:
        return ColumnClassification(
            name=col_name, dtype_pandas=dtype_str, inferred_type="identifier",
            confidence=id_score, reasons=id_reasons,
            cardinality=cardinality, cardinality_ratio=cardinality_ratio,
        )

    # Numérique à faible cardinalité : candidate catégorielle (ex. code, note 1-5)
    if cardinality <= low_cardinality_threshold and id_score >= 0.2:
        return ColumnClassification(
            name=col_name, dtype_pandas=dtype_str, inferred_type="categorical",
            confidence=0.55,
            reasons=["numérique à faible cardinalité avec signaux d'identifiant partiels"]
                    + id_reasons,
            cardinality=cardinality, cardinality_ratio=cardinality_ratio,
        )

    # Par défaut : numérique classique
    return ColumnClassification(
        name=col_name, dtype_pandas=dtype_str, inferred_type="numeric",
        confidence=0.9, reasons=["type numérique, aucun signal d'identifiant significatif"],
        cardinality=cardinality, cardinality_ratio=cardinality_ratio,
    )


def classify_dataframe(df: pd.DataFrame) -> dict[str, ColumnClassification]:
    """Classifie toutes les colonnes d'un DataFrame."""
    return {col: classify_column(df[col], col) for col in df.columns}


# ---------------------------------------------------------------------------
# 2. Validation de configuration de graphique
# ---------------------------------------------------------------------------

@dataclass
class ChartValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestion: str | None = None


# Règles minimales par type de graphique.
# required : liste de (type_attendu, quantité_minimale)
# max_cardinality : cardinalité max tolérée par rôle de variable (0 = premier "required")
CHART_RULES: dict[str, dict] = {
    "bar": {"required": [("categorical", 1), ("numeric", 1)], "max_cardinality": 50},
    "bar_grouped": {"required": [("categorical", 2), ("numeric", 1)], "max_cardinality": 8},
    "bar_stacked": {"required": [("categorical", 2), ("numeric", 1)], "max_cardinality": 8},
    "bar_100pct": {"required": [("categorical", 2), ("numeric", 1)], "max_cardinality": 8},
    "bar_sorted": {"required": [("categorical", 1), ("numeric", 1)], "max_cardinality": 50},
    "histogram": {"required": [("numeric", 1)], "forbidden": ["categorical", "datetime"]},
    "box": {"required": [("numeric", 1)], "optional": [("categorical", 1)], "max_cardinality": 15},
    "violin": {"required": [("numeric", 1)], "optional": [("categorical", 1)],
               "max_cardinality": 15, "min_rows_per_group": 10},
    "density": {"required": [("numeric", 1)], "optional": [("categorical", 1)], "min_rows": 20},
    "scatter": {"required": [("numeric", 2)], "optional": [("categorical", 1)],
                "max_cardinality": 10},
    "bubble": {"required": [("numeric", 3)], "optional": [("categorical", 1)]},
    "correlation_heatmap": {"required": [("numeric", 2)]},
    "line": {"required": [("datetime_or_ordinal", 1), ("numeric", 1)]},
    "area": {"required": [("datetime_or_ordinal", 1), ("numeric", 1)]},
    "area_stacked": {"required": [("datetime_or_ordinal", 1), ("categorical", 1), ("numeric", 1)],
                      "max_cardinality": 8},
    "pie": {"required": [("categorical", 1), ("numeric", 1)], "max_cardinality": 7,
            "forbid_negative": True},
    "donut": {"required": [("categorical", 1), ("numeric", 1)], "max_cardinality": 7,
              "forbid_negative": True},
    "treemap": {"required": [("categorical", 1), ("numeric", 1)], "max_cardinality": 50,
                "forbid_negative": True},
}


def validate_chart_config(
    df: pd.DataFrame,
    chart_type: str,
    mapping: dict[str, str],
    classifications: dict[str, ColumnClassification] | None = None,
) -> ChartValidationResult:
    """
    Valide une configuration de graphique choisie par l'utilisateur.

    Args:
        df: le DataFrame source
        chart_type: clé de CHART_RULES (ex. "scatter", "pie")
        mapping: dict des colonnes choisies, ex. {"x": "age", "y": "salaire", "color": "pays"}
        classifications: résultat de classify_dataframe(df), calculé si non fourni

    Returns:
        ChartValidationResult avec is_valid, errors (bloquants), warnings (non bloquants)
        et une suggestion de type alternatif si invalide.
    """
    if chart_type not in CHART_RULES:
        return ChartValidationResult(is_valid=False, errors=[f"Type de graphique inconnu : {chart_type}"])

    if classifications is None:
        classifications = classify_dataframe(df)

    rules = CHART_RULES[chart_type]
    errors: list[str] = []
    warnings: list[str] = []
    selected_cols = list(mapping.values())

    # --- Vérification d'existence des colonnes ---
    for col in selected_cols:
        if col not in df.columns:
            errors.append(f"Colonne inconnue : '{col}'")
    if errors:
        return ChartValidationResult(is_valid=False, errors=errors)

    # --- Vérification des types requis ---
    numeric_cols = [c for c in selected_cols
                     if classifications[c].inferred_type == "numeric"]
    categorical_cols = [c for c in selected_cols
                         if classifications[c].inferred_type == "categorical"]
    datetime_ordinal_cols = [c for c in selected_cols
                              if classifications[c].inferred_type == "datetime"
                              or (classifications[c].inferred_type == "numeric"
                                  and re.search(r"ann[ée]e|year|date", c.lower()))]
    identifier_cols = [c for c in selected_cols
                        if classifications[c].inferred_type == "identifier"]

    if identifier_cols:
        warnings.append(
            f"Colonne(s) identifiée(s) comme identifiant, probablement inadaptée(s) "
            f"pour un graphique : {', '.join(identifier_cols)}. "
            f"Vérifiez la classification si ce n'est pas voulu."
        )

    for required_type, min_count in rules.get("required", []):
        if required_type == "numeric":
            available = len(numeric_cols)
        elif required_type == "categorical":
            available = len(categorical_cols)
        elif required_type == "datetime_or_ordinal":
            available = len(datetime_ordinal_cols)
        else:
            available = 0

        if available < min_count:
            errors.append(
                f"Ce graphique nécessite au moins {min_count} variable(s) de type "
                f"'{required_type}', {available} fournie(s)."
            )

    if "forbidden" in rules:
        for col in selected_cols:
            if classifications[col].inferred_type in rules["forbidden"]:
                errors.append(
                    f"'{col}' est de type {classifications[col].inferred_type}, "
                    f"non autorisé pour ce type de graphique."
                )

    # --- Vérification de cardinalité ---
    if "max_cardinality" in rules:
        for col in categorical_cols:
            card = classifications[col].cardinality
            if card > rules["max_cardinality"]:
                errors.append(
                    f"'{col}' a {card} valeurs distinctes, "
                    f"au-delà de la limite recommandée ({rules['max_cardinality']}) "
                    f"pour ce type de graphique."
                )

    # --- Vérification des valeurs négatives (pie, donut, treemap) ---
    if rules.get("forbid_negative"):
        for col in numeric_cols:
            if (df[col].dropna() < 0).any():
                errors.append(
                    f"'{col}' contient des valeurs négatives, incompatible avec ce type "
                    f"de graphique (proportions)."
                )

    # --- Vérification de taille minimale d'échantillon ---
    if "min_rows" in rules and len(df) < rules["min_rows"]:
        warnings.append(
            f"Seulement {len(df)} lignes disponibles ; ce type de graphique est plus "
            f"fiable avec au moins {rules['min_rows']} observations."
        )

    if "min_rows_per_group" in rules and categorical_cols:
        group_col = categorical_cols[0]
        counts = df[group_col].value_counts()
        small_groups = counts[counts < rules["min_rows_per_group"]]
        if not small_groups.empty:
            warnings.append(
                f"Certains groupes de '{group_col}' ont moins de "
                f"{rules['min_rows_per_group']} observations : "
                f"{', '.join(small_groups.index.astype(str))}. Le résultat sera peu fiable."
            )

    # --- Avertissement scatter/bubble : trop de points ---
    if chart_type in ("scatter", "bubble") and len(df) > 5000:
        warnings.append(
            f"{len(df)} points à tracer : envisagez un échantillonnage pour éviter "
            f"un nuage de points surchargé."
        )

    is_valid = len(errors) == 0
    suggestion = None
    if not is_valid:
        suggestion = _suggest_alternative(chart_type, categorical_cols, numeric_cols)

    return ChartValidationResult(
        is_valid=is_valid, errors=errors, warnings=warnings, suggestion=suggestion
    )


def _suggest_alternative(chart_type: str, categorical_cols: list[str],
                          numeric_cols: list[str]) -> str | None:
    """Suggestion simple de repli en cas d'échec de validation."""
    fallback_map = {
        "pie": "bar (trop de catégories ou valeurs négatives : un bar chart reste lisible)",
        "donut": "bar",
        "line": "bar (si l'axe X n'est pas temporel/ordinal)",
        "violin": "box (échantillon trop petit pour une estimation de densité fiable)",
        "density": "histogram",
        "scatter": "box (si une des variables est catégorielle plutôt que numérique)",
    }
    return fallback_map.get(chart_type)
