from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet


class EncryptedTokenStore:
    def __init__(self, root: Path, key_file: Path) -> None:
        self.root = root
        self.key_file = key_file
        self.root.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(self._load_or_create_key())

    def _load_or_create_key(self) -> bytes:
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        if self.key_file.exists():
            return self.key_file.read_bytes()
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        return key

    def save(self, token_store_key: str, payload: Dict[str, Any]) -> None:
        target = self.root / f"{token_store_key}.enc"
        raw = json.dumps(payload).encode("utf-8")
        encrypted = self._fernet.encrypt(raw)
        target.write_bytes(encrypted)

    def load(self, token_store_key: str) -> Optional[Dict[str, Any]]:
        target = self.root / f"{token_store_key}.enc"
        if not target.exists():
            return None
        decrypted = self._fernet.decrypt(target.read_bytes())
        return json.loads(decrypted.decode("utf-8"))

    def delete(self, token_store_key: str) -> None:
        target = self.root / f"{token_store_key}.enc"
        target.unlink(missing_ok=True)
