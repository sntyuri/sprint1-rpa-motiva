import json, sys
import wave
import numpy as np
from faster_whisper import WhisperModel

def ler(nome):
    with wave.open(f"audio/{nome.split(".")[0]}.16k.wav") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

modelo = WhisperModel("small", device="cpu", compute_type="int8")
saida = {}
for nome in ["1.ogg", "2.ogg"]:
    segs, _ = modelo.transcribe(ler(nome), language="pt", word_timestamps=True, vad_filter=False)
    lista = []
    for s in segs:
        lista.append({"ini": round(s.start, 2), "fim": round(s.end, 2), "texto": s.text.strip(),
                      "palavras": [[round(w.start, 2), round(w.end, 2), w.word] for w in s.words]})
        print(f"{nome} [{s.start:6.2f} - {s.end:6.2f}] {s.text.strip()}", flush=True)
    saida[nome] = lista
json.dump(saida, open("audio/transcricao.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
