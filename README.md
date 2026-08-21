# Datavera — Analyse de Données en Langage Naturel & DuckDB

![Datavera Architecture](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20DuckDB%20%7C%20ECharts-blue)
![Free Tier 100%](https://img.shields.io/badge/Constraint-100%25%20Free%20Tier-green)
![License](https://img.shields.io/badge/License-MIT-green)

**Datavera** est un outil web exploratoire permettant à n'importe quel utilisateur d'importer un fichier de données (CSV, TSV, Excel `.xlsx` / `.xls`), d'interroger ses données en langage naturel via un chatbot IA (Gemini / Groq) et d'explorer visuellement ses données grâce à un moteur de classification automatique et 16 types de graphiques interactifs (Apache ECharts).

---

## 🎯 Justifications d'Architecture — Contrainte Strictement "100% Free Tier"

Pour garantir un coût d'hébergement et d'utilisation **strictement nul ($0.00/mois)**, l'architecture de Datavera repose sur des choix techniques assumés :

1. **DuckDB In-Memory Embarqué (Pas de Base de Données Cloud)** :
   - Plutôt que d'utiliser une base SQL managée (Supabase, Neon, PostgreSQL), DuckDB est exécuté sous forme de processus in-memory directement au sein du backend FastAPI.
   - **Avantage** : Traitement analytique ultra-rapide en mémoire (colonnes en vectoriel), isolation stricte des sessions sans aucun frais de base de données externe.
2. **Gestion de Session sans Persistance Long Terme (TTL Inactivité)** :
   - Aucune base de données ni de stockage d'objets cloud (GCS, AWS S3) n'est nécessaire.
   - Les données et les instances DuckDB sont conservées en mémoire vive pendant la session active, avec un nettoyage automatique au bout de 30 minutes d'inactivité pour libérer la RAM de l'hébergeur gratuit.
3. **Confidentialité et Quotas LLM Optimisés** :
   - Le LLM externe (Groq / Gemini Free Tier) ne reçoit **jamais** les fichiers bruts ni l'intégralité du dataset.
   - Il reçoit uniquement le schéma des colonnes et un échantillon de 3 lignes pour générer la requête DuckDB SQL, garantissant à la fois un respect strict de la confidentialité et un coût de jetons (tokens) insignifiant.
4. **Architecture BFF Proxy (Next.js & FastAPI)** :
   - Le frontend Next.js fait office de proxy léger BFF (Backend For Frontend) déployé gratuitement sur Vercel, déléguant tous les calculs lourds au backend Python FastAPI hébergé sur Render ou Railway (Free Tier).

---

## 🚀 Fonctionnalités Clés

1. **Pipeline d'Ingestion Ultra-Robuste (`ingestion_v2.py`)** :
   - Détection automatique de format par "magic bytes" et sniffing d'encodage (`chardet`).
   - Prise en charge des classeurs Excel multi-feuilles et désamalgamation automatique des cellules fusionnées (`unmerge`).
   - Détection intelligente des en-têtes complexes, décalés ou surlignés.
   - Nettoyage automatique des totaux/sous-totaux intercalés et conversion des formats régionaux (nombres français `'1 234,56'`, dates ISO Excel).

2. **Classification Statistique & Audit de Confiance (`column_classifier.py`)** :
   - Classification automatique de chaque colonne en : `numeric`, `categorical`, `identifier` ou `datetime`.
   - Score de confiance explicite (0 à 100%) et raisons détaillées pour éviter les effets "boîte noire".
   - **Reclassification manuelle session-persistante** : l'utilisateur peut surcharger le rôle statistique de chaque colonne directement depuis l'interface web.

3. **Exploration Graphique en 16 Types de Graphiques (Apache ECharts)** :
   - **Barres & Proportions** : Bar, Bar Grouped, Bar Stacked, Bar 100%, Bar Sorted, Pie, Donut, Treemap.
   - **Distributions & Statistiques** : Histogram, Boxplot, Violin plot, Density plot.
   - **Correlations & Relations** : Scatter plot, Bubble chart, Correlation Heatmap.
   - **Séries Temporelles & Évolutions** : Line chart, Area chart, Area Stacked.
   - **Moteur de Validation Pré-Rendu (`validate_chart_config`)** : vérification stricte des contraintes statistiques (cardinalité max, valeurs négatives, types requis) avec recommandations automatiques d'alternatives en cas d'incompatibilité.

4. **Assistant IA & Chatbot SQL Sandboxé** :
   - Génération de requêtes SQL en langage naturel par LLM (Gemini / Groq).
   - Validateur AST anti-injection strict (requêtes `SELECT` en lecture seule uniquement, blocage de `DROP`, `DELETE`, `UPDATE`).
   - Auto-correction automatique (1-retry) en cas d'erreur de syntaxe SQL DuckDB.

---

## ⚠️ Limitations Connues & Assumées

- **Tableaux multiples sur une seule feuille Excel** : Le pipeline est optimisé pour les fichiers contenant une table structurée principale par feuille. Les fichiers comportant plusieurs sous-tableaux indépendants sur la même feuille ne sont pas gérés automatiquement.
- **Cardinalité Maximale pour la Visualisation** : Pour maintenir la lisibilité des graphiques et éviter de surcharger le navigateur, certains types de graphiques appliquent des limites de cardinalité recommandée (ex. 7 catégories max pour un Pie Chart, 8 pour un Bar Chart Empilé).
- **Mise en Veille Backend (Free Tier Cold Starts)** : En hébergement gratuit sur Render/Railway, le backend entre en veille après 15 minutes d'inactivité. Un délai de réveil de 10 à 25 secondes peut survenir lors du premier appel, pendant lequel l'UI affiche un indicateur de chargement dédié.

---

## 🛠️ Stack Technique

- **Frontend** : Next.js 14 (React, App Router), Tailwind CSS, Lucide React, Apache ECharts (`echarts` & `echarts-for-react`) — Déployé sur **Vercel**.
- **Backend** : FastAPI (Python 3.12), DuckDB embarqué (In-Memory / Session), Pandas, PyYAML, OpenPyXL, xlrd, Sqlglot — Déployé sur **Render / Railway** (Free Tier).
- **LLM / IA** : Gemini API (`google-generativeai`) / Groq API (`groq`).
- **Tests** : Pytest (Backend) & Vitest (Frontend).

---

## 📂 Structure du Projet

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # Endpoints FastAPI (Upload, Reclassify, Explore, Query, Health)
│   │   ├── column_classifier.py     # Classificateur statistique & règles de validation des 16 graphiques
│   │   ├── chart_generator.py       # Générateur d'options ECharts pour les 16 types
│   │   ├── ingestion_v2.py          # Ingestion CSV/Excel robuste et désamalgamation
│   │   ├── query_engine.py          # Exécuteur SQL IA sandboxé avec validation
│   │   ├── sql_validator.py         # Sécurité AST SQL (Lecture seule, injection)
│   │   ├── profiling.py             # Profilage statistique et résumé du dataset
│   │   ├── session_manager.py       # Gestionnaire de sessions DuckDB in-memory
│   │   └── llm_service.py           # Intégration Gemini/Groq avec gestion de timeout/fallbacks
│   └── tests/                       # Suite de tests unitaires et d'intégration Pytest
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js App Router
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

# (Optionnel) Configurer votre clé d'API LLM (Groq ou Gemini)
export GROQ_API_KEY="votre_cle_groq"
# ou
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
