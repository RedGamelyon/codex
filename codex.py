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

# ==========================================
#
#          Character Creation v1
#
# ==========================================

def save_character(vault_path: str, name: str, summary: str) -> Path:
    vault = Path(vault_path).expanduser().resolve()
    characters_dir = vault / "characters"
    characters_dir.mkdir(exist_ok=True)

    # simple filename slug
    slug = "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")
    file_path = characters_dir / f"{slug}.md"

    content = f"""# {name}

## Summary
{summary}

## Description

## Traits

## History

## Relationships
"""

    file_path.write_text(content, encoding="utf-8")
    print(f"✅ Character saved: {file_path}")
    return file_path

# ==========================================

if __name__ == "__main__":
    create_vault("./my_first_vault")
    save_character("./my_first_vault", "Alaric Stone", "A stoic knight exiled from his order.")
