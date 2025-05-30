# Cypher Backend/API

Cypher is a Python-based API service that analyzes Ethereum and other ERC-20 wallet transactions and computes USD volume metrics over daily, weekly, and monthly periods. It integrates with Supabase for data storage and Alchemy for on-chain blockchain data.

Running server to try api endpoints : https://cypher-1lat.onrender.com (has a cold start of 15 mins after inactivity i believe )

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


### 2. Volume Over Time
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

### 3. Update todays data

**GET** /api/backfill

**Response:**

```json
 {"success": "backfill done"}
```

## 📁 Project Structure

```
cypher/
├── app.py                  # Main Flask app with API endpoints
├── alchemy.py              # Fetches on-chain transactions from Alchemy
├── aerodome.py             # Fetches ETH/USD prices with aerodome subgraph
├── supabase_client.py      # Initializes Supabase connection
├── usd_volume_analysis.py  # Computes and backfills daily/weekly/monthly USD volume
├── coingecko.py            # Unused aerodrome was used
├── requirements.txt        # Python dependencies
```

## 🛠️ Setup Instructions
  1. Clone the Repository
     ```
       git clone https://github.com/KaushikSiva/cypher.git
       cd cypher
     ```
  2. ```
     pip install -r requirements.txt
     ```
  3. setup env variables in env file
     ```
     ALCHEMY_API_KEY=yourkey
     AERODOME_API_KEY=yourkey
     COINGECKO_BASE_URL=yoururl
     ETH_ADDRESS=eth_addr
     WETH_ADDRESS=weth_addr
     ETH_NORMALIZED_ADDRESS=eth_norm_addr
     SUPABASE_URL=your_url
     SUPABASE_KEY=your_key
     MASTER_WALLET=your_wallet_id
     ```

4 . run the app
    ```
     python app.py
    ```
Server will run at localhost:5000


## 🕰️ Data Backfill & Pricing Notes
✅ Historical data has been backfilled up to May 18, 2025.

🔁 To backfill data for the current date, use API # 3

## 💰 Token Price Handling
Aerodrome subgraph was used to fetch historical token prices. For tokens where Aerodrome did not have historical prices:

The latest available price was used as a fallback.
If no price was available (for obscure or low-volume tokens), the price was assumed to be 0.
This may result in minor discrepancies in USD volume and balance calculations, but should not significantly affect aggregate values.

## 🔌 API Usage Summary
Alchemy was used to fetch all on-chain transaction data.
Aerodome was intended for price lookups but was not used due to issues with API key acquisition and instead CoinGecko was used
Supabase was the database used
Render was used for deployment

