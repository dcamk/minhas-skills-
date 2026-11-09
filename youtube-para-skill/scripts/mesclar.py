"""Uso: python scripts/mesclar.py <id>
Junta trabalho/<id>.limpo.txt (fala) com trabalho/<id>.acoes.json (o que acontece na tela)
e grava trabalho/<id>.enriquecido.txt na ordem do tempo."""
import json
import re
import sys
from pathlib import Path

PASTA = Path("trabalho")


def seg(mmss):
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def mmss(s):
    s = int(s)
    return f"{s // 60}:{s % 60:02d}"


def linha_acao(a):
    partes = [f"▶ [{mmss(a['t'])}]"]
    if a.get("tela"):
        partes.append(f"em {a['tela']}:")
    partes.append(a.get("acao", ""))
    if a.get("alvo"):
        partes.append(f"\"{a['alvo']}\"")
    if a.get("valor"):
        partes.append(f"= `{a['valor']}`")
    if a.get("resultado"):
        partes.append(f"→ {a['resultado']}")
    if a.get("confianca") == "baixa":
        partes.append("(incerto)")
    return " ".join(p for p in partes if p)


def main():
    vid = sys.argv[1]
    blocos = []
    for l in (PASTA / f"{vid}.limpo.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\[(\d+:\d{2})\]", l)
        if m:
            blocos.append((seg(m.group(1)), 0, l))
    arq_a = PASTA / f"{vid}.acoes.json"
    acoes = json.loads(arq_a.read_text(encoding="utf-8")) if arq_a.exists() else []
    eventos = blocos + [(a["t"], 1, linha_acao(a)) for a in acoes]
    eventos.sort(key=lambda e: (e[0], e[1]))
    (PASTA / f"{vid}.enriquecido.txt").write_text("\n".join(e[2] for e in eventos) + "\n", encoding="utf-8")
    print(json.dumps({"id": vid, "blocos_fala": len(blocos), "acoes": len(acoes)}))


if __name__ == "__main__":
    main()
