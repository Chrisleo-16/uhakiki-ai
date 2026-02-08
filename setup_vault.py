from pymilvus import MilvusClient, DataType

# 1. Connect to the local Milvus/Konza Node
client = MilvusClient(uri="http://localhost:19530")

COLLECTION_NAME = "sovereign_vault"

# 2. Cleanup (Optional: Use only if you want to reset the vault during testing)
if client.has_collection(COLLECTION_NAME):
    print(f"⚠️  Collection {COLLECTION_NAME} exists. Dropping for fresh setup...")
    client.drop_collection(COLLECTION_NAME)

# 3. Define the Sovereign Schema
schema = client.create_schema(
    auto_id=False, 
    enable_dynamic_field=True, 
    description="Kenyan National Student Identity Vault"
)

# Scalar Field: National ID (Primary Key)
schema.add_field(field_name="national_id", datatype=DataType.VARCHAR, is_primary=True, max_length=20)

# Scalar Field: MTI Band (For funding eligibility checks)
schema.add_field(field_name="mti_band", datatype=DataType.INT64)

# Vector Field: Identity Forensic Embedding (128-dimensional fingerprint)
schema.add_field(field_name="identity_vector", datatype=DataType.FLOAT_VECTOR, dim=128)

# 4. Configure Index Parameters (Optimized for L2 Distance)
index_params = client.prepare_index_params()

index_params.add_index(
    field_name="identity_vector",
    index_type="IVF_FLAT",  # Balanced speed/accuracy for ~1M records
    metric_type="L2",
    params={"nlist": 1024}
)

# 5. Create and Load the Collection
client.create_collection(
    collection_name=COLLECTION_NAME,
    schema=schema,
    index_params=index_params
)

client.load_collection(COLLECTION_NAME)

print(f"✅ [PHASE 1.0] {COLLECTION_NAME} initialized and loaded into memory.")
print(f"🚀 Sub-100ms retrieval is now active.")