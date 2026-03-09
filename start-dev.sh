#!/bin/bash

echo "Starting VaultLine Development Environment..."

docker start vaultline-db 2>/dev/null || docker run -d \
--name vaultline-db \
-e POSTGRES_PASSWORD=vaultpass123 \
-e POSTGRES_DB=vaultlinedb \
-p 5432:5432 postgres:15

echo "Starting ledger service..."
cd backend/ledger-service
uvicorn main:app --port 8000 &
cd ../..

echo "Starting auth service..."
cd backend/auth-service
uvicorn main:app --port 8001 &
cd ../..

echo "VaultLine services running!"
