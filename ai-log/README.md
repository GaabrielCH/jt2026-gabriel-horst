# ai-log — como a análise foi construída com IA

Toda a análise deste repositório foi feita em conversa com **Claude Code
(Opus 5)**. Esta pasta tem a sessão inteira, em texto, sem trechos escolhidos.

## Arquivos

| Arquivo | O que é | Para quem tem |
|---|---|---|
| [`decisoes-e-iteracoes.md`](decisoes-e-iteracoes.md) | Os pontos de virada da sessão, comentados: onde a IA foi corrigida, onde ela discordou de mim, onde ela corrigiu a si mesma | **~10 minutos** — comece por aqui |
| [`transcript-completo.md`](transcript-completo.md) | A conversa inteira em Markdown legível, em ordem cronológica, **incluindo os blocos de raciocínio interno** | ~1 hora de leitura |
| [`sessao-raw.jsonl`](sessao-raw.jsonl) | O transcript bruto exportado pelo Claude Code, sem nenhum corte | auditoria / verificação |
| [`exportar_transcript.py`](exportar_transcript.py) | Script que gera os dois primeiros a partir do bruto | reprodutibilidade |

## Como ler o transcript

O arquivo está organizado por **turno de usuário** (5 prompts principais). Dentro
de cada turno:

- `## Turno N · Usuario` — o prompt, na íntegra
- `### Claude` — a resposta
- `<details>Raciocinio</details>` — **o pensamento interno do modelo**
- `<details>Acao: Bash / Write / ...</details>` — a ferramenta chamada
- `<details>Resultado da ferramenta</details>` — a saída

Os blocos de **raciocínio** são a parte mais reveladora do processo: é neles que
aparecem as dúvidas, as hipóteses testadas e descartadas, e os momentos em que o
modelo percebeu que estava errado antes de escrever a resposta. Foram mantidos
de propósito.

Resultados de ferramenta muito longos foram truncados **apenas no `.md`**, com
marcação explícita. O `sessao-raw.jsonl` tem tudo.

## O que foi alterado no export

Nada de conteúdo. A única transformação é o mascaramento de e-mail pessoal
(PII) via regex, no `.md`. Nenhum trecho de raciocínio, decisão, erro ou
correção foi removido ou editado.

## Regenerar

```bash
python ai-log/exportar_transcript.py
# ou apontando para outro arquivo de sessão:
python ai-log/exportar_transcript.py caminho/para/sessao.jsonl
```

## Como a IA foi configurada

Antes de começar, escrevi um [`CLAUDE.md`](../CLAUDE.md) na raiz do projeto com
instruções permanentes — entre elas:

> - **Antes de rodar análise pesada, explique seu raciocínio primeiro.** Descreva
>   o schema real dos dados (não assuma colunas — confira) [...] e proponha um
>   plano antes de executar.
> - **Não pule direto para a resposta final.** Prefiro decisões incrementais que
>   eu possa revisar e discutir.
> - **Aponte quando os dados não sustentam algo**, mesmo que contrarie a hipótese
>   que eu levantei. Não force uma conclusão para agradar.

Isso moldou a sessão inteira: a análise só começou depois de um plano escrito e
aprovado ([`analise/PLANO.md`](../analise/PLANO.md)), e a IA rejeitou a hipótese
que eu trouxe em vez de acomodá-la.
