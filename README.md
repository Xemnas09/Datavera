# Datavera — Analyse de Données en Langage Naturel & DuckDB

![Datavera Architecture](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20DuckDB%20%7C%20ECharts-blue)
![License](https://img.shields.io/badge/License-MIT-green)

**Datavera** est un outil web exploratoire permettant à n'importe quel utilisateur d'importer un fichier de données (CSV, TSV, Excel `.xlsx` / `.xls`), d'interroger ses données en langage naturel via un chatbot IA (Gemini / Groq) et d'explorer visualement ses données grâce à un moteur de classification automatique et 16 types de graphiques interactifs (Apache ECharts).

---

## 🚀 Fonctionnalités Clés

1. **Pipeline d'Ingestion Ultra-Robuste (`ingestion_v2.py`)** :
   - Détection automatique de format par "magic bytes" et sniffing d'encodage (`chardet`).
   - Prise en charge des classeurs Excel multi-feuilles et désamalgamation automatique des cellules fusionnées (`unmerge`).
   - Détection intelligente des en-têtes complexes, décalés ou surlignés.
   - Nettoyage automatique des totaux/sous-totaux intercalés et conversion des formats régionaux (nombres français `'1 234,56'`, dates ISO Excel).
   - Ingestion zéro persistance dans **DuckDB** embarqué.

2. **Classification Statistique & Audit de Confiance (`column_classifier.py`)** :
   - Classification automatique de chaque colonne en : `numeric`, `categorical`, `identifier` ou `datetime`.
   - Score de confiance explicite (0 à 100%) et raisons détaillées pour éviter les effets "boîte noire".
   - **Reclassification manuelle session-persistante** : l'utilisateur peut surcharger les rôles des colonnes depuis l'interface web.

3. **Exploration Graphique en 16 Types de Graphiques (Apache ECharts)** :
   - **Barres & Proportions** : Bar, Bar Grouped, Bar Stacked, Bar 100%, Bar Sorted, Pie, Donut, Treemap.
   - **Distributions & Statistiques** : Histogram, Boxplot, Violin plot, Density plot.
   - **Correlations & Relations** : Scatter plot, Bubble chart, Correlation Heatmap.
   - **Séries Temporelles & Évolutions** : Line chart, Area chart, Area Stacked.
   - **Moteur de Validation Pré-Rendu (`validate_chart_config`)** : vérification stricte des contraintes statistiques (cardinalité max, valeurs négatives, types requis) avec recommandations automatiques d'alternatives en cas d'incompatibilité.

4. **Assistant IA & Chatbot SQL Sandboxé** :
   - Génération de requêtes SQL en langage naturel par LLM (Gemini / Groq).
   - **Principe de Confidentialité Stricte** : le LLM ne reçoit **jamais** les données brutes, mais uniquement le schéma DuckDB et un échantillon de 3 lignes.
   - Validateur anti-injection strict (requêtes `SELECT` en lecture seule uniquement, blocage de `DROP`, `DELETE`, `UPDATE`).
   - Auto-correction automatique (1-retry) en cas d'erreur de syntaxe SQL DuckDB.

---

## 🛠️ Stack Technique

- **Frontend** : Next.js 14 (React, App Router), Tailwind CSS, Lucide React, Apache ECharts (`echarts` & `echarts-for-react`).
- **Backend** : FastAPI (Python 3.12), DuckDB embarqué (In-Memory / Session), Pandas, PyYAML, OpenPyXL, xlrd.
- **LLM / IA** : Gemini API (`google-generativeai`) / Groq API (`groq`).
- **Tests** : Pytest (Backend) & Vitest (Frontend).

---

## 📂 Structure du Projet

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # Endpoints FastAPI (Upload, Reclassify, Explore, Query)
│   │   ├── column_classifier.py     # Classificateur statistique & règles de validation des 16 graphiques
│   │   ├── chart_generator.py       # Générateur d'options ECharts pour les 16 types
│   │   ├── ingestion_v2.py          # Ingestion CSV/Excel robuste et désamalgamation
│   │   ├── query_engine.py          # Exécuteur SQL IA sandboxé avec validation
│   │   ├── profiling.py             # Profilage statistique et résumé du dataset
│   │   ├── session_manager.py       # Gestionnaire de sessions DuckDB in-memory
│   │   └── llm_service.py           # Intégration Gemini/Groq
│   └── tests/                       # Suite de tests unitaires et d'intégration Pytest
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router (Layout, Page principale)
│   │   ├── components/              # Workspace, Chatbot, ManualExploration, EChartViewer, Profiling
│   │   └── lib/                     # Client API Fetch (`api.ts`)
└── README.md
```

---

## ⚙️ Installation & Lancement Local

### Prérequis
- Python 3.10+
- Node.js 18+

### 1. Démarrer le Backend FastAPI

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt

# (Optionnel) Configurer votre clé d'API LLM
export GEMINI_API_KEY="votre_cle_gemini"

# Lancer le serveur uvicorn sur le port 8000
uvicorn app.main:app --reload --port 8000
```

### 2. Démarrer le Frontend Next.js

```bash
cd frontend
npm install

# Lancer le serveur de développement Next.js sur le port 3000
npm run dev
```

Rendez-vous sur [http://localhost:3000](http://localhost:3000) pour utiliser Datavera.

---

## 🧪 Exécution des Tests

### Tests Backend (Pytest)
```bash
PYTHONPATH=backend pytest backend/tests/
```

### Tests Frontend (Vitest)
```bash
cd frontend
npm test
```

---

## 📄 Licence

Ce projet est sous licence MIT.
