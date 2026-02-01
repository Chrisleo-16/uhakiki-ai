from pymilvus import connections, utility

def check_vault_connection():
    print("[VAULT] Attempting to handshake with Milvus...")
    try:
        # Connect to the Milvus service running in your Docker container
        # The default credentials for a fresh Milvus installation
        connections.connect(
            alias="default", 
            host="localhost", 
            port="19530",
            user="root",
            password="Milvus" # Note: Capital 'M'
        )
        
        # List all collections (Identity Vaults)
        collections = utility.list_collections()
        
        print(f"[SUCCESS] Handshake complete.")
        print(f"[INFO] Active Vaults: {collections}")
        
    except Exception as e:
        print(f"[ERROR] Could not reach the Vault: {e}")

if __name__ == "__main__":
    check_vault_connection()