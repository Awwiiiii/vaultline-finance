#!/bin/bash

echo "Starting VaultLine Development Environment..."

# kill old servers
pkill -f uvicorn 2>/dev/null

# start postgres container
docker start vaultline-db 2>/dev/null || docker run -d \
--name vaultline-db \
-e POSTGRES_PASSWORD=vaultpass123 \
-e POSTGRES_DB=vaultlinedb \
-p 5432:5432 postgres:15

echo "Starting ledger service..."
cd backend/ledger-service
uvicorn main:app --host 0.0.0.0 --port 8000 &

echo "Starting auth service..."
cd ../auth-service
uvicorn main:app --host 0.0.0.0 --port 8001 &

cd ../..

echo "VaultLine services running!"

