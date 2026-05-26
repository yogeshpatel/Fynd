#!/usr/bin/env bash
BASE_URL="${1:-http://127.0.0.1:8000}"

echo "=== Testing $BASE_URL ==="
echo ""

echo "--- GET /api/hello ---"
curl -s "$BASE_URL/api/hello" | python3 -m json.tool
echo ""

echo "--- GET /api/available-documents ---"
curl -s "$BASE_URL/api/available-documents" | python3 -m json.tool
echo ""

echo "--- POST /api/docscan (retrieval only) ---"
curl -s -X POST "$BASE_URL/api/docscan?usellm=false" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this project?"}' | python3 -m json.tool
echo ""

echo "--- POST /api/reindex ---"
curl -s -X POST "$BASE_URL/api/reindex" | python3 -m json.tool
echo ""

echo "--- POST /api/documents (add test doc) ---"
curl -s -X POST "$BASE_URL/api/documents" \
  -H "Content-Type: application/json" \
  -d '{"source": "test_doc.md", "text": "This is a test document added via API."}' \
  | python3 -m json.tool
echo ""
