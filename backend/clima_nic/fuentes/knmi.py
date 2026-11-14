"""Series de KNMI Climate Explorer (https://climexp.knmi.nl), recurso n.º 6 del reto.

Climate Explorer pide verificar que el usuario es humano, así que la serie no se descarga por programa: una
persona la obtiene en la web (ver docs/reto/recursos/contraste.md) y guarda el texto «raw data» tal cual en
data/recursos/contraste/knmi/<producto>_<region>.txt. Este módulo solo lee ese texto.

Formato de Climate Explorer: líneas de comentario que empiezan por «#» (la variable lleva su unidad entre
corchetes, p. ej. «# prcp [mm/day] …»), seguidas de filas «año v1 … v12» (tabla mensual) o «año mes valor».
Los faltantes son -999.9 o menores.
"""
import calendar
import re

# Unidad entre corchetes de la cabecera → factor que da mm en el mes (recibe año y mes).
UNIDADES_MM = {
    "mm/day": lambda a, m: calendar.monthrange(a, m)[1],
    "mm/dy": lambda a, m: calendar.monthrange(a, m)[1],
    "mm/month": lambda a, m: 1.0,
    "mm/mo": lambda a, m: 1.0,
    "mm": lambda a, m: 1.0,
}


def leer_serie(texto):
    """Texto «raw data» de Climate Explorer → {"unidad", "mensual": {(año, mes): mm}, "comentarios": [...]}.

    Rechaza unidades que no sean de precipitación conocida: no se adivinan conversiones.
    """
    comentarios, filas = [], []
    for linea in texto.replace("\r\n", "\n").split("\n"):
        s = linea.strip()
        if not s:
            continue
        if s.startswith("#"):
            comentarios.append(s.lstrip("# ").strip())
        else:
            filas.append(s.split())
    unidad = next((u for c in comentarios for u in re.findall(r"\[([^\]]+)\]", c) if u.strip() in UNIDADES_MM), None)
    if unidad is None:
        raise ValueError("La cabecera de KNMI no declara una unidad de precipitación conocida ([mm/day], [mm/month]…)")
    factor = UNIDADES_MM[unidad.strip()]
    mensual = {}

    def poner(a, m, v):
        if v > -999:
            mensual[(a, m)] = v * factor(a, m)

    for f in filas:
        nums = [float(x) for x in f]
        if len(nums) == 13:
            a = int(nums[0])
            for m, v in enumerate(nums[1:], 1):
                poner(a, m, v)
        elif len(nums) == 3:
            poner(int(nums[0]), int(nums[1]), nums[2])
        else:
            raise ValueError(f"Fila de KNMI con {len(nums)} columnas; se esperaban 13 (tabla mensual) o 3")
    return {"unidad": unidad.strip(), "mensual": mensual, "comentarios": comentarios}


def anual(mensual):
    """{(año, mes): mm} → {año: mm} solo con años de 12 meses válidos."""
    por = {}
    for (a, m), v in mensual.items():
        por.setdefault(a, {})[m] = v
    return {a: sum(ms.values()) for a, ms in sorted(por.items()) if len(ms) == 12}
