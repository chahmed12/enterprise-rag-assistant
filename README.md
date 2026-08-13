<div align="center">
  <h1>Intelligent RAG Assistant</h1>
  <p><strong>Plateforme de Question-Réponse d'Entreprise (Retrieval-Augmented Generation)</strong></p>

  <p>
    <a href="#"><img src="https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white" alt="Angular"></a>
    <a href="#"><img src="https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=spring-boot&logoColor=white" alt="Spring Boot"></a>
    <a href="#"><img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"></a>
    <a href="#"><img src="https://img.shields.io/badge/Qdrant-1A1A1A?style=for-the-badge&logo=qdrant&logoColor=white" alt="Qdrant"></a>
    <a href="#"><img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama"></a>
  </p>
</div>

<br/>

## Sommaire
- [Vue d'ensemble](#vue-densemble)
- [Architecture du Système](#architecture-du-système)
- [Stack Technique](#stack-technique)
- [Démarrage Rapide](#démarrage-rapide)
- [Évaluation RAG](#évaluation-rag)
- [Perspectives d'Amélioration Future](#perspectives-damélioration-future)
- [Licence](#licence)

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/book-open.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Vue d'ensemble</h2>

Cet **Assistant RAG** est une plateforme avancée de question-réponse d'entreprise propulsée par l'Intelligence Artificielle. Conçue avec une architecture **Retrieval-Augmented Generation (RAG)**, l'application permet l'interrogation sémantique de larges bases documentaires métier en utilisant des LLM open-source et des bases de données vectorielles de pointe.

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/sitemap.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Architecture du Système</h2>

L'application repose sur une architecture moderne divisée en trois microservices principaux :

- <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/desktop.svg" width="16" height="16" align="center"> **Frontend** : Interface utilisateur interactive développée en **Angular**, offrant une expérience de chat conversationnel fluide.
- <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/server.svg" width="16" height="16" align="center"> **Backend Core** : API robuste en **Spring Boot (Java)** qui orchestre les requêtes de l'utilisateur, gère l'historique et assure la logique métier.
- <img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/brain.svg" width="16" height="16" align="center"> **Moteur RAG** : Service **Python / FastAPI** dédié à l'Intelligence Artificielle. Il s'occupe de l'intégration, de l'indexation vectorielle via **Qdrant**, et de la génération des réponses à l'aide de modèles locaux (**Ollama**) et de services cloud (**Groq / HuggingFace**).

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/layer-group.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Stack Technique</h2>

### Frontend
- **Framework :** Angular 
- **Langage :** TypeScript / HTML / CSS

### Backend 
- **Framework :** Spring Boot
- **Langage :** Java
- **Outil de build :** Maven

### Intelligence Artificielle & Base de Données
- **Langage :** Python
- **API :** FastAPI
- **Base Vectorielle :** Qdrant
- **LLMs :** Ollama (Local), Groq, HuggingFace
- **Évaluation :** RAGAS (Relevance, Faithfulness, Context Precision/Recall)

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/play.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Démarrage Rapide</h2>

### Prérequis
- Node.js & npm
- Java 17+ & Maven
- Python 3.10+
- Qdrant (disponible via Docker)
- Ollama (installé pour faire tourner les LLM en local)

### 1. Initialiser le Moteur RAG (Python)
```bash
cd masrvi-rag-engine
python -m venv zenvour
source zenvour/bin/activate  # ou zenvour\Scripts\activate sous Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Démarrer le Backend Core (Java)
```bash
cd masrvi-core-backend
mvn clean install
mvn spring-boot:run
```

### 3. Lancer l'Application Frontend (Angular)
```bash
cd masrvi-frontend
npm install
npm start
```

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/chart-line.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Évaluation RAG</h2>

Pour garantir la qualité des réponses générées par le LLM par rapport aux contextes récupérés, un module d'évaluation RAGAS est intégré :
```bash
cd masrvi-rag-engine/scripts
python evaluate_rag.py
```
> **Note :** *Pour des raisons de confidentialité, les rapports d'évaluation détaillés ainsi que les variables d'environnement locales ne sont pas stockés sur ce dépôt.*

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/lightbulb.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Perspectives d'Amélioration Future</h2>

Cet assistant a vocation à évoluer pour répondre à des besoins d'entreprise toujours plus complexes. Voici les principales axes d'évolution prévus :

1. **Intégration Multi-modale :** Support des modèles de vision (ex: LLaVA) pour l'analyse et l'extraction de schémas, graphiques et images dans les documents ingérés.
2. **Architecture Agentique (Routing & GraphRAG) :** Implémentation d'un routeur intelligent capable de diriger les questions complexes vers des agents spécialisés ou de s'appuyer sur des graphes de connaissances (GraphRAG).
3. **Sécurité et Contrôle d'Accès (RBAC) :** Intégration de Keycloak pour garantir que chaque utilisateur ne peut interroger que les documents auxquels ses droits l'autorisent.
4. **Déploiement Cloud-Native :** Mise en place d'une chaîne CI/CD complète, d'une conteneurisation Docker/Kubernetes globale, et d'un monitoring poussé avec Prometheus & Grafana.
5. **Boucle de Rétroaction (Feedback Loop) :** Ajout d'un système d'évaluation en direct par l'utilisateur (pouce vers le haut / bas) permettant d'affiner continuellement les métriques et les algorithmes de recherche sémantique.

---

<h2><img src="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/copyright.svg" width="24" height="24" align="center" style="margin-right: 10px;"> Contexte</h2>

Ce projet est développé dans le cadre d'un stage.
