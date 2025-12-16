from pathlib import Path
import json

# ==========================================
#
#             Vault Creation v1
#
# ==========================================

def create_vault(path: str) -> None:
    vault_path = Path(path).expanduser().resolve()
    vault_path.mkdir(parents=True, exist_ok=True)

    (vault_path / "characters").mkdir(exist_ok=True)
    (vault_path / "templates").mkdir(exist_ok=True)
    (vault_path / "metadata").mkdir(exist_ok=True)

    vault_yaml = vault_path / "vault.yaml"
    if not vault_yaml.exists():
        vault_yaml.write_text("name: My Codex Vault\nversion: 1\n", encoding="utf-8")

    relationships_json = vault_path / "metadata" / "relationships.json"
    if not relationships_json.exists():
        relationships_json.write_text(json.dumps({"relationships": []}, indent=2), encoding="utf-8")

    print(f"✅ Vault created at: {vault_path}")

if __name__ == "__main__":
    create_vault("./my_first_vault")
