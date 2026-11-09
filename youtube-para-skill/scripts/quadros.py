"""Uso: python scripts/quadros.py <id> [--max 40] [--largura 1024] [--sensibilidade 6]
Baixa o vídeo (sem áudio, até 720p), detecta os momentos em que a tela muda e os momentos em que o
narrador indica uma ação ("clica", "vai em", "digita"...), extrai esses quadros e monta o pacote:
  trabalho/<id>.quadros/q_<segundos>.jpg
  trabalho/<id>.quadros.json  -> [{"arquivo","t","motivo","mudanca","fala"}]
Imprime se o vídeo é demonstrativo (ensina na tela) e quantos quadros foram gerados."""
import argparse
import json
import re
import subprocess
from pathlib import Path

PASTA = Path("trabalho")
GATILHOS = re.compile(
    r"\b(clic\w*|clique|aperta\w*|pression\w*|seleciona\w*|marca\w*|desmarca\w*|digit\w*|escrev\w*|cola\w*|copi\w*|"
    r"arrast\w*|abr[ea]\w*|vai em|vamos em|entra em|acess\w*|menu|aba|bot[aã]o|op[cç][aã]o|campo|configura\w*|"
    r"ajust\w*|instal\w*|salv\w*|aqui|ali|esse aqui|essa aqui|nessa tela|na tela|olha|repara|perceba|"
    r"click|select|type|open|settings|tab|button)\b", re.I)
AMOSTRA_S = 2
W, H = 64, 36


def baixar(vid):
    destino = PASTA / f"{vid}.mp4"
    if not destino.exists():
        subprocess.run(["yt-dlp", "-f", "bv*[height<=720][ext=mp4]/bv*[height<=720]/b[height<=720]",
                        "--sleep-requests", "2", "-o", str(destino), f"https://www.youtube.com/watch?v={vid}"],
                       check=True, capture_output=True)
    return destino


def mudancas(video):
    bruto = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf",
                            f"fps=1/{AMOSTRA_S},scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                           check=True, capture_output=True).stdout
    n = W * H
    quadros = [bruto[i:i + n] for i in range(0, len(bruto) - n + 1, n)]
    difs = [0.0] + [sum(abs(a - b) for a, b in zip(quadros[i - 1], quadros[i])) / n for i in range(1, len(quadros))]
    return [(i * AMOSTRA_S, d) for i, d in enumerate(difs)], len(quadros) * AMOSTRA_S


def fala_em(segs, t, janela=8):
    return " ".join(s["txt"] for s in segs if t - janela <= s["t"] <= t + janela)[:400]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("id")
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--largura", type=int, default=1024)
    ap.add_argument("--sensibilidade", type=float, default=6.0)
    ap.add_argument("--video")
    a = ap.parse_args()

    arq_t = PASTA / f"{a.id}.transcricao.json"
    segs = json.loads(arq_t.read_text(encoding="utf-8")) if arq_t.exists() else []
    gatilhos = [s["t"] for s in segs if GATILHOS.search(s["txt"])]

    video = Path(a.video) if a.video else baixar(a.id)
    serie, duracao = mudancas(video)
    minutos = max(duracao / 60, 1)
    demonstrativo = len(gatilhos) / minutos >= 1.5 or sum(1 for _, d in serie if d >= a.sensibilidade) / minutos >= 1

    candidatos = {}
    for t, d in serie:
        if d >= a.sensibilidade:
            candidatos[t + 1] = {"t": t + 1, "motivo": "mudança de tela", "mudanca": round(d, 1)}
    for t in gatilhos:
        tt = int(t) + 2
        if not any(abs(tt - c) <= 3 for c in candidatos):
            candidatos[tt] = {"t": tt, "motivo": "ação narrada", "mudanca": 0}
    if not candidatos:
        candidatos = {t: {"t": t, "motivo": "amostra", "mudanca": 0} for t in range(5, int(duracao), 30)}

    ordem = sorted(candidatos.values(), key=lambda c: (c["motivo"] != "ação narrada", -c["mudanca"]))
    escolhidos = sorted(ordem[:a.max], key=lambda c: c["t"])
    escolhidos = [c for c in escolhidos if c["t"] < duracao]

    pasta_q = PASTA / f"{a.id}.quadros"
    pasta_q.mkdir(parents=True, exist_ok=True)
    pacote = []
    for c in escolhidos:
        nome = f"q_{c['t']:05d}.jpg"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(c["t"]), "-i", str(video), "-frames:v", "1",
                        "-vf", f"scale={a.largura}:-2", "-q:v", "4", str(pasta_q / nome)], check=True)
        pacote.append({"arquivo": f"{pasta_q.name}/{nome}", "t": c["t"], "motivo": c["motivo"],
                       "mudanca": c["mudanca"], "fala": fala_em(segs, c["t"])})
    (PASTA / f"{a.id}.quadros.json").write_text(json.dumps(pacote, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"id": a.id, "demonstrativo": demonstrativo, "quadros": len(pacote),
                      "gatilhos_narrados": len(gatilhos), "duracao_s": duracao}, ensure_ascii=False))


if __name__ == "__main__":
    main()
