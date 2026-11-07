#!/usr/bin/env bash
# Cria um repositório novo no GitHub já com categoria e estrutura inicial.
#
# Uso:   ./scripts/novo-projeto.sh <categoria> <nome> ["descrição"] [--privado]
# Ex.:   ./scripts/novo-projeto.sh web portfolio "O meu site pessoal"
#        ./scripts/novo-projeto.sh bots bot-discord-musica "Bot de música para Discord"
#        ./scripts/novo-projeto.sh robotica braco-arduino      # categoria nova? é criada automaticamente
#
# Requer o GitHub CLI autenticado:  gh auth login
set -euo pipefail

[[ $# -lt 2 ]] && { sed -n '2,10p' "$0"; exit 1; }
CAT=$(echo "$1" | tr '[:upper:]' '[:lower:]' | tr ' _' '--')
NOME=$2
DESC=${3:-"Projeto da categoria $CAT"}
VIS=--public
[[ "${4:-}" == "--privado" ]] && VIS=--private

case "$CAT" in
  web)       GI=Node;   ESTRUTURA=(index.html src/.gitkeep) ;;
  bots)      GI=Python; ESTRUTURA=(main.py requirements.txt .env.example) ;;
  dados)     GI=Python; ESTRUTURA=(notebooks/.gitkeep data/.gitkeep requirements.txt) ;;
  jogos)     GI=Python; ESTRUTURA=(main.py assets/.gitkeep) ;;
  mobile)    GI=Dart;   ESTRUTURA=(README_SETUP.md) ;;
  automacao) GI=Python; ESTRUTURA=(main.py requirements.txt) ;;
  estudos)   GI=Python; ESTRUTURA=(exercicios/.gitkeep notas.md) ;;
  *)         GI=Python; ESTRUTURA=(src/.gitkeep) ; echo "ℹ️  Categoria nova: '$CAT' — vai aparecer sozinha no teu perfil." ;;
esac

TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
for f in "${ESTRUTURA[@]}"; do mkdir -p "$(dirname "$f")"; : > "$f"; done
[[ -f .env.example ]] && echo "TOKEN=coloca_aqui_o_teu_token" > .env.example
printf '.env\n__pycache__/\nnode_modules/\n.venv/\n' > .gitignore
cat > README.md <<MD
# $NOME

$DESC

**Categoria:** \`$CAT\`

## Como executar

_A preencher._
MD
git init -q -b main && git add -A && git commit -qm "Estrutura inicial ($CAT)"

gh repo create "$NOME" $VIS --description "$DESC" --source . --push
gh repo edit "$NOME" --add-topic "categoria-$CAT"
echo "✅ Criado: https://github.com/$(gh api user --jq .login)/$NOME  (categoria: $CAT)"
echo "   O README do perfil é atualizado na próxima execução diária (ou corre o workflow à mão)."
