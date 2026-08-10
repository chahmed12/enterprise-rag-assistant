#!/bin/bash
# =============================================================================
#  Masrvi — Script de test FastAPI + Spring Boot
#  Usage :  bash test_masrvi.sh    (depuis Git Bash, WSL ou Linux)
#  Prérequis : services démarrés (Ollama, Qdrant, RAG :8000, Spring :8080)
# =============================================================================
set -u

RAG="http://localhost:8000"
SPRING="http://localhost:8080"
QDRANT="http://localhost:6333"
PDF="/c/Users/MLAB/Downloads/Cahier_des_Charges_Assistant_RAG_Masrvi (1).pdf"

echo "==================== 1. SANTÉ ===================="
echo "-- RAG --"
curl -s $RAG/health
echo ""
echo "-- Qdrant (collections) --"
curl -s $QDRANT/collections | grep -o '"name":"[^"]*"' | head -5

echo ""
echo "==================== 2. INGESTION ===================="
echo "-- 1ère ingestion (via proxy Spring) --"
curl -s -X POST $SPRING/api/documents/ingest -F "file=@$PDF"
echo ""

echo "-- Attente de l'indexation (15 s)... --"
sleep 15
curl -s $QDRANT/collections/masrvi_docs | grep -o '"points_count":[0-9]*'
echo ""

echo "-- 2e ingestion du même document → doit refuser (déjà ingéré) --"
curl -s -X POST $SPRING/api/documents/ingest -F "file=@$PDF"
echo ""
echo "-- points_count inchangé (1 seul doc) --"
curl -s $QDRANT/collections/masrvi_docs | grep -o '"points_count":[0-9]*'
echo ""
echo "==================== 3. QUESTIONS (RAG direct) ===================="
echo "-- Question simple (nom de doc + score attendus) --"
curl -s -X POST $RAG/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le but du projet Masrvi ?"}'
echo ""

echo "-- Vérification : scores non-nuls dans les sources --"
curl -s -X POST $RAG/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le but du projet Masrvi ?"}' \
  | grep -o '"score":[0-9.]*' | head -5
echo ""

echo "-- Question avec filtres (basename) --"
curl -s -X POST $RAG/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le but du projet Masrvi ?", "source_filter":"Cahier_des_Charges_Assistant_RAG_Masrvi (1).pdf", "type_filter":"pdf"}'
echo ""

echo "-- Vérification dédup : citation avec le vrai nom du document (pas de placeholder) --"
curl -s -X POST $RAG/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le but du projet Masrvi ?"}' \
  | grep -o '\[[^]]*pdf[^]]*\]' | head -5
echo ""

echo "-- Question hors corpus (pas d'invention) --"
curl -s -X POST $RAG/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le code de la fusee Saturn V ?"}'
echo ""

echo "==================== 4. QUESTIONS (Spring Boot) ===================="
echo "-- Chat complet (score propagé dans les sources) --"
curl -s -X POST $SPRING/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le but du projet Masrvi ?"}' \
  | grep -o '"score":[0-9.]*' | head -5
echo ""

echo "-- Question avec apostrophe --"
curl -s -X POST $SPRING/api/chat/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Quelle est la procedure d'installation ?\"}"
echo ""

echo "-- Re-questionner la même session (sessionId=23, adapter si besoin) --"
curl -s -X POST $SPRING/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"sessionId":23,"question":"Et quelles sont les precautions ?"}'
echo ""

echo "-- Session invalide → HTTP 404 --"
curl -s -o /dev/null -w "%{http_code}\n" -X POST $SPRING/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"sessionId":99999,"question":"test"}'

echo "==================== 5. RELOAD ===================="
echo "-- Re-ingestion depuis corpus/ (dédup : les chunks sont remplacés, pas dupliqués) --"
curl -s -X POST $SPRING/api/documents/reload
echo ""
echo "-- Attente de l'indexation (30 s)... --"
sleep 30
curl -s $QDRANT/collections/masrvi_docs | grep -o '"points_count":[0-9]*'

echo "==================== 6. PERSISTANCE BASE (PostgreSQL) ===================="
PGPASSWORD=zenvour psql -h localhost -U postgres -d masrvidb \
  -c "SELECT id, role, LEFT(content,40) AS contenu FROM messages ORDER BY id DESC LIMIT 5;"
PGPASSWORD=zenvour psql -h localhost -U postgres -d masrvidb \
  -c "SELECT document_name, page, section, score FROM sources ORDER BY id DESC LIMIT 5;"

echo ""
echo "==================== 7. ROBUSTESSE : RAG arrêté → Spring 503 ===================="
echo "(stoppez le RAG puis relancez la commande du §4 — le chat doit répondre 503)"
echo ""
echo "==================== TERMINÉ ===================="
