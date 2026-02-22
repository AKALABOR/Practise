import os
import logging
import threading
from web3 import Web3

logger = logging.getLogger(__name__)

RPC_URL = os.getenv("WEB3_PROVIDER_URI", "http://ganache:8545")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

tx_lock = threading.Lock()
_local_nonce = None 

CONTRACT_ABI = [
	{
		"anonymous": false,
		"inputs": [
			{
				"indexed": true,
				"internalType": "uint256",
				"name": "sensorId",
				"type": "uint256"
			},
			{
				"indexed": false,
				"internalType": "int256",
				"name": "value",
				"type": "int256"
			},
			{
				"indexed": false,
				"internalType": "string",
				"name": "location",
				"type": "string"
			},
			{
				"indexed": false,
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"name": "MeasurementSaved",
		"type": "event"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_sensorId",
				"type": "uint256"
			},
			{
				"internalType": "int256",
				"name": "_value",
				"type": "int256"
			},
			{
				"internalType": "string",
				"name": "_location",
				"type": "string"
			}
		],
		"name": "saveMeasurement",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]

def send_data_to_blockchain(sensor_id: int, value: float, location: str):
    global _local_nonce 

    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))

        account = w3.eth.account.from_key(PRIVATE_KEY)
        contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

        int_value = int(value * 100)
        location_str = location if location else "Unknown"

        with tx_lock:
            if _local_nonce is None:
                _local_nonce = w3.eth.get_transaction_count(account.address, 'pending')

            current_nonce = _local_nonce

            tx = contract.functions.saveMeasurement(
                sensor_id, 
                int_value, 
                location_str
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 3000000,
                'gasPrice': w3.to_wei('10', 'gwei')
            })

            signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            _local_nonce += 1
        
        logger.info(f"[Запис збережено. Хеш: {w3.to_hex(tx_hash)}")
        
    except Exception as e:
        with tx_lock:
            _local_nonce = None
        logger.error(f"Помилка блокчейну: {e}")