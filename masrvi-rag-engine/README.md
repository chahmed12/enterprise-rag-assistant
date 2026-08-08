<div align="center">
  <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" alt="Robot" width="100" />

  # Masrvi RAG Engine 🧠

  **Un moteur de recherche vectorielle et de génération augmentée (RAG) propulsé par FastAPI & Qdrant.**

  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Qdrant](https://img.shields.io/badge/Qdrant-FF5252?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
  [![Status](https://img.shields.io/badge/Status-Work_In_Progress-FFC107?style=for-the-badge&logo=git)](https://github.com/)
</div>

---

> [!WARNING]
> 🚧 **PROJET EN COURS DE DÉVELOPPEMENT (WORK IN PROGRESS)** 🚧
> Ce projet est actuellement en phase de construction. Certaines fonctionnalités peuvent être incomplètes, instables ou sujettes à d'importantes modifications.

## 🚀 À Propos

**Masrvi RAG Engine** est le composant d'intelligence artificielle du projet Masrvi. Il s'agit d'un microservice chargé d'ingérer des documents (PDF, Markdown, Word, TXT), de les traiter (nettoyage, chunking), de les vectoriser et de répondre aux questions des utilisateurs en se basant sur ce contexte (Retrieval-Augmented Generation).

## ✨ Fonctionnalités (Actuelles & Prévues)

- [x] 📄 **Ingestion multi-formats** : Support de PDF, MD, TXT, DOCX.
- [x] 🔪 **Smart Chunking** : Découpage sémantique des documents.
- [x] 💾 **Stockage Vectoriel** : Intégration avec **Qdrant**.
- [x] ⚡ **API Asynchrone** : Ingestion en arrière-plan (BackgroundTasks).
- [x] 💬 **Génération de réponses** : Intégration de LLMs.
- [ ] 🔄 **Synchronisation en temps réel** : Mise à jour du contexte dynamique.
- [ ] 📊 **Dashboard de suivi** : Monitoring des performances de recherche.
- [ ] 🛡️ **Sécurité & Auth** : Sécurisation complète de l'API.

## 🛠️ Architecture

L'application repose sur une architecture moderne, orientée données :

*   **Framework Web** : [FastAPI](https://fastapi.tiangolo.com/)
*   **Orchestration LLM** : LangChain
*   **Base de données Vectorielle** : [Qdrant](https://qdrant.tech/)

## ⚙️ Installation & Démarrage

### Prérequis
* Python 3.9+
* Qdrant (via Docker ou Cloud)

### Démarrage Rapide

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/VOTRE_USER/VOTRE_REPO.git
   cd masrvi-rag-engine
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv zenvour
   # Windows :
   zenvour\Scripts\activate
   # Linux/Mac :
   # source zenvour/bin/activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**
   Créez un fichier `.env` à la racine :
   ```env
   # Ajoutez vos variables d'environnement ici
   ```

5. **Lancer le serveur**
   ```bash
   uvicorn app.main:app --reload
   ```
   L'API sera disponible sur `http://localhost:8000`. Vous pouvez tester les endpoints via `http://localhost:8000/docs`.

## 🗺️ Roadmap (Prochaines étapes)
- Amélioration de la stratégie de découpage.
- Implémentation du système de reranking.
- Tests unitaires et d'intégration complets.
- Conteneurisation (Dockerfile et docker-compose).

<br>
<div align="center">
  <i>Développé pour le projet Masrvi</i>
</div>
