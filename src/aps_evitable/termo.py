"""Cálculo del Termómetro de la Mortalidad: tablas de vida, tasas y sus incertidumbres.

Todo opera sobre arreglos cuyo último eje son los 20 grupos de edad
abreviados del termómetro:

    0 · 1-4 · 5-9 · 10-14 · … · 80-84 · 85+         (G = 19)

La tabla cierra en 85 y más en toda la serie porque hasta 2007 el DANE agrupa
a los mayores de 85 en una sola categoría; cerrar igual todos los años hace
comparable la serie completa.

Convenciones (declaradas en la metodología del tablero):
  · Tabla abreviada de período (Chiang). Radix 100.000.
  · Años vividos por quien muere en el intervalo (nax): 1a0 y 4a1 de Coale y
    Demeny, modelo Oeste, en la versión de Preston, Heuveline y Guillot (2001,
    cuadro 3.3), según la tasa de mortalidad infantil; ambos sexos = promedio de
    las dos fórmulas; resto = n/2; intervalo abierto = 1/M.
  · Población estándar: OMS (Ahmad et al., 2001), pesos por millón tal como los
    publica SEER; 0-4 en un solo grupo; 85+ = 85-89 + 90-94 + 95-99 + 100+.
  · Intervalos de las tasas: Fay y Feuer (1997), aproximación gamma, que el
    NCHS usa para tasas ajustadas por edad; para tasas crudas coincide con el
    intervalo exacto de Poisson.
  · Intervalos de las medidas de la tabla de vida: simulación de Monte Carlo
    con defunciones Poisson por grupo de edad (población fija), percentiles
    2,5 y 97,5.
"""
from __future__ import annotations
import numpy as np
from scipy.stats import chi2

G = 19
X = np.array([0, 1] + list(range(5, 90, 5)), float)               # 0,1,5,…,85
NANCHO = np.array([1, 4] + [5] * 16 + [np.nan], float)
I15, I30, I60, I65, I70, I75 = 4, 7, 13, 14, 15, 16
ETQ = ["0", "1-4"] + [f"{a}-{a+4}" for a in range(5, 85, 5)] + ["85+"]

# OMS 2000–2025, pesos por millón (SEER). 0-4 juntos y 85+ = 4.398 + 1.500 + 400 + 50.
W_OMS = np.array([88569, 86870, 85970, 84670, 82171, 79272, 76073, 71475, 65877, 60379,
                  53681, 45484, 37187, 29590, 22092, 15195, 9097, 6348], float)
assert W_OMS.sum() == 1_000_000


def a_jovenes(m0, sexo):
    """1a0 y 4a1 de Coale-Demeny Oeste (Preston et al. 2001). sexo: 'h','m','t'."""
    m0 = np.asarray(m0, float)
    def h():
        a0 = np.where(m0 >= .107, .330, .045 + 2.684 * m0)
        a1 = np.where(m0 >= .107, 1.352, 1.651 - 2.816 * m0)
        return a0, a1
    def m():
        a0 = np.where(m0 >= .107, .350, .053 + 2.800 * m0)
        a1 = np.where(m0 >= .107, 1.361, 1.522 - 1.518 * m0)
        return a0, a1
    if sexo == "h":
        return h()
    if sexo == "m":
        return m()
    (a, b), (c, d) = h(), m()
    return (a + c) / 2, (b + d) / 2


def tabla(D, N, sexo="t"):
    """Tabla de vida vectorizada. D, N: [..., G]. Devuelve dict de arreglos [..., G]."""
    D = np.asarray(D, float); N = np.asarray(N, float)
    M = np.divide(D, N, out=np.zeros(np.broadcast(D, N).shape), where=N > 0)
    a = np.broadcast_to(NANCHO / 2, M.shape).copy()
    a0, a1 = a_jovenes(M[..., 0], sexo)
    a[..., 0] = a0; a[..., 1] = a1
    n = NANCHO[:-1]
    q = np.ones_like(M)
    q[..., :-1] = np.minimum(n * M[..., :-1] / (1 + (n - a[..., :-1]) * M[..., :-1]), 1.0)
    l = np.empty_like(M); l[..., 0] = 1.0
    l[..., 1:] = np.cumprod(1 - q[..., :-1], axis=-1)
    d = np.empty_like(M); d[..., :-1] = l[..., :-1] - l[..., 1:]; d[..., -1] = l[..., -1]
    L = np.empty_like(M)
    L[..., :-1] = n * l[..., 1:] + a[..., :-1] * d[..., :-1]
    Mo = M[..., -1]
    L[..., -1] = np.where(Mo > 0, l[..., -1] / np.where(Mo > 0, Mo, 1), l[..., -1] * 5)
    a[..., -1] = np.where(Mo > 0, 1 / np.where(Mo > 0, Mo, 1), 5)
    T = np.cumsum(L[..., ::-1], axis=-1)[..., ::-1]
    e = np.divide(T, l, out=np.zeros_like(T), where=l > 0)
    return dict(M=M, a=a, q=q, l=l, d=d, L=L, T=T, e=e)


