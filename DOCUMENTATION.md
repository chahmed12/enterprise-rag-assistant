# MASRVI â€” Rapport technique du projet

> **Version :** 1.1 â€” 10/08/2026 *(refonte du client RAG : RestTemplate â†’ RestClient, DTO typÃ©s, timeouts, erreurs centralisÃ©es)*
> **PÃ©rimÃ¨tre :** `masrvi-project` (core-backend, rag-engine, frontend)
> **Diagrammes :** `MASRVI_CLASS_DIAGRAM.mmd` (Mermaid) / `MASRVI_CLASS_DIAGRAM.puml` (PlantUML) Ã  la racine

---

## Table des matiÃ¨res

1. [Introduction et objectifs](#1-introduction-et-objectifs)
2. [Vue d'ensemble architecturale](#2-vue-densemble-architecturale)
3. [Backend Spring Boot â€” masrvi-core-backend](#3-backend-spring-boot--masrvi-core-backend)
4. [Moteur RAG â€” masrvi-rag-engine](#4-moteur-rag--masrvi-rag-engine)
5. [Frontend Angular â€” masrvi-frontend](#5-frontend-angular--masrvi-frontend)
6. [Flux fonctionnels (diagrammes de sÃ©quence)](#6-flux-fonctionnels-diagrammes-de-sÃ©quence)
7. [ModÃ¨le de donnÃ©es relationnel](#7-modÃ¨le-de-donnÃ©es-relationnel)
8. [DÃ©cisions techniques](#8-dÃ©cisions-techniques)
9. [SÃ©curitÃ© et perspectives](#9-sÃ©curitÃ©-et-perspectives)

---

## 1. Introduction et objectifs

MASRVI est un **assistant RAG (Retrieval-Augmented Generation)** d'entreprise : l'utilisateur pose une question en langage naturel, le systÃ¨me rÃ©cupÃ¨re les passages pertinents dans une base de documents vectorielle (Qdrant), puis un LLM gÃ©nÃ¨re une rÃ©ponse fondÃ©e **exclusivement** sur ces extraits, en citant les sources (nom du document + page + section).

L'objectif fonctionnel est de fournir aux collaborateurs un accÃ¨s conversationnel Ã  la documentation interne, avec une garantie de **fiabilitÃ©** (aucune invention, rÃ©ponse bornÃ©e au contexte) et une **traÃ§abilitÃ©** (sources citÃ©es).

Le monorepo est composÃ© de trois modules :

| Module | Technologie | RÃ´le |
|---|---|---|
| `masrvi-core-backend` | Spring Boot 3.3 Â· Java 17 Â· PostgreSQL | API REST, persistance, orchestration, proxy vers le moteur RAG |
| `masrvi-rag-engine` | FastAPI Â· Python Â· LangChain Â· Qdrant | Ingestion de documents, vectorisation, recherche sÃ©mantique, gÃ©nÃ©ration de rÃ©ponses |
| `masrvi-frontend` | Angular | Interface utilisateur (squelette en cours) |

---

## 2. Vue d'ensemble architecturale

```mermaid
flowchart LR
    subgraph FE["Frontend Angular (:4200)"]
        APP["App (squelette)"]
    end

    subgraph BE["core-backend Spring Boot (:8080)"]
        CTRL["ContrÃ´leurs REST"]
        SVC["ChatService"]
        REPO["Repositories JPA"]
        CLIENT["RagEngineClient"]
    end

    subgraph RE["rag-engine FastAPI (:8000)"]
        API["/ask Â· /ingest Â· /reload"]
        PRO["process_document"]
        RET["search_passages"]
    end

    PG[(PostgreSQL)]
    QD[(Qdrant :6333)]

    APP -- HTTP/CORS --> CTRL
    CTRL --> SVC
    SVC --> REPO --> PG
    SVC -- REST --> CLIENT
    CLIENT -- HTTP --> API
    API --> RET --> QD
    API --> PRO --> QD
    API -- "LLM (Groq)" --> LLM["ChatGroq llama-3.1-8b-instant"]
    PRO -- "embeddings" --> EM["Ollama nomic-embed-text"]
    RET -- "embeddings" --> EM
```

**Flux gÃ©nÃ©ral d'une question :** Frontend â†’ Backend (`POST /api/chat/ask`) â†’ persistance du message utilisateur â†’ appel du moteur RAG (`/ask`) â†’ recherche vectorielle filtrÃ©e dans Qdrant â†’ construction du prompt RAG â†’ gÃ©nÃ©ration par le LLM â†’ persistance de la rÃ©ponse + sources â†’ retour du DTO au frontend.

---

## 3. Backend Spring Boot â€” masrvi-core-backend

### 3.1 Structure des packages

```
com.masrvi.core
â”œâ”€â”€ MasrviCoreApplication.java        Point d'entrÃ©e Spring Boot
â”œâ”€â”€ client/RagEngineClient.java       Client HTTP (RestClient) vers le moteur RAG (FastAPI)
â”œâ”€â”€ config/                           Configurations Spring
â”‚   â”œâ”€â”€ CorsConfig.java               CORS (frontend Angular)
â”‚   â””â”€â”€ RestClientConfig.java         Bean RestClient + timeouts vers le moteur RAG
â”œâ”€â”€ controller/                       Couche API REST
â”‚   â”œâ”€â”€ ChatController.java
â”‚   â”œâ”€â”€ ChatSessionController.java
â”‚   â””â”€â”€ DocumentController.java
â”œâ”€â”€ dto/                              Objets de transfert
â”‚   â”œâ”€â”€ AskRequestDTO.java            (record)
â”‚   â”œâ”€â”€ ChatMessageDTO.java           (record)
â”‚   â”œâ”€â”€ ChatResponseDTO.java          (record)
â”‚   â”œâ”€â”€ IngestResponseDTO.java        (record, rÃ©ponse typÃ©e /ingest)
â”‚   â”œâ”€â”€ ReloadResponseDTO.java        (record, rÃ©ponse typÃ©e /reload)
â”‚   â”œâ”€â”€ SourceDTO.java                (record)
â”‚   â””â”€â”€ ChatSessionSummaryDTO.java    (classe @Data + @Builder)
â”œâ”€â”€ entity/                           EntitÃ©s JPA
â”‚   â”œâ”€â”€ ChatSession.java
â”‚   â”œâ”€â”€ Message.java
â”‚   â”œâ”€â”€ Source.java
â”‚   â””â”€â”€ DocumentMetadata.java
â”œâ”€â”€ exception/                        Gestion des erreurs
â”‚   â”œâ”€â”€ GlobalExceptionHandler.java
â”‚   â””â”€â”€ RagEngineException.java
â”œâ”€â”€ repository/                       AccÃ¨s aux donnÃ©es (Spring Data JPA)
â”‚   â”œâ”€â”€ ChatSessionRepository.java
â”‚   â”œâ”€â”€ MessageRepository.java
â”‚   â””â”€â”€ DocumentMetadataRepository.java
â””â”€â”€ service/ChatService.java          Logique mÃ©tier
```

### 3.2 ModÃ¨le de donnÃ©es (entitÃ©s JPA)

#### `ChatSession` â€” table `chat_sessions`
Une session de conversation.

| Attribut | Type | Contrainte | Description |
|---|---|---|---|
| `id` | `Long` | `@Id`, auto-gÃ©nÃ©rÃ© | Identifiant |
| `title` | `String` | â€” | Titre affichÃ© |
| `createdAt` | `LocalDateTime` | `@Column(nullable = false)` | Date de crÃ©ation, posÃ©e par `@PrePersist` |
| `messages` | `List<Message>` | `@OneToMany(mappedBy="chatSession", cascade=ALL, orphanRemoval=true)` | Messages de la session |

#### `Message` â€” table `messages`
Un message Ã©changÃ© (utilisateur ou IA).

| Attribut | Type | Contrainte | Description |
|---|---|---|---|
| `id` | `Long` | `@Id`, auto-gÃ©nÃ©rÃ© | Identifiant |
| `role` | `String` | `nullable=false` | `"USER"` ou `"AI"` |
| `content` | `String` | `columnDefinition="TEXT"` | Contenu du message |
| `timestamp` | `LocalDateTime` | `nullable=false` | Horodatage, posÃ© par `@PrePersist` |
| `chatSession` | `ChatSession` | `@ManyToOne(fetch=LAZY)`, `@JoinColumn("session_id")` | Session parente |
| `sources` | `List<Source>` | `@OneToMany(mappedBy="message", cascade=ALL, orphanRemoval=true)` | Sources ayant servi Ã  la rÃ©ponse |

#### `Source` â€” table `sources`
Une source citÃ©e dans une rÃ©ponse IA.

| Attribut | Type | Contrainte | Description |
|---|---|---|---|
| `id` | `Long` | `@Id`, auto-gÃ©nÃ©rÃ© | Identifiant |
| `documentName` | `String` | `nullable=false` | Nom du document |
| `page` | `Integer` | â€” | NumÃ©ro de page (nullable, ex. fichier `.txt`) |
| `section` | `String` | â€” | Section du document (ex. Â« Chapitre 2 Â») |
| `score` | `Double` | â€” | Score de pertinence renvoyÃ© par le moteur RAG |
| `message` | `Message` | `@ManyToOne(fetch=LAZY)`, `@JoinColumn("message_id")` | Message IA associÃ© |

#### `DocumentMetadata` â€” table `documents`
MÃ©tadonnÃ©es des documents indexÃ©s (non encore branchÃ© au flux d'ingestion).

| Attribut | Type | Contrainte | Description |
|---|---|---|---|
| `id` | `Long` | `@Id`, auto-gÃ©nÃ©rÃ© | Identifiant |
| `filename` | `String` | `nullable=false` | Nom du fichier |
| `uploadDate` | `LocalDateTime` | `nullable=false` | Date d'upload, posÃ©e par `@PrePersist` |
| `status` | `String` | `nullable=false` | `"PROCESSING"`, `"INDEXED"`, `"ERROR"` |

### 3.3 Relations JPA et cascade

Les relations bidirectionnelles sont des **compositions** en UML (losange plein) : le cycle de vie de l'enfant dÃ©pend entiÃ¨rement du parent, grÃ¢ce Ã  `cascade = CascadeType.ALL` + `orphanRemoval = true`.

```mermaid
classDiagram
    direction LR
    class ChatSession {
        -Long id
        -String title
        -LocalDateTime createdAt
    }
    class Message {
        -Long id
        -String role
        -String content
        -LocalDateTime timestamp
    }
    class Source {
        -Long id
        -String documentName
        -Integer page
        -String section
        -Double score
    }
    ChatSession "1" *-- "*" Message : contient (cascade ALL, orphanRemoval)
    Message "*" --> "1" ChatSession : @ManyToOne
    Message "1" *-- "*" Source : possÃ¨de (cascade ALL, orphanRemoval)
    Source "*" --> "1" Message : @ManyToOne
```

**ConsÃ©quences pratiques :**
- Enregistrer un `ChatSession` (ou `Message`) persiste rÃ©cursivement ses enfants.
- Supprimer un parent supprime ses enfants (`orphanRemoval`).
- Les relations navigables `@ManyToOne` sont en chargement **LAZY** pour Ã©viter de charger l'objet graph complet inutilement.
- `@ToString` et `@EqualsAndHashCode` excluent les relations pour Ã©viter les boucles infinies de sÃ©rialisation / de comparaison.

### 3.4 Couche DTO

Les DTO isolent l'API de la reprÃ©sentation persistÃ©e. Quatre sont des **records** Java (immuables, gÃ©nÃ©ration automatique de `constructor`, accesseurs `field()`, `equals/hashCode/toString`) ; un seul est une classe Lombok `@Data` + `@Builder`.

| DTO | Type | Champs | RÃ´le |
|---|---|---|---|
| `AskRequestDTO` | `record` | `sessionId`, `question`, `sourceFilter`, `typeFilter` | RequÃªte d'une question |
| `ChatMessageDTO` | `record` | `id`, `role`, `content`, `timestamp`, `sources: List<SourceDTO>` | Message exposÃ© Ã  l'API |
| `ChatResponseDTO` | `record` | `sessionId`, `userMessage`, `aiMessage` | RÃ©ponse complÃ¨te d'un `ask` |
| `SourceDTO` | `record` | `documentName` (alias JSON `document_name`), `page`, `score`, `section` | Source exposÃ©e Ã  l'API |
| `ChatSessionSummaryDTO` | classe `@Data @Builder` | `id`, `title`, `createdAt`, `messageCount` | RÃ©sumÃ© d'une session pour la liste |

**Pourquoi records :** immutabilitÃ© (pas de mutation accidentelle), zÃ©ro boilerplate, sÃ©rialisation Jackson native (Spring Boot 3). Le `@JsonAlias("document_name")` de `SourceDTO` gÃ¨re le format snake_case renvoyÃ© par le moteur Python.
**Pourquoi `ChatSessionSummaryDTO` est une classe :** historique d'Ã©criture ; il est construit via un builder fluent dans `ChatService` (lisibilitÃ© du mapping). Une conversion en record est possible sans changement fonctionnel.

### 3.5 Couche Repository

Interface Spring Data JPA, hÃ©ritant de `JpaRepository<T, Long>` :

| Repository | MÃ©thodes |
|---|---|
| `ChatSessionRepository` | hÃ©ritÃ©es (`findAll`, `findById`, `save`â€¦) |
| `MessageRepository` | hÃ©ritÃ©es + `findByChatSessionIdOrderByTimestampAsc(Long)` |
| `DocumentMetadataRepository` | hÃ©ritÃ©es |

### 3.6 Couche service â€” `ChatService`

Classe centrale, annotÃ©e `@Service`, construite par injection de constructeur (`@RequiredArgsConstructor`).

| MÃ©thode | Description |
|---|---|
| `ask(AskRequestDTO) : ChatResponseDTO` | Orchestration complÃ¨te d'une question (voir 3.7) |
| `getAllSessions() : List<ChatSessionSummaryDTO>` | Liste des sessions rÃ©sumÃ©es (lecture seule) |
| `getSessionMessages(Long) : List<ChatMessageDTO>` | Historique d'une session, ordonnÃ© par timestamp ; lÃ¨ve `EntityNotFoundException` si absente |
| `toDTO(Message) : ChatMessageDTO` | Mapping privÃ© entitÃ© â†’ DTO (flat, sans relation cyclique) |

### 3.7 Flux `ask` â€” sÃ©quence dÃ©taillÃ©e

```
1.  RÃ©cupÃ©rer la session (request.sessionId) ou en crÃ©er une nouvelle
    â†’ title = "Session du {date du jour}"
2.  Persister le message USER (role="USER", content=question)
3.  Hors transaction : appeler le moteur RAG via RagEngineClient.ask()
    (pas de @Transactional pour ne pas bloquer la base pendant l'appel HTTP)
4.  Persister la rÃ©ponse IA (role="AI", content=rÃ©ponse du moteur)
5.  Si le moteur a renvoyÃ© des sources â†’ les mapper en entitÃ©s Source
    et les rattacher au message IA (sauvegardÃ©es en cascade par JPA)
6.  Construire et retourner ChatResponseDTO(sessionId, userMessage, aiMessage)
```

**Point de vigilance :** `getAllSessions()` accÃ¨de Ã  `s.getMessages().size()` ; le `@Transactional(readOnly=true)` garantit la disponibilitÃ© de la relation lazy dans ce contexte.

### 3.8 API REST

| MÃ©thode | Endpoint | ContrÃ´leur | Description |
|---|---|---|---|
| `POST` | `/api/chat/ask` | `ChatController` | Poser une question (JSON `AskRequestDTO`) |
| `GET` | `/api/chat/sessions` | `ChatSessionController` | Liste rÃ©sumÃ©e des sessions |
| `GET` | `/api/chat/sessions/{id}/messages` | `ChatSessionController` | Historique complet d'une session |
| `POST` | `/api/documents/ingest` | `DocumentController` | Uploader un document (multipart) vers le moteur RAG |
| `POST` | `/api/documents/reload` | `DocumentController` | Recharger l'index depuis le corpus |

### 3.9 Client RAG â€” `RagEngineClient`

Proxy HTTP vers le moteur RAG, basÃ© sur **`RestClient`** (Spring 6.1, successeur de `RestTemplate`). La connexion est configurÃ©e dans `config/RestClientConfig.java` (bean `RestClient` avec `baseUrl` = `rag.engine.url` â†’ `http://localhost:8000` et **timeouts** : 5 s connexion / 60 s rÃ©ponse).

| MÃ©thode | Endpoint cible | Corps |
|---|---|---|
| `ask(question, sourceFilter, typeFilter) : RagResponse` | `POST /ask` | JSON `{question, source_filter?, type_filter?}` |
| `reload() : ReloadResponseDTO` | `POST /reload` | â€” |
| `ingest(MultipartFile) : IngestResponseDTO` | `POST /ingest` | `multipart/form-data` (fichier) |

La classe imbriquÃ©e `RagResponse` (`@Data`) porte `reponse` et `sources: List<SourceDTO>`. `reload()` et `ingest()` retournent des **DTO typÃ©s** (`ReloadResponseDTO`, `IngestResponseDTO`) dont les `@JsonProperty` conservent le format snake_case du moteur Python (`file_name`, `nb_passages`) â€” contrat API identique Ã  l'ancien relais de `Map`.

**Gestion d'erreurs centralisÃ©e** dans `RagEngineClient.execute()` :
- erreurs **HTTP 4xx/5xx** â†’ `onStatus` + `handleError` â†’ `RagEngineException` avec le corps de la rÃ©ponse ;
- erreurs **rÃ©seau/techniques** (`RestClientException`) â†’ enveloppÃ©es en `RagEngineException`.

Les services appelants n'ont plus Ã  gÃ©rer les erreurs eux-mÃªmes (`ChatService` a Ã©tÃ© simplifiÃ©) : tout aboutit Ã  `GlobalExceptionHandler` â†’ HTTP 503.

### 3.10 Gestion des exceptions

`GlobalExceptionHandler` (`@ControllerAdvice`) centralise les rÃ©ponses d'erreur :

| Exception | HTTP | Message |
|---|---|---|
| `RagEngineException` (IA indisponible) | `503 Service Unavailable` | Â« Erreur de communication avec le moteur RAG Â» |
| `EntityNotFoundException` (JPA) | `404 Not Found` | Message du service (ex. session inexistante) |

Le corps est normalisÃ© : `{timestamp, status, error, message}`.

### 3.11 Configuration â€” `application.properties`

| PropriÃ©tÃ© | Valeur | RÃ´le |
|---|---|---|
| `server.port` | `8080` | Port du backend |
| `spring.datasource.url` | `jdbc:postgresql://localhost:5432/masrvidb` | Base PostgreSQL |
| `spring.jpa.hibernate.ddl-auto` | `update` | CrÃ©ation/maj des tables sans perte (dev) |
| `rag.engine.url` | `http://localhost:8000` | URL du moteur RAG |
| `masrvi.frontend.url` | `http://localhost:4200` | Origine CORS autorisÃ©e (Angular) |

---

## 4. Moteur RAG â€” masrvi-rag-engine

### 4.1 RÃ´le

Convertir des documents en **chunks vectorisÃ©s** stockÃ©s dans Qdrant, puis, pour chaque question : rechercher les chunks les plus pertinents, construire un prompt strict, et demander au LLM une rÃ©ponse **bornÃ©e au contexte** avec citations.

```
masrvi-rag-engine
â”œâ”€â”€ app/main.py                 Application FastAPI (endpoints)
â”œâ”€â”€ app/models.py               ModÃ¨les Pydantic
â”œâ”€â”€ core/exchange.py            GÃ©nÃ©ration de rÃ©ponse RAG
â”œâ”€â”€ core/process_document.py    Pipeline d'ingestion
â”œâ”€â”€ retrieval/qdrant_client.py  AccÃ¨s Qdrant (index, recherche, filtres)
â”œâ”€â”€ retrieval/semantic_chunker.py  DÃ©coupage sÃ©mantique
â”œâ”€â”€ utils/clients.py            Embeddings (Ollama/HF) + LLM (Groq)
â””â”€â”€ config.py                   Constantes d'environnement
```

### 4.2 API FastAPI

| MÃ©thode | Endpoint | ModÃ¨le rÃ©ponse | Description |
|---|---|---|---|
| `GET` | `/health` | â€” | Sonde de santÃ© |
| `POST` | `/ask` | `AnswerResponse` | RÃ©pond Ã  une question (avec filtres optionnels) |
| `POST` | `/ingest` | `IngestResponse` | IngÃ¨re un fichier en arriÃ¨re-plan |
| `POST` | `/reload` | `ReloadResponse` | Vide l'index et re-ingÃ¨re depuis `corpus/` |

### 4.3 ModÃ¨les Pydantic (`app/models.py`)

| ModÃ¨le | Champs |
|---|---|
| `SourceItem` | `document_name`, `page?`, `score?`, `section?` |
| `QuestionRequest` | `question`, `source_filter?`, `type_filter?` |
| `AnswerResponse` | `reponse`, `sources: List[SourceItem]` |
| `IngestResponse` | `file_name`, `nb_passages?`, `messages` |
| `ReloadResponse` | `messages` |

### 4.4 Flux d'ingestion (`core/process_document.py`)

```
1.  Choisir le loader selon l'extension (.pdf, .txt, .md, .docx, .html)
2.  Extraire le texte :
    â€¢ PDF  â†’ pymupdf4llm.to_markdown (1 document par page, metadata.page)
    â€¢ Autres â†’ loader LangChain (TextLoader, Docx2txtLoader, BSHTMLLoader)
3.  Nettoyer le texte (espaces multiples, sauts de ligne redondants)
4.  DÃ©couper en chunks (voir 4.6)
5.  Enrichir les mÃ©tadonnÃ©es de chaque chunk :
    â€¢ type   = extension du fichier
    â€¢ section = titre Markdown le plus profond (Header 1â†’3)
6.  DÃ©dupliquer : supprimer les anciens chunks du mÃªme document (delete_document)
7.  Vectoriser et indexer dans Qdrant (get_vector_store().add_documents)
8.  Copier le fichier source dans corpus/ (persistance pour le rechargement)
```

### 4.5 Flux d'interrogation (`core/exchange.py`)

```
1.  search_passages(question, source_filter, type_filter)
    â†’ top-K chunks (K = SEARCH_K) + scores (cosinus)
2.  Si aucun rÃ©sultat ou score max < SEARCH_K seuil (0.65)
    â†’ rÃ©ponse Â« Je n'ai pas trouvÃ© d'information pertinente Â»
3.  Sinon, construire le CONTEXTE :
    [Nom_Document, page N, section S] + texte des chunks
4.  Remplir le prompt RAG (RAG_PROMPT_TEMPLATE) :
    â€¢ RÃ©pondre EXCLUSIVEMENT avec le contexte
    â€¢ Si introuvable â†’ Â« Je ne trouve pas cette information dans les documents fournis. Â»
    â€¢ Citer chaque affirmation : [Nom_RÃ©el_Du_Document, Page X]
    â€¢ Ton professionnel + Markdown
5.  GÃ©nÃ©rer avec ChatGroq (temperature=0) et retourner {reponse, sources}
```

### 4.6 Chunking sÃ©mantique (`retrieval/semantic_chunker.py`)

Deux Ã©tages :
1. **Structure** : `MarkdownHeaderTextSplitter` dÃ©coupe par titres (`#`, `##`, `###`) ; les titres non rÃ©pÃ©tÃ©s sont propagÃ©s aux splits suivants (mÃ©moire d'en-tÃªtes) ; les mÃ©tadonnÃ©es de page/source sont fusionnÃ©es.
2. **Taille** : `RecursiveCharacterTextSplitter` (langage Markdown) avec `CHUNK_SIZE=1000` et `CHUNK_OVERLAP=200`.

Ceci prÃ©serve la sÃ©mantique (une section = une unitÃ©) tout en bornant la taille des vecteurs.

### 4.7 Recherche vectorielle (`retrieval/qdrant_client.py`)

| Fonction | Description |
|---|---|
| `get_vector_store()` | CrÃ©e/retourne la connexion Qdrant (collection `masrvi_docs`, vecteurs 768D, distance COSINE) |
| `search_passages(question, source_filter, type_filter)` | Recherche de similaritÃ© + score, avec filtres Qdrant optionnels sur `metadata.source` et `metadata.type` |
| `delete_document(source)` | Supprime tous les chunks d'un document (anti-doublon) |
| `document_exists(source)` | VÃ©rifie la prÃ©sence d'un document dans l'index |
| `clear_collection()` | Supprime la collection (utilisÃ© par `/reload`) |

### 4.8 Infrastructure externe

- **Qdrant** (`:6333`) : base vectorielle, collection `masrvi_docs`.
- **Embeddings** : `OllamaEmbeddings` (`nomic-embed-text`, 768D) par dÃ©faut ; bascule possible vers HuggingFace via `USE_OLLAMA_EMBEDDINGS=false`.
- **LLM** : `ChatGroq` (`llama-3.1-8b-instant`, `temperature=0`) via `GROQ_API_KEY`.

### 4.9 Configuration (`config.py`)

| Variable | DÃ©faut | RÃ´le |
|---|---|---|
| `QDRANT_URL` | `http://localhost:6333` | Adresse Qdrant |
| `COLLECTION_NAME` | `masrvi_docs` | Nom de la collection |
| `SEARCH_K` | `5` | Nombre de chunks retournÃ©s |
| `RELEVANCE_THRESHOLD` | `0.65` | Seuil de pertinence |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1000` / `200` | ParamÃ¨tres de chunking |
| `CORPUS_DIR` | `corpus` | Dossier des fichiers sources permanents |
| `LLM_MODEL` / `GROQ_API_KEY` | `llama-3.1-8b-instant` | ModÃ¨le LLM Groq |

---

## 5. Frontend Angular â€” masrvi-frontend

Le frontend est une **interface de chat Angular** (nouvelle syntaxe : `signal`, `provideRouter`, hydration SSR). Il comprend la sidebar (historique des sessions), la zone de chat et les cartes de sources.

| Ã‰lÃ©ment | RÃ´le |
|---|---|
| `app.ts` / `app.html` / `app.css` | Composant racine |
| `app.config.ts` | Configuration (router, event replay, hydration) |
| `app.routes.ts` | Routes (vide actuellement) |

Le backend autorise dÃ©jÃ  son origine (`CorsConfig` : `http://localhost:4200`).

---

## 6. Flux fonctionnels (diagrammes de sÃ©quence)

### 6.1 Poser une question (`POST /api/chat/ask`)

```mermaid
sequenceDiagram
    participant F as Frontend
    participant C as ChatController
    participant S as ChatService
    participant R as MessageRepository
    participant G as RagEngineClient
    participant P as RAG Engine (FastAPI)
    participant Q as Qdrant
    participant L as LLM (Groq)

    F->>C: POST /api/chat/ask {question}
    C->>S: ask(request)
    S->>R: save(Message USER)
    S->>G: ask(question, filters)
    G->>P: POST /ask
    P->>Q: search_passages (top-K)
    Q-->>P: chunks + scores
    P->>L: prompt RAG (contexte bornÃ©)
    L-->>P: rÃ©ponse
    P-->>G: {reponse, sources}
    G-->>S: RagResponse
    S->>R: save(Message AI + Sources cascade)
    S-->>C: ChatResponseDTO
    C-->>F: 200 OK (JSON)
```

### 6.2 IngÃ©rer un document (`POST /api/documents/ingest`)

```mermaid
sequenceDiagram
    participant F as Frontend
    participant D as DocumentController
    participant G as RagEngineClient
    participant P as RAG Engine (FastAPI)
    participant PRO as process_file_task
    participant Q as Qdrant

    F->>D: POST /api/documents/ingest (multipart)
    D->>G: ingest(file)
    G->>P: POST /ingest
    P->>PRO: background task (async)
    PRO->>PRO: extraire, nettoyer, chunker
    PRO->>PRO: enrichir metadata (type, section)
    PRO->>Q: delete_document (anti-doublon)
    PRO->>Q: add_documents (vectorisation)
    P-->>G: {file_name, messages}
    G-->>D: 200 OK
    D-->>F: 200 OK
```

---

## 7. ModÃ¨le de donnÃ©es relationnel

```mermaid
erDiagram
    chat_sessions {
        BIGINT id PK
        VARCHAR title
        TIMESTAMP created_at
    }
    messages {
        BIGINT id PK
        VARCHAR role
        TEXT content
        TIMESTAMP timestamp
        BIGINT session_id FK
    }
    sources {
        BIGINT id PK
        VARCHAR document_name
        INTEGER page
        VARCHAR section
        DOUBLE score
        BIGINT message_id FK
    }
    documents {
        BIGINT id PK
        VARCHAR filename
        TIMESTAMP upload_date
        VARCHAR status
    }

    chat_sessions ||--o{ messages : "contient"
    messages ||--o{ sources : "possÃ¨de"
```

| Table | RÃ´le | Relations |
|---|---|---|
| `chat_sessions` | Sessions de chat | 1 â†’ N `messages` |
| `messages` | Messages USER/AI | N â†’ 1 `chat_sessions`, 1 â†’ N `sources` |
| `sources` | Sources citÃ©es | N â†’ 1 `messages` |
| `documents` | MÃ©tadonnÃ©es des documents | autonome (Ã  brancher) |

---

## 8. DÃ©cisions techniques

| Sujet | DÃ©cision | Justification |
|---|---|---|
| DTO | **Records Java** majoritairement | ImmutabilitÃ©, zÃ©ro boilerplate, sÃ©rialisation Jackson native |
| Un DTO | `ChatSessionSummaryDTO` en classe `@Data @Builder` | Construction par Ã©tapes pour lisibilitÃ© ; convertible en record |
| EntitÃ©s | Lombok (`@Getter/@Setter/@Builder/@NoArgs/AllArgs`) + `@PrePersist` | RÃ©duction du code, horodatages automatiques |
| Cascade | `cascade = ALL` + `orphanRemoval` | Cycle de vie gÃ©rÃ© par le parent (composition) |
| Recherche | Vectorielle Qdrant (cosinus, 768D) | Pertinence sÃ©mantique |
| FidÃ©litÃ© | Prompt RAG strict + `temperature=0` | RÃ©ponses bornÃ©es au contexte, sources citÃ©es |
| Seuil | `RELEVANCE_THRESHOLD = 0.65` | Ã‰viter les rÃ©ponses sur des passages non pertinents |
| Chunking | MarkdownHeader + Recursive (1000/200) | Sections conservÃ©es, tailles bornÃ©es |
| Transactions | `ask()` sans `@Transactional` ; lectures en `readOnly` | Ne pas bloquer la base pendant l'appel HTTP long |
| Client HTTP | **`RestClient`** + timeouts (5 s / 60 s) | Successeur de `RestTemplate` : fluent, gestion d'erreurs `onStatus`, attente bornÃ©e |
| RÃ©ponses RAG | **DTO typÃ©s** (`ReloadResponseDTO`, `IngestResponseDTO`) | SchÃ©mas Python vÃ©rifiÃ©s par Jackson, contrat snake_case conservÃ© |
| Erreurs RAG | CentralisÃ©es dans `RagEngineClient` â†’ `RagEngineException` | Les services appelants restent simples ; mapping unique vers HTTP 503 |

