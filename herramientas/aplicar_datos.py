# -*- coding: utf-8 -*-
"""Reemplaza en el dashboard los bloques de datos por los generados."""
import sys, re, io
HTML = sys.argv[1]; OUT = sys.argv[2]; SAL = sys.argv[3]

src = io.open(HTML, encoding="utf-8").read()

def block_span(text, name):
    """Devuelve (ini, fin) del bloque 'const <name> = ... ;' balanceando llaves/corchetes."""
    i = text.index("const " + name)
    d = 0; j = text.index("=", i)
    for k in range(j, len(text)):
        ch = text[k]
        if ch in "{[": d += 1
        elif ch in "}]": d -= 1
        elif ch == ";" and d == 0:
            return i, k + 1
    raise ValueError("no cierra " + name)

blocks = {
    "monthlyData": io.open(SAL + "/monthly.js", encoding="utf-8").read(),
    "weeklyData":  io.open(SAL + "/weekly.js", encoding="utf-8").read(),
    "clientData":  io.open(SAL + "/clients.js", encoding="utf-8").read(),
    "INVOICES":    io.open(SAL + "/invoices.js", encoding="utf-8").read(),
}
cat = io.open(SAL + "/catalog.js", encoding="utf-8").read().split("\n")
blocks["INV_CLIENTS"] = cat[0]
blocks["INV_NITS"] = cat[1]

# de atras hacia adelante para no mover los indices
spans = sorted(((block_span(src, n)), n) for n in blocks)
for (a, b), n in reversed(spans):
    src = src[:a] + blocks[n] + src[b:]

io.open(OUT, "w", encoding="utf-8").write(src)
print("escrito", OUT, len(src), "bytes")
