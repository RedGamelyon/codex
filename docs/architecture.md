# Codex Architecture (Early Draft)

## Vault
A vault is a folder that contains all data for one world / story / campaign.

### Vault structure
vault/
├── vault.yaml
├── characters/
├── templates/
└── metadata/
    └── relationships.json

### Notes
- Characters are stored as Markdown in `characters/`
- Templates are stored in `templates/`
- Relationship/graph data is stored in `metadata/relationships.json`