def medidas(t):
    """Medidas resumen de una tabla (dict de tabla()). Devuelve dict de arreglos [...]."""
    l, d, e, a = t["l"], t["d"], t["e"], t["a"]
    edad = X + a                                         # edad media al morir en cada grupo
    w = d / d.sum(axis=-1, keepdims=True)
    media = (w * edad).sum(-1)
    sd = np.sqrt((w * (edad - media[..., None]) ** 2).sum(-1))
    # e† : esperanza de vida restante a la edad al morir, interpolada en el intervalo
    f = np.zeros_like(a); f[..., :-1] = a[..., :-1] / NANCHO[:-1]
    e_sig = np.concatenate([e[..., 1:], e[..., -1:]], axis=-1)
    e_muerte = e * (1 - f) + e_sig * f
    e_muerte[..., -1] = e[..., -1]
    edag = (d * e_muerte).sum(-1) / l[..., 0]
    return dict(e0=e[..., 0], e65=e[..., I65], q15_60=1 - l[..., I60] / l[..., I15],
                sd0=sd, edag=edag)


def prob_30_70(Dc, N):
    """ODS 3.4.1: probabilidad de morir entre 30 y 70 por las causas de Dc."""
    M = np.divide(Dc[..., I30:I70], N[..., I30:I70], out=np.zeros(np.broadcast(Dc[..., I30:I70], N[..., I30:I70]).shape),
                  where=N[..., I30:I70] > 0)
    q = 5 * M / (1 + 2.5 * M)
    return 1 - np.prod(1 - q, axis=-1)


def a_estandar(D, N):
    """Agrupa los 19 grupos en los 18 de la población estándar (0-4 juntos)."""
    D = np.asarray(D, float); N = np.asarray(N, float)
    Ds = np.concatenate([D[..., :1] + D[..., 1:2], D[..., 2:]], axis=-1)
    Ns = np.concatenate([N[..., :1] + N[..., 1:2], N[..., 2:]], axis=-1)
    return Ds, Ns


def fay_feuer(D, N, w, mult=1e5, alfa=.05, peso_muerte=None):
    """Tasa directamente estandarizada con su intervalo de Fay y Feuer (1997).
    D, N: [..., k]; w: pesos [k] que suman 1; peso_muerte: [k] (p. ej. años de
    vida perdidos por defunción) o None. Devuelve (tasa, ee, lo, hi, muertes)."""
    D = np.asarray(D, float); N = np.asarray(N, float)
    pm = np.ones(D.shape[-1]) if peso_muerte is None else np.asarray(peso_muerte, float)
    c = np.divide(w * pm, N, out=np.zeros(np.broadcast(D, N).shape), where=N > 0)      # contribución por muerte
    y = (c * D).sum(-1)
    v = (c ** 2 * D).sum(-1)
    wm = np.where(N > 0, c, 0).max(-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        lo = np.where(y > 0, v / (2 * y) * chi2.ppf(alfa / 2, 2 * y ** 2 / np.where(v > 0, v, 1)), 0.0)
        hi = (v + wm ** 2) / (2 * (y + wm)) * chi2.ppf(1 - alfa / 2, 2 * (y + wm) ** 2 / (v + wm ** 2))
    lo = np.nan_to_num(lo)
    return y * mult, np.sqrt(v) * mult, lo * mult, hi * mult, D.sum(-1)


def mediana_agrupada(Dg, z=1.959964):
    """Edad mediana al morir desde defunciones por grupo, con interpolación lineal
    dentro del grupo; IC por estadísticos de orden (posiciones n/2 ± z·√n/2)."""
    Dg = np.asarray(Dg, float)
    ancho = np.where(np.isnan(NANCHO), 10.0, NANCHO)        # 85+: se supone 85–95 para interpolar
    n = Dg.sum(-1)
    cum = np.cumsum(Dg, axis=-1)
    def cuantil(p):
        objetivo = p * n
        i = np.argmax(cum >= objetivo[..., None], axis=-1)
        prev = np.take_along_axis(cum, np.maximum(i - 1, 0)[..., None], -1)[..., 0] * (i > 0)
        dentro = np.take_along_axis(Dg, i[..., None], -1)[..., 0]
        frac = np.divide(objetivo - prev, dentro, out=np.zeros_like(objetivo), where=dentro > 0)
        return X[i] + frac * ancho[i]
    med = cuantil(np.full(n.shape, .5))
    hw = np.divide(z * np.sqrt(n) / 2, n, out=np.zeros_like(n), where=n > 0)
    return med, cuantil(np.clip(.5 - hw, 0, 1)), cuantil(np.clip(.5 + hw, 0, 1)), n
