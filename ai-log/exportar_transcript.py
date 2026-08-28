# -*- coding: utf-8 -*-
"""
exportar_transcript.py — converte o transcript bruto da sessao do Claude Code
(JSONL) em Markdown legivel para a pasta ai-log/.

Uso:
    python ai-log/exportar_transcript.py [caminho_do_jsonl]

Sem argumento, procura a sessao deste projeto em ~/.claude/projects/.

Exporta a sessao INTEIRA, em ordem cronologica, incluindo:
  - todos os prompts do usuario, na integra
  - todas as respostas do assistente, na integra
  - os blocos de raciocinio (thinking) — e onde se ve o processo de decisao
  - todas as chamadas de ferramenta (comandos, arquivos escritos)
  - os resultados das ferramentas (truncados quando muito longos; o arquivo
    sessao-raw.jsonl guarda tudo sem corte)

Unica alteracao de conteudo: mascaramento de e-mail pessoal (PII). Nenhum
trecho de raciocinio, decisao ou erro foi removido.
"""
import json, sys, os, re, glob
from datetime import datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
LIM_RESULT = 2500          # corte por resultado de ferramenta
LIM_PARAM = 1800           # corte por parametro de ferramenta

def achar_sessao():
    if len(sys.argv) > 1:
        return sys.argv[1]
    base = os.path.expanduser("~/.claude/projects")
    alvo = os.path.join(base, "c--Users-gabri--vscode-jovens-talentos-2026-hackathon-data")
    cands = sorted(glob.glob(os.path.join(alvo, "*.jsonl")), key=os.path.getmtime)
    if not cands:
        cands = sorted(glob.glob(os.path.join(base, "*hackathon*", "*.jsonl")),
                       key=os.path.getmtime)
    if not cands:
        sys.exit("Nao encontrei o .jsonl da sessao. Passe o caminho como argumento.")
    return cands[-1]

def mascarar(t):
    """Mascara apenas PII. Nao altera conteudo tecnico."""
    if not t:
        return t
    t = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email removido]", t)
    return t

def corta(t, lim):
    t = t or ""
    if len(t) <= lim:
        return t
    return t[:lim] + f"\n\n... [cortado: +{len(t)-lim:,} caracteres. " \
                     f"Conteudo integral em sessao-raw.jsonl] ..."

def texto_de(content):
    """Normaliza content (str ou lista de blocos) para lista de (tipo, texto)."""
    out = []
    if isinstance(content, str):
        out.append(("text", content))
    elif isinstance(content, list):
        for b in content:
            if not isinstance(b, dict):
                continue
            t = b.get("type")
            if t == "text":
                out.append(("text", b.get("text", "")))
            elif t == "thinking":
                out.append(("thinking", b.get("thinking", "")))
            elif t == "tool_use":
                out.append(("tool_use", b))
            elif t == "tool_result":
                c = b.get("content")
                if isinstance(c, list):
                    c = "\n".join(x.get("text", "") for x in c
                                  if isinstance(x, dict) and x.get("type") == "text")
                out.append(("tool_result", c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)))
    return out

def fmt_ferramenta(b):
    nome = b.get("name", "?")
    inp = b.get("input") or {}
    linhas = [f"**Ferramenta:** `{nome}`"]
    for k, v in inp.items():
        if isinstance(v, str):
            v_ = corta(v, LIM_PARAM)
            if "\n" in v_ or len(v_) > 90:
                linhas.append(f"\n*{k}:*\n```\n{v_}\n```")
            else:
                linhas.append(f"- *{k}:* `{v_}`")
        else:
            linhas.append(f"- *{k}:* `{json.dumps(v, ensure_ascii=False)[:300]}`")
    return "\n".join(linhas)


