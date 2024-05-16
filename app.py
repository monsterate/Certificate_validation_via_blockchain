from flask import Flask, render_template, request
from datetime import datetime
from web3 import Web3
from hexbytes import HexBytes
import hashlib
from web3.middleware import construct_sign_and_send_raw_middleware
from eth_account import Account


app = Flask(__name__)

infura_url = 'https://sepolia.infura.io/v3/3de4de810fe54166bd043b152d234ce8'
w3 = Web3(Web3.HTTPProvider(infura_url))

# Account private key
private_key = "private_key"

# Convert private key to account object
account = Account.from_key(private_key)

# Inject middleware to sign transactions locally
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(private_key))



# Check connection status
if w3.is_connected():
    print("Connected to Ethereum node")
else:
    print("Failed to connect to Ethereum node")

# Load the compiled smart contract ABI
contract_abi = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "bytes32",
                "name": "hash",
                "type": "bytes32"
            }
        ],
        "name": "CertificateAdded",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32"
            }
        ],
        "name": "addCertificateHash",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "",
                "type": "bytes32"
            }
        ],
        "name": "certificateHashes",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "bytes32",
                "name": "_hash",
                "type": "bytes32"
            }
        ],
        "name": "verifyCertificate",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
  # Your smart contract ABI
contract_address = Web3.to_checksum_address('0xbd7131325a4fc9aa915532029fc82cf6db03e7d7') # Your smart contract address

# Instantiate the contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    

@app.route('/')
def hello_world():
    return render_template('index.html')
    # return 'Hello, World!'
    
@app.route('/add', methods=['GET', 'POST'])
def add():
    hashed_data = None
    if request.method == 'POST':
        print(request.form['name'])
        print(request.form['certificate'])
        print(request.form['certificate_number'])
        name = request.form['name']
        issuer = request.form['certificate']
        issue_date = request.form['issue_date']
        certificate_number = request.form['certificate_number']

        # Concatenate input values
        concatenated_data = f"{name}{issuer}{issue_date}{certificate_number}"

        # Hash the concatenated data using SHA-256
        hashed_data = hashlib.sha256(concatenated_data.encode()).hexdigest()
        print(f"hash: {hashed_data}")

        # Store the hash value on the blockchain
        store_hash_on_blockchain(hashed_data)

    # return render_template('add.html')
    return render_template('add.html', hashed = hashed_data)

# Function to send signed transaction
def send_signed_transaction(tx):
    raw_tx = account.sign_transaction(tx)
    return w3.eth.send_raw_transaction(raw_tx.rawTransaction)

def store_hash_on_blockchain(hash_value):
    # Convert hash value to bytes32
    hash_bytes32 = HexBytes(hash_value)
    
    try:
        # Build the transaction
        tx = contract.functions.addCertificateHash(hash_bytes32).build_transaction({
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 1000000,  # Adjust gas limit as needed
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        })

        # Sign and send the transaction
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        # Wait for the transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    except Exception as e:
        print("Error occurred during transaction:", e)
        return None    
    

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    result = ""
    if request.method == 'POST':
        user_hash = request.form['hashCode']
        print("Received hash code:", user_hash)
        
        # Convert hash code string to bytes32
        user_hash_bytes32 = HexBytes(user_hash)

        #  Call contract function to verify hash
        is_verified = contract.functions.verifyCertificate(user_hash_bytes32).call()
        print("Verification result:", is_verified)

        # # Display result to user
        if is_verified:
            result = "Sucessfull"
        else:
            result = "Unsucessfull"
        print("Result:", result)
    return render_template('verify.html' , result= result)

@app.route('/products')
def product():
    return 'This is Products Page.'

if __name__ == "__main__":
    app.run(debug=True, port=8000)
