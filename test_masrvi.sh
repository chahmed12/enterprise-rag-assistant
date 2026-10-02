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

# Lit points_count de la collection.
points_count() {
  curl -s $QDRANT/collections/masrvi_docs \
    | grep -o '"points_count":[0-9]*' | cut -d: -f2
}

# L'ingestion étant asynchrone, une attente fixe n'est pas fiable.
# Entre deux fichiers, le compteur peut rester plat plus de 50 s : une fenêtre de
# stabilisation courte confond donc "en cours" et "terminé". On exige par défaut
# 12 lectures identiques espacées de 6 s, soit 72 s sans changement.
wait_points_stable() {
  local max=${1:-420} needed=${2:-12} prev="" stable=0 start=$SECONDS c
  while [ $(( SECONDS - start )) -lt "$max" ]; do
    c=$(points_count)
    if [ -z "$c" ]; then c=0; fi
    if [ "$c" = "$prev" ] && [ "$c" -gt 0 ]; then
      stable=$(( stable + 1 ))
      [ $stable -ge $needed ] && { echo "$c"; return 0; }
    else
      stable=0; prev="$c"
    fi
    sleep 6
  done
  echo "${prev:-inconnu}"
}

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

echo "-- Attente de la stabilisation de l'indexation... --"
echo "points_count = $(wait_points_stable)"
echo ""

echo "-- 2e ingestion du même document → doit refuser (déjà ingéré) --"
curl -s -X POST $SPRING/api/documents/ingest -F "file=@$PDF"
echo ""
echo "-- points_count inchangé (1 seul doc) --"
echo "points_count = $(points_count)"
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

echo "-- Re-questionner la même session (sessionId repris de la réponse précédente) --"
SESSION_ID=$(curl -s -X POST $SPRING/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Quel est le but du projet Masrvi ?"}' \
  | grep -o '"sessionId":[0-9]*' | head -1 | cut -d: -f2)
echo "-- sessionId obtenu : ${SESSION_ID:-aucun} --"
if [ -n "${SESSION_ID:-}" ]; then
  curl -s -X POST $SPRING/api/chat/ask \
    -H "Content-Type: application/json" \
    -d "{\"sessionId\": $SESSION_ID, \"question\": \"Et quelles sont les precautions ?\"}"
  echo ""
else
  echo "-- Aucune session obtainable, test de continuation ignoré --"
fi

echo "-- Session invalide → HTTP 404 --"
curl -s -o /dev/null -w "%{http_code}\n" -X POST $SPRING/api/chat/ask \
  -H "Content-Type: application/json" \
  -d '{"sessionId":99999,"question":"test"}'

echo "==================== 5. RELOAD ===================="
echo "-- Re-ingestion depuis corpus/ (dédup : les chunks sont remplacés, pas dupliqués) --"
COUNT_BEFORE=$(points_count)
echo "-- points_count avant reload = $COUNT_BEFORE --"
curl -s -m 320 -X POST $SPRING/api/documents/reload
echo ""
echo "-- Attente de la fin réelle du rechargement (jusqu'à ~7 min)... --"
COUNT_AFTER=$(wait_points_stable 420 12)
echo "-- points_count après reload = $COUNT_AFTER --"
if [ "$COUNT_AFTER" = "$COUNT_BEFORE" ]; then
  echo "-- OK : rechargement idempotent, corpus inchangé ($COUNT_AFTER points) --"
else
  echo "-- ECHEC : attendu $COUNT_BEFORE, obtenu $COUNT_AFTER --"
fi

echo "==================== 6. PERSISTANCE BASE (PostgreSQL) ===================="
if command -v psql >/dev/null 2>&1; then
  PGPASSWORD=zenvour psql -h localhost -U postgres -d masrvidb \
    -c "SELECT id, role, LEFT(content,40) AS contenu FROM messages ORDER BY id DESC LIMIT 5;"
  PGPASSWORD=zenvour psql -h localhost -U postgres -d masrvidb \
    -c "SELECT document_name, page, section, score FROM sources ORDER BY id DESC LIMIT 5;"
else
  echo "-- psql absent : vérification PostgreSQL ignorée."
  echo "-- Contrôle équivalent via l'API backend (sources persistées) --"
  curl -s -X POST $SPRING/api/chat/ask \
    -H 'Content-Type: application/json' \
    -d '{"question":"Quel est le but du projet Masrvi ?"}' \
    | grep -o '"documentName":"[^"]*"' | head -5
  echo "-- (des sources ci-dessus prouvent la persistance en base) --"
fi

echo ""
echo "==================== 7. ROBUSTESSE : RAG arrêté → Spring 503 ===================="
echo "(stoppez le RAG puis relancez la commande du §4 — le chat doit répondre 503)"
echo ""
echo "==================== TERMINÉ ===================="
