# Guia: organização automática dos repositórios

## Como as categorias funcionam
- Todos os dias (e quando carregas em **Actions → Organizar repositórios → Run workflow**),
  `scripts/organizar.py` analisa cada repositório e coloca-o numa categoria no README do perfil.
- A categoria é detetada pelo código: Django/Flask/React → **web**, telebot/aiogram/discord → **bots**,
  pandas/notebooks → **dados**, pygame/Godot → **jogos**, Flutter/Android → **mobile**, etc.
- **Para forçar ou criar uma categoria nova**, adiciona ao repositório o tópico `categoria-<nome>`
  (ex.: `categoria-robotica`). Na execução seguinte aparece uma secção nova sozinha.

## Criar um projeto novo
```bash
./scripts/novo-projeto.sh <categoria> <nome> "descrição" [--privado]
./scripts/novo-projeto.sh web portfolio "O meu site pessoal"
```
Cria o repositório, a estrutura inicial adequada à categoria e o tópico `categoria-<nome>`.

## Aplicar os tópicos também nos repositórios (opcional)
Cria um token em GitHub → Settings → Developer settings → Fine-grained tokens, com
"Administration: Read and write" nos teus repositórios, e guarda-o como secret `ORGANIZER_TOKEN`
neste repositório (Settings → Secrets and variables → Actions).
