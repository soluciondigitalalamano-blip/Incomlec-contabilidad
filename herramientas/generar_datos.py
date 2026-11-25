# -*- coding: utf-8 -*-
"""Genera los bloques de datos del dashboard de Facturacion desde el Excel de ventas."""
import sys, json, unicodedata, datetime
import openpyxl

XLSX = sys.argv[1]
MONTHS = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto",
          "Septiembre","Octubre","Noviembre","Diciembre"]
UP = {m.upper(): m for m in MONTHS}

def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()

wb = openpyxl.load_workbook(XLSX, data_only=True)

# ---------- 1. ACUMULADO -> monthlyData + weeklyData ----------
ws = wb["ACUMULADO"]
rows = list(ws.iter_rows(values_only=True))

def cells(r):
    return ["" if c is None else c for c in r]

monthly, weekly, months_present = {}, {}, []
i = 0
while i < len(rows):
    r = cells(rows[i])
    # fila de titulo de mes: contiene exactamente un texto que es un mes
    titles = [norm(c) for c in r if isinstance(c, str) and norm(c) in UP]
    if len(titles) == 1 and not any(norm(c) == "SEMANA N" for c in r):
        mes = UP[titles[0]]
        hdr = cells(rows[i+1]); dias = cells(rows[i+2])
        # columnas de semana: las que en hdr son numero entero 1..5
        wcols = [j for j, c in enumerate(hdr) if isinstance(c, (int, float)) and float(c) in (1,2,3,4,5)]
        data = {}
        for k in range(i+3, min(i+8, len(rows))):
            rr = cells(rows[k])
            label = norm(rr[1]) if len(rr) > 1 else ""
            if label.startswith("SUPLEC"): data["Suplec"] = rr
            elif label.startswith("INCOMELEC"): data["Incomelec"] = rr
            elif label.startswith("INTERCOM"): data["Intercompany"] = rr
            elif label.startswith("TOTAL FACTURADO"): data["Total"] = rr
        if not {"Suplec","Incomelec","Intercompany"} <= set(data):
            i += 1; continue
        # total del mes = columna "Total <Mes>"
        tcol = None
        for j, c in enumerate(hdr):
            if isinstance(c, str) and norm(c).startswith("TOTAL " + norm(mes)): tcol = j
        monthly[mes] = {k: float(data[k][tcol] or 0) for k in ("Suplec","Incomelec","Intercompany")}
        wk = []
        for j in wcols:
            wk.append({
                "semana": int(hdr[j]),
                "rango": str(dias[j]).strip() if j < len(dias) and dias[j] != "" else "",
                "Incomelec": float(data["Incomelec"][j] or 0),
                "Suplec":    float(data["Suplec"][j] or 0),
                "Intercompany": float(data["Intercompany"][j] or 0),
            })
        # el mes en curso puede traer semanas futuras en blanco (sin rango y en cero)
        while wk and wk[-1]["Incomelec"] == 0 and wk[-1]["Suplec"] == 0 \
              and wk[-1]["Intercompany"] == 0:
            wk.pop()
        weekly[mes] = wk
        months_present.append(mes)
        i += 5
    else:
        i += 1

# ---------- 2. Hojas por mes -> facturas ----------
def find_sheet(mes, empresa):
    """empresa: 'I' (Incomelec) o 'S' (Suplec)."""
    tgt_emp = "INCOMELEC" if empresa == "I" else "SUPLEC"
    cands = []
    for name in wb.sheetnames:
        n = norm(name)
        if n == "ACUMULADO": continue
        has_month = norm(mes)[:4] in n
        if empresa == "S":
            is_emp = "SUPLEC" in n
        else:
            is_emp = ("INCOMELEC" in n or "INCOMLEC" in n) and "SUPLEC" not in n
        if is_emp and has_month: cands.append(name)
    if cands: return cands[0]
    # mes en curso: hojas sin nombre de mes ('Incomelc', 'Suplec')
    if mes == months_present[-1]:
        for name in wb.sheetnames:
            n = norm(name)
            if any(norm(m)[:4] in n for m in MONTHS): continue
            if empresa == "S" and n == "SUPLEC": return name
            if empresa == "I" and n in ("INCOMELC","INCOMELEC"): return name
    return None

