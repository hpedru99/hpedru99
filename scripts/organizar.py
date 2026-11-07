#!/usr/bin/env python3
"""Organiza automaticamente os repositórios de um utilizador do GitHub por categorias.

Como funciona:
  1. Lista todos os repositórios do utilizador.
  2. Deteta a categoria de cada um:
       - se o repositório tiver um tópico `categoria-<nome>`, usa esse nome
         (uma categoria nova é criada automaticamente, basta inventar o nome);
       - senão, adivinha pelo nome, linguagem e ficheiros (Django → web, telebot → bots, ...).
  3. (Opcional, com token) adiciona o tópico `categoria-<nome>` ao repositório.
  4. Reescreve a secção de projetos do README.md do perfil, agrupada por categoria.

Variáveis de ambiente:
  GITHUB_USER      utilizador (por defeito: hpedru99)
  GITHUB_TOKEN     token para a API (o do Actions chega para ler)
  ORGANIZER_TOKEN  token pessoal com permissão de escrita; se existir, aplica os tópicos
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

USER = os.environ.get("GITHUB_USER", "hpedru99")
README = os.environ.get("README_PATH", "README.md")
API = "https://api.github.com"
START, END = "<!-- PROJETOS:INICIO -->", "<!-- PROJETOS:FIM -->"

# Categorias conhecidas: emoji + nome bonito. Categorias novas (tópico categoria-xyz)
# aparecem sozinhas com o emoji por defeito.
CATEGORIAS = {
    "web": ("🌐", "Web"),
    "bots": ("🤖", "Bots"),
    "dados": ("📊", "Dados & IA"),
    "jogos": ("🎮", "Jogos"),
    "mobile": ("📱", "Mobile"),
    "automacao": ("⚙️", "Automação & Scripts"),
    "estudos": ("🎓", "Estudos & Faculdade"),
    "perfil": ("👤", "Perfil"),
    "templates": ("🧩", "Templates"),
    "outros": ("📁", "Outros"),
}
ORDEM = list(CATEGORIAS)

# Regras de deteção: (categoria, padrões no nome, padrões no conteúdo/ficheiros)
REGRAS = [
    ("bots", r"bot", r"telebot|aiogram|python-telegram-bot|telegram\.ext|discord\.py|import discord|discord\.js|whatsapp-web"),
    ("jogos", r"game|jogo|pygame", r"import pygame|import arcade|project\.godot|phaser|ProjectSettings/ProjectVersion"),
    ("mobile", r"app-?mobile|android|ios|flutter", r"pubspec\.yaml|AndroidManifest\.xml|react-native|\bexpo\b[\"\']|\.xcodeproj"),
    ("dados", r"(^|[-_])(ml|ai|ia)([-_]|$)|data|dados|analise|analysis", r"import pandas|import numpy|sklearn|tensorflow|torch|\.ipynb|matplotlib"),
    ("web", r"site|web|shop|loja|api|blog", r"\bdjango\b|\bflask\b|fastapi|\"express\"|\"react\"|\"vue\"|\"next\"|svelte|index\.html|manage\.py"),
    ("automacao", r"script|auto|tool|cli", r"\bselenium\b|\bplaywright\b|import argparse|import schedule"),
    ("estudos", r"lab|laba|semestre|aula|curso|trabalho|tp\d|exerc|homework|course", r""),
]


def api(path, token=None, method="GET", body=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    tok = token or os.environ.get("GITHUB_TOKEN")
    if tok:
        req.add_header("Authorization", f"Bearer {tok}")
    data = json.dumps(body).encode() if body is not None else None
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data, timeout=30) as r:
            return json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        if e.code in (404, 409):  # repositório vazio / ficheiro inexistente
            return None
        raise


def listar_repos():
    repos, page = [], 1
    while True:
        lote = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not lote:
            return repos
        repos += lote
        page += 1


def ficheiros(repo):
    """Devolve {caminho: conteúdo} com a árvore e alguns ficheiros-chave."""
    branch = repo.get("default_branch") or "main"
    arvore = api(f"/repos/{repo['full_name']}/git/trees/{branch}?recursive=1") or {}
    caminhos = [t["path"] for t in arvore.get("tree", []) if t["type"] == "blob"]
    chave = [p for p in caminhos if re.search(
        r"(^|/)(requirements\.txt|package\.json|pyproject\.toml|pubspec\.yaml)$|^[^/]+\.py$", p)][:8]
    out = {p: "" for p in caminhos}
    for p in chave:
        raw = f"https://raw.githubusercontent.com/{repo['full_name']}/{branch}/{p}"
        try:
            with urllib.request.urlopen(raw, timeout=30) as r:
                out[p] = r.read(200_000).decode("utf-8", "ignore")
        except Exception:
            pass
    return out


def detetar(nome, linguagem, topicos, files, dono=USER):
    for t in topicos:
        if t.startswith("categoria-"):
            return t[len("categoria-"):]
    if nome.lower() == dono.lower():
        return "perfil"
    texto = "\n".join(files) + "\n" + "\n".join(files.values())
    # O conteúdo é a pista mais forte; o nome serve de desempate.
    for cat, _, conteudo in REGRAS:
        if conteudo and re.search(conteudo, texto, re.I):
            return cat
    for cat, padrao_nome, _ in REGRAS:
        if re.search(padrao_nome, nome, re.I):
            return cat
    if linguagem in ("HTML", "CSS", "JavaScript", "TypeScript", "PHP"):
        return "web"
    if linguagem == "Jupyter Notebook":
        return "dados"
    return "outros"


def rotulo(cat):
    emoji, nome = CATEGORIAS.get(cat, ("📂", cat.replace("-", " ").title()))
    return f"{emoji} {nome}"


def gerar_seccao(grupos):
    ordem = sorted(grupos, key=lambda c: (ORDEM.index(c) if c in ORDEM else len(ORDEM) - 1.5, c))
    linhas = [START, "", "## 🗂️ Os meus projetos por categoria", ""]
    for cat in ordem:
        linhas += [f"### {rotulo(cat)}", "", "| Projeto | Descrição | Linguagem |", "|---|---|---|"]
        for r in sorted(grupos[cat], key=lambda r: r["name"].lower()):
            desc = (r.get("description") or "—").replace("|", "\\|")
            linhas.append(f"| [{r['name']}]({r['html_url']}) | {desc} | {r.get('language') or '—'} |")
        linhas.append("")
    linhas += ["<sub>Atualizado automaticamente por `scripts/organizar.py`. "
               "Para mudar a categoria de um projeto, adiciona-lhe o tópico `categoria-<nome>`.</sub>", "", END]
    return "\n".join(linhas)


def atualizar_readme(seccao):
    texto = open(README, encoding="utf-8").read() if os.path.exists(README) else ""
    if START in texto and END in texto:
        novo = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: seccao, texto, flags=re.S)
    else:
        novo = texto.rstrip() + "\n\n" + seccao + "\n"
    if novo != texto:
        open(README, "w", encoding="utf-8").write(novo)
        return True
    return False


def main():
    escrita = os.environ.get("ORGANIZER_TOKEN")
    grupos = {}
    for r in listar_repos():
        if r.get("fork") or r.get("archived"):
            continue
        topicos = r.get("topics") or []
        cat = detetar(r["name"], r.get("language"), topicos, ficheiros(r))
        grupos.setdefault(cat, []).append(r)
        print(f"{r['name']:<30} -> {cat}")
        tag = f"categoria-{cat}"
        if escrita and tag not in topicos:
            novos = [t for t in topicos if not t.startswith("categoria-")] + [tag]
            api(f"/repos/{r['full_name']}/topics", escrita, "PUT", {"names": novos})
            print(f"{'':<30}    tópico {tag} aplicado")
    mudou = atualizar_readme(gerar_seccao(grupos))
    print("README atualizado." if mudou else "README já estava atualizado.")


if __name__ == "__main__":
    sys.exit(main())
