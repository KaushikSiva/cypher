# Cypher API

Cypher is a Python-based API service that analyzes Ethereum wallet transactions and computes USD volume metrics over daily, weekly, and monthly periods. It integrates with Supabase for data storage and Alchemy for on-chain blockchain data.

## 📌 API Endpoints

### 1. Health Check

**GET** `/api/test`

Checks if the API is live.

**Response:**
```json
{ "status": "ok" }


### 2. Wallet Analysis
**GET** /api/wallet/<wallet_address>

Analyzes a given Ethereum wallet. Returns all unique counterparties, transaction counts, labels, and the direction of interaction (send/receive).

Path Parameter:

wallet_address — Ethereum wallet address to analyze.