COLS = {"nit": ("CC/NIT", "NIT", "CC / NIT"), "cliente": ("CLIENTE",),
        "fecha": ("FECHA",), "doc": ("DOCUMENTO",), "bruta": ("VENTA BRUTA",),
        "desc": ("DESCUENTO",), "iva": ("IVA",)}

def parse_sheet(name, empresa):
    """[nit, cliente, fecha dd/mm, doc, bruta, desc, iva, empresa].
    Localiza la cabecera y mapea las columnas POR NOMBRE, no por posicion:
    algunas hojas traen columnas extra (p. ej. 'Sucursal') o vacias al inicio."""
    sh = wb[name]
    out, cmap = [], None
    for r in sh.iter_rows(values_only=True):
        c = cells(r)
        if cmap is None:
            heads = {norm(v): j for j, v in enumerate(c) if isinstance(v, str) and v.strip()}
            if not any(h in heads for h in COLS["nit"]):
                continue
            cmap = {}
            for key, alts in COLS.items():
                for a in alts:
                    if a in heads: cmap[key] = heads[a]; break
            missing = [k for k in COLS if k not in cmap]
            if missing:
                print("AVISO: a %s le faltan columnas %s" % (name, missing), file=sys.stderr)
                return []
            continue
        def g(k):
            j = cmap[k]
            return c[j] if j < len(c) else ""
        nit, cli = g("nit"), g("cliente")
        if isinstance(cli, str) and norm(cli).startswith("TOTAL"): continue
        if isinstance(nit, str) and norm(nit).startswith("TOTAL"): continue
        if nit in ("", None) or cli in ("", None): continue
        bruta = g("bruta")
        if not isinstance(bruta, (int, float)): continue
        f = g("fecha")
        if not isinstance(f, (datetime.datetime, datetime.date)): continue
        out.append([str(nit).strip(), str(cli).strip(), f.strftime("%d/%m"), str(g("doc")).strip(),
                    float(bruta or 0), float(g("desc") or 0), float(g("iva") or 0), empresa])
    if cmap is None:
        print("AVISO: no encontre cabecera en", name, file=sys.stderr)
    return out

invoices_by_month = {}
for mes in months_present:
    facs = []
    for emp in ("I", "S"):
        sn = find_sheet(mes, emp)
        if sn: facs += parse_sheet(sn, emp)
        else: print("AVISO: sin hoja para", mes, emp, file=sys.stderr)
    invoices_by_month[mes] = facs

# ---------- 3. Catalogo de clientes ----------
clients, nits = [], []
idx = {}
for mes in months_present:
    for f in invoices_by_month[mes]:
        nombre = f[1]
        if nombre not in idx:
            idx[nombre] = len(clients); clients.append(nombre); nits.append(f[0])

# ---------- 4. clientData e INVOICES ----------
client_data, inv_out = {}, {}
for mes in months_present:
    agg = {}
    rows_m = []
    for nit, nombre, fecha, doc, bruta, desc, iva, emp in invoices_by_month[mes]:
        a = agg.setdefault(nombre, {"Incomelec": 0.0, "Suplec": 0.0})
        a["Incomelec" if emp == "I" else "Suplec"] += bruta - desc
        rows_m.append([idx[nombre], emp, fecha, doc, bruta, desc, iva])
    lst = [{"name": n, "Incomelec": round(v["Incomelec"], 2), "Suplec": round(v["Suplec"], 2)}
           for n, v in agg.items()]
    lst.sort(key=lambda x: -(x["Incomelec"] + x["Suplec"]))
    client_data[mes] = lst
    inv_out[mes] = rows_m

