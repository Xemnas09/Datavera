import os
import json
import logging
from typing import Dict, Any, Tuple, Optional
from groq import Groq
from google import genai
from app.config import (
    DEFAULT_LLM_PROVIDER,
    GROQ_API_KEY,
    GROQ_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL
)

logger = logging.getLogger("datavera.llm_service")

SYSTEM_PROMPT = """Tu es un expert DuckDB SQL et un analyste de données expérimenté.
Ton objectif est de générer une requête DuckDB SQL valide pour répondre à la question de l'utilisateur sur la table nommée `dataset`.

Règles de génération :
1. Utilise TOUJOURS la table `dataset`.
2. Génère uniquement des requêtes SELECT ou WITH en lecture seule.
3. N'utilise JAMAIS de commandes destructrices (DROP, DELETE, UPDATE, INSERT, ALTER).
4. Respecte scrupuleusement le nom des colonnes fournies dans le schéma (attention à la casse et aux espaces, entoure les noms de colonnes complexes de guillemets doubles si nécessaire `"Nom Colonne"`).
5. Réponds STRICTEMENT sous la forme d'un objet JSON valide contenant les clés :
   - "sql": la requête DuckDB SQL générée (sans bloc markdown ```sql).
   - "explanation": une explication claire et concise en français de l'analyse effectuée.

Exemple de format de réponse :
{
  "sql": "SELECT categorie, SUM(chiffre_affaires) AS total_ca FROM dataset GROUP BY categorie ORDER BY total_ca DESC LIMIT 10",
  "explanation": "Agrégation du chiffre d'affaires total par catégorie de produits, classée par ordre décroissant."
}
"""

def build_user_prompt(
    schema_info: str,
    sample_rows_str: str,
    question: str,
    error_feedback: Optional[str] = None
) -> str:
    prompt = f"""Schéma de la table `dataset` :
{schema_info}

Échantillon de données (3 à 5 lignes) :
{sample_rows_str}

Question de l'utilisateur :
"{question}"
"""
    if error_feedback:
        prompt += f"""\nATTENTION: Ta précédente tentative de requête SQL a échoué avec l'erreur suivante de DuckDB :
"{error_feedback}"
Corrige la syntaxe ou les noms de colonnes et génère une nouvelle requête SQL valide.
"""
    return prompt

def generate_sql_with_groq(prompt: str) -> Tuple[str, str]:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY non configurée.")

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        timeout=10.0,  # 10s timeout
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    data = json.loads(content)
    return data.get("sql", ""), data.get("explanation", "")

def generate_sql_with_gemini(prompt: str) -> Tuple[str, str]:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY non configurée.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
        config={"response_mime_type": "application/json"}
    )
    data = json.loads(response.text)
    return data.get("sql", ""), data.get("explanation", "")

def generate_fallback_sql(question: str, schema_info: str) -> Tuple[str, str]:
    """
    Fallback heuristics generator when no LLM API key is present or APIs fail.
    Analyzes basic question keywords (compte, somme, moyenne, liste, etc.).
    """
    q_lower = question.lower()

    if "combien" in q_lower or "nombre" in q_lower or "compte" in q_lower or "total" in q_lower:
        return "SELECT COUNT(*) AS nombre_total FROM dataset", "Calcul du nombre total d'enregistrements dans le jeu de données."
    elif "moyenne" in q_lower or "avg" in q_lower:
        return "SELECT * FROM dataset LIMIT 10", "Aperçu des 10 premiers enregistrements pour analyse de la moyenne."
    else:
        return "SELECT * FROM dataset LIMIT 10", "Affichage des 10 premiers enregistrements de la table."

def generate_sql_query(
    schema_info: str,
    sample_rows_str: str,
    question: str,
    provider: Optional[str] = None,
    error_feedback: Optional[str] = None
) -> Tuple[str, str]:
    """
    Calls requested provider (or default) and falls back gracefully if unconfigured or failed.
    Categorizes errors for clear user-facing feedback without raw stack traces.
    Returns: (sql, explanation)
    """
    target_provider = (provider or DEFAULT_LLM_PROVIDER).lower()
    user_prompt = build_user_prompt(schema_info, sample_rows_str, question, error_feedback)

    # Try preferred provider
    if target_provider == "groq" and GROQ_API_KEY:
        try:
            return generate_sql_with_groq(user_prompt)
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "429" in err_msg or "rate limit" in err_msg:
                logger.error(f"Quota Groq dépassé : {e}")
            elif "timeout" in err_msg:
                logger.error(f"Timeout lors de l'appel Groq : {e}")
            else:
                logger.warning(f"Erreur API Groq : {e}. Tentative avec Gemini...")

    if (target_provider == "gemini" or not GROQ_API_KEY) and GEMINI_API_KEY:
        try:
            return generate_sql_with_gemini(user_prompt)
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
                logger.error(f"Quota Gemini dépassé : {e}")
            elif "timeout" in err_msg:
                logger.error(f"Timeout lors de l'appel Gemini : {e}")
            else:
                logger.warning(f"Erreur API Gemini : {e}.")

    # Fallback generator
    logger.info("Génération de secours par heuristique (moteur local sans LLM).")
    return generate_fallback_sql(question, schema_info)
