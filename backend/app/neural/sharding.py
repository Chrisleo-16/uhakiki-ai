import hashlib
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
# ---------------------------------------------------------
# SOVEREIGN SHARDING ENGINE v1.0
# "Breaks data into neural nutrients without losing context"
# ---------------------------------------------------------

class SovereignSharder:
    def __init__(self, chunk_size=500, overlap=50):
        # We use overlap so the AI understands the connection between
        # the end of one paragraph and the start of the next.
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def _generate_checksum(self, text: str) -> str:
        """Creates a digital fingerprint (SHA-256) for data integrity."""
        return hashlib.sha256(text.encode()).hexdigest()

    def process_document(self, raw_text: str, source_id: str) -> List[Dict]:
        """
        Takes raw text, shreds it, fingerprints it, and prepares it for the Vault.
        """
        chunks = self.splitter.split_text(raw_text)
        shards = []

        print(f"[NEURAL] Sharding document {source_id} into {len(chunks)} fragments...")

        for i, chunk in enumerate(chunks):
            shard = {
                "content": chunk,
                "metadata": {
                    "source_id": source_id,
                    "chunk_index": i,
                    "checksum": self._generate_checksum(chunk), # <--- The Integrity Seal
                    "version": "sovereign-v1"
                }
            }
            shards.append(shard)
        
        return shards

# Singleton instance to be imported elsewhere
sharder = SovereignSharder()