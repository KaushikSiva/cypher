# Cypher API

Cypher is a Python-based API service that analyzes Ethereum wallet transactions and computes USD volume metrics over daily, weekly, and monthly periods. It integrates with Supabase for data storage and Alchemy for on-chain blockchain data.

## 📌 API Endpoints


### 1. Wallet Analysis
**GET** /api/wallet/<wallet_address>

Analyzes a given Ethereum wallet. Returns all unique counterparties, transaction counts, labels, and the direction of interaction (send/receive).

Path Parameter:

wallet_address — Ethereum wallet address to analyze.

**Response:**
```json
[
  {
    "counterparty": "0xabc123...",
    "tx_count": 14,
    "type": "send",
    "label": "exchange"
  },
  {
    "counterparty": "0xdef456...",
    "tx_count": 6,
    "type": "receive",
    "label": "wallet"
  }
]

```


### 3. Volume Over Time
**GET** /api/volume

Returns total volume in USD sent from the master wallet over daily, weekly, and monthly timeframes.

**Response:**

```json
[
  {
    "date": "2025-05-17",
    "daily": 15000,
    "weekly": 105000,
    "monthly": 450000
  },
  {
    "date": "2025-05-16",
    "daily": 12000,
    "weekly": 98000,
    "monthly": 440000
  }
]
```