acum = {}
for mes in months_present:
    for c in client_data[mes]:
        a = acum.setdefault(c["name"], {"Incomelec": 0.0, "Suplec": 0.0})
        a["Incomelec"] += c["Incomelec"]; a["Suplec"] += c["Suplec"]
client_data["Acumulado"] = sorted(
    [{"name": n, "Incomelec": round(v["Incomelec"], 2), "Suplec": round(v["Suplec"], 2)}
     for n, v in acum.items()],
    key=lambda x: -(x["Incomelec"] + x["Suplec"]))

def num(x):
    x = round(float(x), 2)
    return int(x) if x == int(x) else x

def js_monthly():
    L = ["const monthlyData = {"]
    for m in months_present:
        d = monthly[m]
        L.append("  %s: { Suplec:%s, Incomelec:%s, Intercompany:%s }%s"
                 % (m, num(d["Suplec"]), num(d["Incomelec"]), num(d["Intercompany"]),
                    "" if m == months_present[-1] else ","))
    L.append("};")
    return "\n".join(L)

def js_weekly():
    L = ["const weeklyData = {"]
    for mi, m in enumerate(months_present):
        L.append("  %s: [" % m)
        for wi, w in enumerate(weekly[m]):
            L.append('    { semana:%d, rango:"%s", Incomelec:%s, Suplec:%s, Intercompany:%s }%s'
                     % (w["semana"], w["rango"], num(w["Incomelec"]), num(w["Suplec"]),
                        num(w["Intercompany"]), "" if wi == len(weekly[m]) - 1 else ","))
        L.append("  ]%s" % ("" if mi == len(months_present) - 1 else ","))
    L.append("};")
    return "\n".join(L)

def js_clients():
    keys = months_present + ["Acumulado"]
    L = ["const clientData = {"]
    for mi, m in enumerate(keys):
        L.append("  %s:[" % m)
        for ci, c in enumerate(client_data[m]):
            L.append('    {name:%s,Incomelec:%s,Suplec:%s}%s'
                     % (json.dumps(c["name"], ensure_ascii=False), num(c["Incomelec"]),
                        num(c["Suplec"]), "" if ci == len(client_data[m]) - 1 else ","))
        L.append("  ]%s" % ("" if mi == len(keys) - 1 else ","))
    L.append("};")
    return "\n".join(L)

def js_catalog():
    return ("const INV_CLIENTS = %s;\nconst INV_NITS = %s;"
            % (json.dumps(clients, ensure_ascii=False), json.dumps(nits, ensure_ascii=False)))

def js_invoices():
    L = ["const INVOICES = {"]
    for mi, m in enumerate(months_present):
        L.append("  %s:[" % m)
        for ri, r in enumerate(inv_out[m]):
            L.append("[%d,%s,%s,%s,%s,%s,%s]%s"
                     % (r[0], json.dumps(r[1]), json.dumps(r[2]), json.dumps(r[3], ensure_ascii=False),
                        num(r[4]), num(r[5]), num(r[6]), "" if ri == len(inv_out[m]) - 1 else ","))
        L.append("  ]%s" % ("" if mi == len(months_present) - 1 else ","))
    L.append("};")
    return "\n".join(L)

if __name__ == "__main__":
    import os
    out = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/salida"
    os.makedirs(out, exist_ok=True)
    open(out + "/monthly.js", "w").write(js_monthly())
    open(out + "/weekly.js", "w").write(js_weekly())
    open(out + "/clients.js", "w").write(js_clients())
    open(out + "/catalog.js", "w").write(js_catalog())
    open(out + "/invoices.js", "w").write(js_invoices())
    meta = {"months": months_present,
            "monthly_total": {m: round(sum(monthly[m].values()), 2) for m in months_present},
            "n_clients": len(clients),
            "n_invoices": {m: len(inv_out[m]) for m in months_present}}
    open(out + "/meta.json", "w").write(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False, indent=1))
