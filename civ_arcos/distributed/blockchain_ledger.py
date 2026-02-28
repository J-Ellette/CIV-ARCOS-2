"""SHA-256 blockchain for evidence integrity."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Block:
    index: int
    timestamp: str
    data: Dict[str, Any]
    previous_hash: str
    hash: str = ""

    def compute_hash(self) -> str:
        content = json.dumps(
            {
                "index": self.index,
                "timestamp": self.timestamp,
                "data": self.data,
                "previous_hash": self.previous_hash,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()


class BlockchainLedger:
    """Immutable blockchain for evidence integrity verification."""

    def __init__(self) -> None:
        self._chain: List[Block] = []
        self._evidence_index: Dict[str, Block] = {}
        self._create_genesis()

    def _create_genesis(self) -> None:
        genesis = Block(
            index=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"genesis": True},
            previous_hash="0" * 64,
        )
        genesis.hash = genesis.compute_hash()
        self._chain.append(genesis)

    def add_block(self, data: Dict[str, Any]) -> Block:
        previous_block = self._chain[-1]
        block = Block(
            index=len(self._chain),
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data,
            previous_hash=previous_block.hash,
        )
        block.hash = block.compute_hash()
        self._chain.append(block)
        evidence_id = data.get("evidence_id")
        if evidence_id is not None:
            self._evidence_index[evidence_id] = block
        return block

    def validate_chain(self) -> bool:
        for block_index in range(1, len(self._chain)):
            current_block = self._chain[block_index]
            previous_block = self._chain[block_index - 1]
            if current_block.hash != current_block.compute_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def get_block(self, index: int) -> Optional[Block]:
        if 0 <= index < len(self._chain):
            return self._chain[index]
        return None

    def find_evidence(self, evidence_id: str) -> Optional[Block]:
        return self._evidence_index.get(evidence_id)

    def get_chain_length(self) -> int:
        return len(self._chain)
