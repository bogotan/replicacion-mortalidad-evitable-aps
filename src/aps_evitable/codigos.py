"""Listas de códigos CIE-10 escritas como en los documentos fuente («A00-A09, A40.3, K74.0-K74.2»).

Las usan los estudios 54 (lista OCDE/Eurostat de mortalidad evitable) y 55 (códigos basura de
Naghavi et al., 2010). La causa básica del DANE viene con cuatro caracteres sin punto («A403») o con
tres («A09»). Regla de pertenencia: un código de cuatro caracteres de la lista gana sobre un rango de
tres caracteres de otra fila (lo más específico manda); así se resuelven las exclusiones del tipo
«A40 (excl. A40.3)», que en la fuente se escriben en otra fila.
"""
from __future__ import annotations

LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TODOS3 = [f"{l}{n:02d}" for l in LETRAS for n in range(100)]


def expandir(spec: str) -> tuple[set, set]:
    """Devuelve (códigos de 3 caracteres, códigos de 4 caracteres) de una lista tipo «A00-A09, A40.3, V01.1-V01.9».
    Un rango de cuatro caracteres («K74.0-K74.2», «F32-F33.9») se expande a subcódigos de cuatro caracteres;
    «F32-F33.9» abarca F32.0 … F33.9 y por eso F32 y F33 completos."""
    t3, t4 = set(), set()
    for tok in [x.strip() for x in spec.replace("\n", " ").replace("–", "-").split(",") if x.strip()]:
        a, _, b = tok.partition("-")
        a, b = a.strip().replace(".", ""), (b.strip() or a.strip()).replace(".", "")
        if len(a) == 3 and len(b) == 3:
            t3 |= {c for c in TODOS3 if a <= c <= b}
        else:
            a4 = a if len(a) == 4 else a + "0"
            b4 = b if len(b) == 4 else b + "9"
            t4 |= {c + str(d) for c in TODOS3 if a4[:3] <= c <= b4[:3] for d in range(10) if a4 <= c + str(d) <= b4}
    return t3, t4


def clasificador(filas: list[tuple[object, str, str]]):
    """filas: [(id, especificación, exclusiones)]. Devuelve f(cb) -> id o None.
    Verifica que ninguna pareja de filas reclame el mismo código con la misma especificidad."""
    m3, m4 = {}, {}
    for fid, spec, excl in filas:
        t3, t4 = expandir(spec)
        e3, e4 = expandir(excl) if excl else (set(), set())
        for c in t4 - e4:
            if m4.get(c) not in (None, fid):
                raise ValueError(f"{c} en dos filas: {m4[c]} y {fid}")
            m4[c] = fid
        for c in t3 - e3:
            if m3.get(c) not in (None, fid):
                raise ValueError(f"{c} en dos filas: {m3[c]} y {fid}")
            m3[c] = fid
        for c in e4:                              # exclusión explícita de un subcódigo de un rango de 3
            m4.setdefault(c, None)

    def f(cb: str):
        cb = (cb or "").upper()
        if len(cb) >= 4 and cb[:4] in m4:
            return m4[cb[:4]]
        return m3.get(cb[:3])
    return f
