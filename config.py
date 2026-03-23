import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    SOLANA_DEVNET_RPC_URL: str = os.getenv("SOLANA_DEVNET_RPC_URL", "https://api.devnet.solana.com")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    DOCS_PORT: int = int(os.getenv("DOCS_PORT", "8080"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    CLUSTER_URLS = {
        "mainnet-beta": "https://api.mainnet-beta.solana.com",
        "mainnet": "https://api.mainnet-beta.solana.com",
        "devnet": "https://api.devnet.solana.com",
        "testnet": "https://api.testnet.solana.com",
        "localnet": "http://127.0.0.1:8899",
    }

    def rpc_url(self, cluster: str = "mainnet-beta") -> str:
        return self.CLUSTER_URLS.get(cluster, self.SOLANA_RPC_URL)

config = Config()
