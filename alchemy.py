import os
import requests
from collections import defaultdict

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
ALCHEMY_BASE_URL = f"https://base-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

ETH_ADDRESS = os.getenv("ETH_ADDRESS")
ETH_DECIMALS = 18
token_decimals_cache = {}

known = {
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3 Router",
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2 Router",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "Sushiswap Router",
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch Router",
    "0x8d12a197cb00d4747a1fe03395095ce2a5cc6819": "Coinbase Wallet",
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": "Binance Hot Wallet",
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "Tether Treasury",
    # Add more as needed
}

prefix_labels = {
    "0x4200": "Base Network Contract or Wallet",
    "0x28c6": "Binance Hot Wallet",
    "0x3f5c": "Binance Hot Wallet",
    "0x8d12": "Coinbase Wallet",
    "0xdac1": "Tether Treasury",
    "0x93": "Likely Base Network Wallet or Unknown Entity",
}

def get_label(address):
    address = address.lower()
    if address in known:
        return known[address]
    for prefix, label in prefix_labels.items():
        if address.startswith(prefix.lower()):
            return label
    return "Unknown"

def analyze_wallet(wallet):
    wallet = wallet.lower()
    tx_count = defaultdict(int)
    headers = {"Content-Type": "application/json"}

    def fetch_transfers(params):
        try:
            resp = requests.post(ALCHEMY_BASE_URL, json=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Error fetching transfers: {e}")
            return {}

    payload_from = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": "0x0",
            "toBlock": "latest",
            "fromAddress": wallet,
            "category": ["erc20"],
            "maxCount": "0x64",
            "excludeZeroValue": True,
            "order": "desc"
        }]
    }
    data_from = fetch_transfers(payload_from)
    transfers_from = data_from.get("result", {}).get("transfers", [])

    payload_to = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "alchemy_getAssetTransfers",
        "params": [{
            "fromBlock": "0x0",
            "toBlock": "latest",
            "toAddress": wallet,
            "category": ["erc20"],
            "maxCount": "0x64",
            "excludeZeroValue": True,
            "order": "desc"
        }]
    }
    data_to = fetch_transfers(payload_to)
    transfers_to = data_to.get("result", {}).get("transfers", [])

    for tx in transfers_from:
        to_addr = tx["to"].lower()
        tx_count[to_addr] += 1

    for tx in transfers_to:
        from_addr = tx["from"].lower()
        tx_count[from_addr] += 1

    sorted_peers = sorted(tx_count.items(), key=lambda x: -x[1])[:10]

    result = []
    for peer, count in sorted_peers:
        label = get_label(peer)
        peer_type = "protocol/cex" if label != "Unknown" else "wallet"
        result.append({
            "counterparty": peer,
            "tx_count": count,
            "type": peer_type,
            "label": label
        })

    return result

def fetch_all_incoming_transfers(wallet):
    transfers = []
    page_key = None

    while True:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "fromBlock": "0x0",
                "toBlock": "latest",
                "toAddress": wallet,
                "category": ["erc20", "external"],
                "maxCount": "0x64",
                "excludeZeroValue": True,
                "order": "desc"
            }]
        }

        if page_key:
            payload["params"][0]["pageKey"] = page_key

        headers = {"Content-Type": "application/json"}
        response = requests.post(ALCHEMY_BASE_URL, json=payload, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch transfers: {response.text}")

        result = response.json().get("result", {})
        batch_transfers = result.get("transfers", [])
        transfers.extend(batch_transfers)

        page_key = result.get("pageKey")
        if not page_key:
            break

    return transfers

def get_token_decimals(token_address):
    token_address = token_address.lower()
    if token_address == ETH_ADDRESS:
        return ETH_DECIMALS

    if token_address in token_decimals_cache:
        return token_decimals_cache[token_address]

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getTokenMetadata",
        "params": [token_address]
    }
    try:
        response = requests.post(ALCHEMY_BASE_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        decimals = data.get("result", {}).get("decimals", 18)
    except Exception as e:
        print(f"Failed to get decimals for {token_address}: {e}")
        decimals = 18

    token_decimals_cache[token_address] = decimals
    return decimals

def get_block_timestamp_from_alchemy(block_num_hex):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBlockByNumber",
        "params": [block_num_hex, False]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(ALCHEMY_BASE_URL, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch block {block_num_hex} timestamp: {response.text}")
        return None
    result = response.json().get("result")
    if result and "timestamp" in result:
        try:
            return int(result["timestamp"], 16)
        except Exception as e:
            print(f"Error parsing timestamp for block {block_num_hex}: {e}")
            return None
    return None