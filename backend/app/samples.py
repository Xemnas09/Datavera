import os
from pathlib import Path
from typing import List, Dict, Tuple, Any
from app.schemas import SampleDatasetInfo

SAMPLES_DIR = Path(__file__).resolve().parent / "sample_files"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

# Sample 1: Sales / Ventes E-Commerce
SALES_CSV_PATH = SAMPLES_DIR / "ventes_ecommerce.csv"
SALES_CSV_CONTENT = """id_commande,date_commande,client_nom,categorie,produit,quantite,prix_unitaire,chiffre_affaires,pays,mode_livraison
CMD-1001,2024-01-05,TechCorp,Électronique,Écran 27 pouces,5,250.00,1250.00,France,Express
CMD-1002,2024-01-08,DataConsult,Logiciels,Licence Annuelle,2,499.00,998.00,France,Standard
CMD-1003,2024-01-12,AeroSpace SAS,Électronique,Clavier Mécanique,10,85.00,850.00,Belgique,Express
CMD-1004,2024-01-15,Global Retail,Mobilier,Chaise Ergonomique,4,210.00,840.00,Suisse,Standard
CMD-1005,2024-01-20,TechCorp,Services,Audit Sécurité,1,1500.00,1500.00,France,Express
CMD-1006,2024-02-02,InnoLab,Électronique,Casque Réduction Bruit,8,180.00,1440.00,Belgique,Standard
CMD-1007,2024-02-10,FinTech SA,Mobilier,Bureau Assis-Debout,3,650.00,1950.00,Luxembourg,Express
CMD-1008,2024-02-14,AeroSpace SAS,Services,Formation Cloud,2,800.00,1600.00,Belgique,Standard
CMD-1009,2024-02-18,Global Retail,Électronique,Webcam HD,15,60.00,900.00,Suisse,Express
CMD-1010,2024-02-25,DataConsult,Logiciels,Module IA Analytics,3,1200.00,3600.00,France,Express
CMD-1011,2024-03-01,BioHealth,Mobilier,Chaise Ergonomique,6,210.00,1260.00,France,Standard
CMD-1012,2024-03-05,TechCorp,Électronique,Écran 27 pouces,4,250.00,1000.00,France,Express
CMD-1013,2024-03-12,FinTech SA,Services,Audit Sécurité,2,1500.00,3000.00,Luxembourg,Express
CMD-1014,2024-03-18,InnoLab,Logiciels,Licence Annuelle,5,499.00,2495.00,Belgique,Standard
CMD-1015,2024-03-22,Global Retail,Électronique,Clavier Mécanique,12,85.00,1020.00,Suisse,Standard
"""

# Sample 2: HR / Ressources Humaines
HR_CSV_PATH = SAMPLES_DIR / "effectifs_rh.csv"
HR_CSV_CONTENT = """id_employe,nom,prenom,departement,poste,salaire_annuel,date_embauche,niveau_etudes,satisfaction_score
EMP-001,Dupont,Jean,R&D,Ingénieur Senior,62000,2019-03-15,Master,8.5
EMP-002,Martin,Sophie,Marketing,Chef de Projet,48000,2021-06-01,Master,7.8
EMP-003,Bernard,Lucas,Ventes,Account Executive,55000,2020-01-10,Licence,9.0
EMP-004,Petit,Camille,RH,Responsable Recrutement,51000,2018-11-20,Master,8.1
EMP-005,Robert,Antoine,R&D,Data Scientist,58000,2022-02-14,Doctorat,8.9
EMP-006,Richard,Emma,Finance,Contrôleur de Gestion,54000,2020-09-01,Master,7.5
EMP-007,Durand,Thomas,Ventes,Directeur Commercial,85000,2016-04-05,Master,9.2
EMP-008,Moreau,Léa,Marketing,Growth Hacker,42000,2023-01-16,Licence,8.0
EMP-009,Lefebvre,Hugo,R&D,Développeur Fullstack,50000,2021-11-02,Master,8.4
EMP-0010,Gras,Manon,Finance,Analyste Financier,47000,2022-08-20,Master,7.9
"""

def init_sample_files():
    if not SALES_CSV_PATH.exists():
        SALES_CSV_PATH.write_text(SALES_CSV_CONTENT, encoding="utf-8")
    if not HR_CSV_PATH.exists():
        HR_CSV_PATH.write_text(HR_CSV_CONTENT, encoding="utf-8")

init_sample_files()

SAMPLE_DATASETS: Dict[str, Dict[str, Any]] = {
    "sales": {
        "info": SampleDatasetInfo(
            id="sales",
            title="Ventes E-Commerce",
            description="Chiffre d'affaires, produits, catégories et pays de livraison (15 commandes)",
            filename="ventes_ecommerce.csv",
            row_count=15,
            column_count=10
        ),
        "path": SALES_CSV_PATH
    },
    "hr": {
        "info": SampleDatasetInfo(
            id="hr",
            title="Ressources Humaines & Salaires",
            description="Effectifs, départements, postes, salaires et scores de satisfaction (10 employés)",
            filename="effectifs_rh.csv",
            row_count=10,
            column_count=9
        ),
        "path": HR_CSV_PATH
    }
}

def get_sample_list() -> List[SampleDatasetInfo]:
    return [s["info"] for s in SAMPLE_DATASETS.values()]

def get_sample_filepath(sample_id: str) -> Tuple[Path, str]:
    if sample_id not in SAMPLE_DATASETS:
        raise ValueError(f"Jeu de données exemple non trouvé: {sample_id}")
    dataset = SAMPLE_DATASETS[sample_id]
    return dataset["path"], dataset["info"].filename