def main():
    caminho = achar_sessao()
    print(f"lendo: {caminho}")
    regs = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                regs.append(json.loads(linha))
            except json.JSONDecodeError:
                continue

    # copia integral, sem cortes
    destino_raw = os.path.join(AQUI, "sessao-raw.jsonl")
    with open(caminho, encoding="utf-8") as src, \
         open(destino_raw, "w", encoding="utf-8") as dst:
        dst.write(src.read())

    convo = [r for r in regs
             if r.get("type") in ("user", "assistant")
             and isinstance(r.get("message"), dict)
             and r["message"].get("role") in ("user", "assistant")]

    ts = [r.get("timestamp") for r in convo if r.get("guess") is None and r.get("timestamp")]
    inicio, fim = (ts[0][:19].replace("T", " "), ts[-1][:19].replace("T", " ")) if ts else ("?", "?")

    n_user = sum(1 for r in convo if r["message"]["role"] == "user")
    n_asst = sum(1 for r in convo if r["message"]["role"] == "assistant")
    modelos = sorted({r["message"].get("model") for r in convo
                      if r["message"].get("model")})

    out = []
    out.append("# Transcript completo da sessao\n")
    out.append("Conversa integral com o Claude Code (Opus 5) durante a construcao "
               "da analise.\nExportado automaticamente de `sessao-raw.jsonl` por "
               "[`exportar_transcript.py`](exportar_transcript.py).\n")
    out.append("| | |\n|---|---|")
    out.append(f"| Inicio | {inicio} |")
    out.append(f"| Fim | {fim} |")
    out.append(f"| Mensagens do usuario | {n_user} |")
    out.append(f"| Mensagens do assistente | {n_asst} |")
    out.append(f"| Modelo | {', '.join(modelos) or 'claude-opus-5'} |")
    out.append(f"| Registros brutos | {len(regs)} |")
    out.append("\n> Os blocos **Raciocinio** sao o pensamento interno do modelo. "
               "Estao incluidos de proposito:\n> e neles que aparecem as duvidas, "
               "as hipoteses descartadas e as auto-correcoes.\n")
    out.append("\n---\n")

    turno = 0
    for r in convo:
        m = r["message"]
        papel = m["role"]
        quando = (r.get("timestamp") or "")[:19].replace("T", " ")
        blocos = texto_de(m.get("content"))

        # pula mensagens que sao so tool_result (entram junto do turno anterior)
        so_result = blocos and all(t == "tool_result" for t, _ in blocos)

        if papel == "user" and not so_result:
            turno += 1
            out.append(f"\n## Turno {turno} · Usuario\n")
            out.append(f"*{quando}*\n")
            for t, v in blocos:
                if t == "text":
                    txt = mascarar(v).strip()
                    if txt:
                        out.append("> " + txt.replace("\n", "\n> ") + "\n")
        elif papel == "user" and so_result:
            for t, v in blocos:
                out.append("\n<details><summary>Resultado da ferramenta</summary>\n")
                out.append("```\n" + corta(mascarar(v), LIM_RESULT).strip() + "\n```")
                out.append("\n</details>\n")
        else:
            cab = False
            for t, v in blocos:
                if not cab:
                    out.append(f"\n### Claude\n")
                    cab = True
                if t == "thinking":
                    txt = mascarar(v).strip()
                    if txt:
                        out.append("\n<details><summary>Raciocinio</summary>\n")
                        out.append("\n" + txt + "\n")
                        out.append("\n</details>\n")
                elif t == "text":
                    txt = mascarar(v).strip()
                    if txt:
                        out.append("\n" + txt + "\n")
                elif t == "tool_use":
                    out.append("\n<details><summary>Acao: `"
                               + v.get("name", "?") + "`</summary>\n")
                    out.append("\n" + mascarar(fmt_ferramenta(v)) + "\n")
                    out.append("\n</details>\n")

    destino_md = os.path.join(AQUI, "transcript-completo.md")
    with open(destino_md, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"gravado: {destino_md} ({os.path.getsize(destino_md):,} bytes)")
    print(f"gravado: {destino_raw} ({os.path.getsize(destino_raw):,} bytes)")
    print(f"turnos de usuario: {turno} | registros: {len(regs)}")

if __name__ == "__main__":
    main()
