"""Series observadas de las Américas y el Caribe para la pestaña Investigate.

Lee los CSV versionados en data/recursos/hallazgos/ producidos por generar_americas.py y construye
cada serie mediante recursos._investigacion(). Si los CSV no existen (p. ej. en pruebas con datos
sintéticos aislados), devuelve listas vacías sin fallar.
"""
from pathlib import Path

from . import recursos as _rec

LUGARES = {
    "colorado_lees_ferry": ("Colorado River at Lees Ferry", "Arizona, USA", [36.86, -111.59], 6),
    "permafrost_deadhorse": ("Deadhorse permafrost borehole (North Slope)", "Alaska, USA", [70.16, -148.47], 6),
    "permafrost_west_dock": ("West Dock permafrost borehole (Prudhoe Bay)", "Alaska, USA", [70.37, -148.55], 6),
    "permafrost_franklin_bluffs": ("Franklin Bluffs permafrost borehole", "Alaska, USA", [69.67, -148.72], 6),
    "permafrost_chandalar_shelf": ("Chandalar Shelf permafrost borehole (Brooks Range)", "Alaska, USA", [68.07, -149.58], 6),
    "permafrost_alert": ("Alert borehole 2 (Ellesmere Island)", "Nunavut, Canada", [82.50, -62.42], 5),
    "lago_superior_bayfield": ("Lake Superior at Bayfield", "Wisconsin, USA", [46.81, -90.81], 7),
    "lago_monona": ("Lake Monona", "Wisconsin, USA", [43.05, -89.37], 9),
    "lago_mendota": ("Lake Mendota", "Wisconsin, USA", [43.10, -89.40], 9),
    "lago_simcoe": ("Lake Simcoe", "Ontario, Canada", [44.38, -79.68], 8),
    "lago_utopia": ("Lake Utopia", "New Brunswick, Canada", [45.10, -66.73], 8),
    "chile_central": ("Central Chile (30°S–38°S)", "Chile (30°S–38°S, 73°W–69.5°W)", [-33.5, -71.0], 5),
    "nordeste_brasil": ("Semiarid Northeast Brazil (Caatinga)", "Brazil (16°S–3°S, 45°W–35°W)", [-9.5, -40.5], 5),
    "atlantico_norte_ciclones": ("North Atlantic hurricane basin", "North Atlantic (5°N–45°N, 100°W–20°W)", [22.0, -65.0], 4),
    "pacifico_oriental_ciclones": ("Eastern North Pacific hurricane basin", "Eastern North Pacific (5°N–32°N, 140°W–90°W)", [16.0, -112.0], 4),
    "snotel_blewett_pass": ("Blewett Pass SNOTEL (Cascades)", "Washington, USA", [47.35, -120.68], 7),
    "snotel_arbuckle_mtn": ("Arbuckle Mountain SNOTEL (Blue Mountains)", "Oregon, USA", [45.19, -119.25], 7),
    "snotel_bateman": ("Bateman SNOTEL (Southern Rockies)", "New Mexico, USA", [36.52, -106.32], 7),
    "snotel_niwot": ("Niwot Ridge SNOTEL (Front Range)", "Colorado, USA", [40.04, -105.54], 7),
    "lago_poopo": ("Lake Poopó (Altiplano)", "Bolivia", [-18.8, -67.1], 7),
    "lago_titicaca": ("Lake Titicaca (Altiplano)", "Peru and Bolivia", [-15.8, -69.4], 7),
    "lago_mar_chiquita": ("Mar Chiquita (endorheic lake)", "Argentina", [-30.7, -62.6], 7),
    "lago_colhue_huapi": ("Lake Colhué Huapi (Patagonia)", "Argentina", [-45.5, -68.8], 7),
    "lago_argentino": ("Lago Argentino (Southern Patagonian Ice Field)", "Argentina", [-50.2, -72.8], 7),
    "lago_junin": ("Lake Junín (Central Andes)", "Peru", [-11.0, -76.1], 8),
}

# Fusionar lugares al importar el módulo para que recursos.LUGARES los incluya automáticamente.
_rec.LUGARES.update(LUGARES)

ESTUDIOS = {
    "colorado": (
        "Published check: Twenty-first-century Colorado River flows dropped about 19% below the 20th-century average, "
        "with warming cutting mean discharge by roughly 9.3% per °C through snow-albedo feedback "
        "(Udall & Overpeck 2017, doi:10.1002/2016WR019638; Milly & Dunne 2020, doi:10.1126/science.aay9187)."
    ),
    "permafrost": (
        "Published check: Borehole observations show Arctic continuous permafrost warmed by +0.39 ± 0.15 °C per decade "
        "over 2007–2016 (Biskaborn et al. 2019, doi:10.1038/s41467-018-08240-4), with North Slope Alaska sites "
        "warming by +0.52 to +0.83 °C per decade since the late 1970s (Smith et al. 2022, doi:10.1038/s43017-021-00240-1)."
    ),
    "hielo_lagos": (
        "Published check: Northern Hemisphere lake ice cover duration shortened by 0.7 to 4.3 days per decade "
        "over 1855–2005 (Benson et al. 2012, doi:10.1007/s10584-011-0212-8; Magnuson et al. 2000, doi:10.1126/science.289.5485.1743)."
    ),
    "chile_central": (
        "Published check: Central Chile experienced a drying trend of about 7.1% per decade over 1979–2014 "
        "(Boisier et al. 2016, doi:10.1002/2015GL067265), escalating into an unbroken 20–40% rainfall deficit "
        "megadrought since 2010 (Garreaud et al. 2020, doi:10.1002/joc.6219)."
    ),
    "nordeste_brasil": (
        "Published check: Semiarid Northeast Brazil endured its most severe multi-year drought on record during 2011–2016 "
        "with 16 of 25 years below normal since the mid-1990s (Marengo et al. 2018, doi:10.1590/0001-3765201720170206; "
        "Brito et al. 2018, doi:10.1002/joc.5225), alongside declining station totals and intensifying dry spells "
        "(Costa et al. 2020, doi:10.1016/j.wace.2020.100254)."
    ),
    "huracanes_ri": (
        "Published check: Homogenized satellite records show North Atlantic peak 24-hour intensification rates rose by "
        "28.7% between 1971–1990 and 2001–2020 (Garner 2023, doi:10.1038/s41598-023-42669-y; Bhatia et al. 2019, "
        "doi:10.1038/s41467-019-08471-z), whereas raw best-track storm proportions are sensitive to improved detection "
        "of short-lived storms (Klotzbach et al. 2022, doi:10.1029/2021GL095774)."
    ),
    "snotel_swe": (
        "Published check: Over 90% of long-term mountain snow monitoring sites across the western United States show "
        "declines in April 1 snow water equivalent, averaging a 15–30% loss since mid-century "
        "(Mote et al. 2018, doi:10.1038/s41612-018-0012-1)."
    ),
    "lagos_altiplano": (
        "Published check: Shallow Lake Poopó dried out completely in late 2015 under combined warming-driven evaporation, "
        "El Niño anomalies, and upstream diversions from regulated Lake Titicaca "
        "(Satgé et al. 2017, doi:10.3390/rs9030218; Torres-Batlló et al. 2019, doi:10.3390/rs12010073)."
    ),
}


def americas(carpeta: Path) -> tuple[list[dict], list[Path]]:
    """Construye las investigaciones y lista de archivos de entrada para las Américas y el Caribe."""
    carpeta = Path(carpeta)
    invs, entradas = [], []

    # 1. Cuenca del río Colorado en Lees Ferry (USGS 09380000: 1922–2025 y 1963–2025)
    ruta = carpeta / "colorado_lees_ferry_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        usgs_fuente = {
            "producto": "USGS National Water Information System (NWIS) gauge 09380000 at Lees Ferry, Arizona",
            "url": "https://waterservices.usgs.gov/nwis/stat/?format=rdb&sites=09380000&statReportType=annual&statTypeCd=mean&parameterCd=00060",
        }
        filas = sorted(_rec._leer_csv(ruta), key=lambda f: int(f["anio"]))
        anios_tot = [int(f["anio"]) for f in filas]
        vals_tot = [float(f["volumen_km3"]) for f in filas]
        pre63 = [v for a, v in zip(anios_tot, vals_tot) if a < 1963]
        pos63_pares = [(a, v) for a, v in zip(anios_tot, vals_tot) if a >= 1963]
        anios_pos = [a for a, _ in pos63_pares]
        vals_pos = [v for _, v in pos63_pares]
        t_pos = _rec.tendencia_compacta(anios_pos, vals_pos, "km³")
        t_tot = _rec.tendencia_compacta(anios_tot, vals_tot, "km³")

        invs.append(_rec._investigacion(
            "cuenca_colorado_caudal",
            "agua",
            "colorado_lees_ferry",
            "Colorado River annual discharge (since 1922)",
            "Total yearly river volume passing Lees Ferry, Arizona, the legal dividing point between the Upper and "
            "Lower Colorado River basins.",
            "km³",
            anios_tot,
            vals_tot,
            usgs_fuente,
            notas=[
                f"Average before Glen Canyon Dam ({anios_tot[0]}–1962): {sum(pre63) / len(pre63):.1f} km³ per year; "
                f"since 1963: {sum(vals_pos) / len(vals_pos):.1f} km³ per year.",
                f"Since 1963 only (regulated releases from Lake Powell): {_rec._frase_tendencia(t_pos, 'km³')}.",
                ESTUDIOS["colorado"],
            ],
        ))
        invs.append(_rec._investigacion(
            "cuenca_colorado_caudal_pos1963",
            "agua",
            "colorado_lees_ferry",
            "Colorado River regulated flow (since 1963)",
            "Yearly river volume at Lees Ferry since Glen Canyon Dam closed in 1963, where legal delivery rules buffer "
            "year-to-year swings.",
            "km³",
            anios_pos,
            vals_pos,
            usgs_fuente,
            notas=[
                "Glen Canyon Dam (Lake Powell) began regulating releases in 1963 to meet fixed compact deliveries, "
                "masking natural streamflow losses until reservoir storage drops heavily.",
                f"Full record since {anios_tot[0]}: {_rec._frase_tendencia(t_tot, 'km³')}.",
                ESTUDIOS["colorado"],
            ],
        ))

    # 2. Permafrost profundo (MAGT) en Alaska y Canadá (GTN-P, PANGAEA 10.1594/PANGAEA.930669)
    ruta = carpeta / "gtnp_permafrost_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        gtnp_fuente = {
            "producto": "GTN-P long-term permafrost borehole temperature archive (PANGAEA)",
            "url": "https://doi.org/10.1594/PANGAEA.930669",
        }
        filas = _rec._leer_csv(ruta)
        meta_pozos = {
            "deadhorse": (
                "permafrost_deadhorse",
                "Permafrost ground temperature at Deadhorse",
                "Mean annual ground temperature at 20 m depth in continuous Arctic permafrost on Alaska's North Slope.",
            ),
            "west_dock": (
                "permafrost_west_dock",
                "Permafrost ground temperature at West Dock",
                "Mean annual ground temperature at 20 m depth near the Beaufort Sea coast at Prudhoe Bay, Alaska.",
            ),
            "franklin_bluffs": (
                "permafrost_franklin_bluffs",
                "Permafrost temperature at Franklin Bluffs",
                "Mean annual ground temperature at 20 m depth in inland North Slope tundra south of Prudhoe Bay, Alaska.",
            ),
            "chandalar_shelf": (
                "permafrost_chandalar_shelf",
                "Permafrost temperature at Chandalar Shelf",
                "Mean annual ground temperature at 20 m depth in the Brooks Range foothills of northern Alaska.",
            ),
            "alert_2": (
                "permafrost_alert",
                "Permafrost ground temperature at Alert 2",
                "Mean annual ground temperature at 24.4 m depth at Alert on northern Ellesmere Island, Nunavut, Canada.",
            ),
        }
        for sitio, (lugar, titulo, definicion) in meta_pozos.items():
            propias = sorted((f for f in filas if f["sitio"] == sitio), key=lambda f: int(f["anio"]))
            if not propias:
                continue
            anios = [int(f["anio"]) for f in propias]
            valores = [float(f["magt_c"]) for f in propias]
            prof = propias[0]["profundidad_m"]
            cambio = valores[-1] - valores[0]
            notas = [
                f"Measured at {prof} m depth, where seasonal summer-winter cycles fade out: "
                f"from {_rec._menos(f'{valores[0]:.2f}')} °C in {anios[0]} to {_rec._menos(f'{valores[-1]:.2f}')} °C in {anios[-1]} "
                f"({_rec._menos(f'{cambio:+.2f}')} °C).",
                ESTUDIOS["permafrost"],
            ]
            invs.append(_rec._investigacion(
                f"canada_alaska_permafrost_magt_{sitio}",
                "polos",
                lugar,
                titulo,
                definicion,
                "°C",
                anios,
                valores,
                gtnp_fuente,
                notas=notas,
            ))

    # 3. Fenología de hielo lacustre en Norteamérica (NSIDC G01377)
    ruta = carpeta / "nsidc_hielo_lagos_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        nsidc_fuente = {
            "producto": "Global Lake and River Ice Phenology Database, Version 1 (NSIDC G01377)",
            "url": "https://noaadata.apps.nsidc.org/NOAA/G01377/liag_freeze_thaw_table.csv",
        }
        filas = _rec._leer_csv(ruta)
        meta_lagos = {
            "JJM33": (
                "norteamerica_hielo_lagos_bayfield",
                "lago_superior_bayfield",
                "Lake Superior ice cover at Bayfield",
                "Days of winter ice cover each season at Bayfield, Wisconsin, on the southern shore of Lake Superior.",
                False,
            ),
            "DMR2": (
                "norteamerica_hielo_lagos_monona",
                "lago_monona",
                "Lake Monona winter ice duration",
                "Days between autumn freeze-up and spring ice breakup on Lake Monona in Madison, Wisconsin.",
                False,
            ),
            "DMR1": (
                "norteamerica_hielo_lagos_mendota",
                "lago_mendota",
                "Lake Mendota winter ice duration",
                "Days of winter ice cover each season on Lake Mendota, Wisconsin, tracked since the mid-19th century.",
                False,
            ),
            "PJD28": (
                "norteamerica_hielo_lagos_simcoe",
                "lago_simcoe",
                "Lake Simcoe ice duration (to 1995)",
                "Days of winter ice cover on Lake Simcoe, Ontario, showing a Canadian record that stops in the mid-1990s.",
                True,
            ),
            "WRS310": (
                "norteamerica_hielo_lagos_utopia",
                "lago_utopia",
                "Lake Utopia ice duration (to 1994)",
                "Days of winter ice cover on Lake Utopia, New Brunswick, before Canadian ground reporting ended in 1994.",
                True,
            ),
        }
        for codigo, (id_inv, lugar, titulo, definicion, truncado) in meta_lagos.items():
            propias = sorted((f for f in filas if f["lakecode"] == codigo), key=lambda f: int(f["anio"]))
            if not propias:
                continue
            anios = [int(f["anio"]) for f in propias]
            valores = [float(f["duracion_dias"]) for f in propias]
            notas = [
                f"Record covers {len(anios)} winters between {anios[0]} and {anios[-1]} "
                f"(average {sum(valores) / len(valores):.0f} days of ice cover)."
            ]
            if truncado:
                notas.append(
                    f"Canadian ground observations in NSIDC G01377 for this lake end in {anios[-1]}, missing the strong "
                    "post-1995 warming seen in US lakes updated through 2018–2019."
                )
            notas.append(ESTUDIOS["hielo_lagos"])
            invs.append(_rec._investigacion(
                id_inv,
                "polos",
                lugar,
                titulo,
                definicion,
                "days",
                anios,
                valores,
                nsidc_fuente,
                notas=notas,
            ))

    # 4 y 5. Megasequía de Chile central y lluvia en el Semiárido del Nordeste de Brasil (CHIRPS v2.0 + CRU TS 4.10)
    ruta = carpeta / "americas_lluvia_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        chirps_f = {
            "producto": "CHIRPS v2.0 global precipitation (UCSB Climate Hazards Center via NOAA CoastWatch ERDDAP)",
            "url": "https://coastwatch.pfeg.noaa.gov/erddap/griddap/chirps20GlobalMonthlyP05.html",
        }
        cru_f = {
            "producto": "CRU TS v4.10 monthly gridded precipitation at 0.5° (Climatic Research Unit, University of East Anglia)",
            "url": "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/",
        }
        filas = _rec._leer_csv(ruta)

        def _extraer_lluvia(reg, fte, var):
            sub = sorted(
                (f for f in filas if f["region"] == reg and f["fuente"] == fte and f["variable"] == var),
                key=lambda f: int(f["anio"]),
            )
            return [int(f["anio"]) for f in sub], [float(f["mm"]) for f in sub]

        # Caso 4: Chile central
        ch_a_ch, ch_v_ch = _extraer_lluvia("chile_central", "chirps", "anual")
        ch_a_cru, ch_v_cru = _extraer_lluvia("chile_central", "cru", "anual")
        if ch_a_ch and ch_a_cru:
            pre2010 = [v for a, v in zip(ch_a_ch, ch_v_ch) if a < 2010]
            pos2010 = [v for a, v in zip(ch_a_ch, ch_v_ch) if a >= 2010]
            deficit_pct = 100.0 * (sum(pos2010) / len(pos2010) - sum(pre2010) / len(pre2010)) / (sum(pre2010) / len(pre2010))
            t_cru_ch = _rec.tendencia_compacta(ch_a_cru, ch_v_cru, "mm")
            t_ch_ch = _rec.tendencia_compacta(ch_a_ch, ch_v_ch, "mm")

            invs.append(_rec._investigacion(
                "chile_central_megasequia",
                "lluvia",
                "chile_central",
                "Central Chile yearly rainfall (CHIRPS)",
                "Area-averaged annual rainfall across Central Chile (30°S–38°S), tracking the multi-year megadrought "
                "that began in 2010.",
                "mm",
                ch_a_ch,
                ch_v_ch,
                chirps_f,
                notas=[
                    f"Average 2010–{ch_a_ch[-1]} ({sum(pos2010) / len(pos2010):.0f} mm) is "
                    f"{_rec._menos(f'{deficit_pct:+.0f}')}% compared with 1981–2009 ({sum(pre2010) / len(pre2010):.0f} mm).",
                    f"Longer gauge record (CRU TS 4.10, {ch_a_cru[0]}–{ch_a_cru[-1]}): {_rec._frase_tendencia(t_cru_ch, 'mm')}.",
                    ESTUDIOS["chile_central"],
                ],
            ))
            invs.append(_rec._investigacion(
                "chile_central_megasequia_cru",
                "lluvia",
                "chile_central",
                "Central Chile yearly rainfall (CRU)",
                "Long-term gridded rain-gauge annual precipitation across Central Chile (30°S–38°S) since 1951 from CRU TS 4.10.",
                "mm",
                ch_a_cru,
                ch_v_cru,
                cru_f,
                notas=[
                    f"Satellite-gauge record since 1981 (CHIRPS v2.0): {_rec._frase_tendencia(t_ch_ch, 'mm')}.",
                    ESTUDIOS["chile_central"],
                ],
            ))

        # Caso 5: Nordeste de Brasil (Semiárido)
        ne_a_ch, ne_v_ch = _extraer_lluvia("nordeste_brasil", "chirps", "anual")
        ne_af_ch, ne_vf_ch = _extraer_lluvia("nordeste_brasil", "chirps", "fmam")
        ne_a_cru, ne_v_cru = _extraer_lluvia("nordeste_brasil", "cru", "anual")
        if ne_a_ch and ne_a_cru:
            sequia_12_16 = [v for a, v in zip(ne_a_ch, ne_v_ch) if 2012 <= a <= 2016]
            t_cru_ne = _rec.tendencia_compacta(ne_a_cru, ne_v_cru, "mm")
            t_ch_ne = _rec.tendencia_compacta(ne_a_ch, ne_v_ch, "mm")

            invs.append(_rec._investigacion(
                "nordeste_brasil_semiarido_lluvia",
                "lluvia",
                "nordeste_brasil",
                "Northeast Brazil yearly rainfall (CHIRPS)",
                "Yearly total rainfall over semiarid Northeast Brazil (Caatinga, 16°S–3°S, 45°W–35°W), shaped by strong "
                "El Niño and tropical Atlantic swings.",
                "mm",
                ne_a_ch,
                ne_v_ch,
                chirps_f,
                notas=[
                    f"2012–2016 drought average: {sum(sequia_12_16) / len(sequia_12_16):.0f} mm per year, compared with the "
                    f"{ne_a_ch[0]}–{ne_a_ch[-1]} average of {sum(ne_v_ch) / len(ne_v_ch):.0f} mm.",
                    f"CRU TS 4.10 gauge record ({ne_a_cru[0]}–{ne_a_cru[-1]}): {_rec._frase_tendencia(t_cru_ne, 'mm')}.",
                    ESTUDIOS["nordeste_brasil"],
                ],
            ))
            if ne_af_ch:
                invs.append(_rec._investigacion(
                    "nordeste_brasil_semiarido_lluvia_fmam",
                    "lluvia",
                    "nordeste_brasil",
                    "Northeast Brazil rainy-season rain (CHIRPS)",
                    "February–May (FMAM) main rainy-season total across semiarid Northeast Brazil from CHIRPS v2.0.",
                    "mm",
                    ne_af_ch,
                    ne_vf_ch,
                    chirps_f,
                    notas=[
                        "February to May brings the core rainy season in the northern Sertão as the Intertropical "
                        "Convergence Zone migrates south.",
                        ESTUDIOS["nordeste_brasil"],
                    ],
                ))
            invs.append(_rec._investigacion(
                "nordeste_brasil_semiarido_lluvia_cru",
                "lluvia",
                "nordeste_brasil",
                "Northeast Brazil yearly rainfall (CRU)",
                "Gridded rain-gauge annual precipitation over semiarid Northeast Brazil since 1951 from CRU TS 4.10.",
                "mm",
                ne_a_cru,
                ne_v_cru,
                cru_f,
                notas=[
                    f"CHIRPS v2.0 satellite-gauge record ({ne_a_ch[0]}–{ne_a_ch[-1]}): {_rec._frase_tendencia(t_ch_ne, 'mm')}.",
                    ESTUDIOS["nordeste_brasil"],
                ],
            ))

    # 6. Rápida intensificación de huracanes en el Atlántico Norte (NA) y Pacífico Oriental (EP)
    ruta = carpeta / "ibtracs_ri_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        ib_fuente = {
            "producto": "IBTrACS v04r01 tropical cyclone best-track archive (NOAA NCEI)",
            "url": "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/",
        }
        filas = _rec._leer_csv(ruta)
        for cuenca, sufijo, lugar, nombre_cuenca in (
            ("NA", "na", "atlantico_norte_ciclones", "North Atlantic"),
            ("EP", "ep", "pacifico_oriental_ciclones", "Eastern Pacific"),
        ):
            propias = sorted((f for f in filas if f["cuenca"] == cuenca), key=lambda f: int(f["anio"]))
            if not propias:
                continue
            anios = [int(f["anio"]) for f in propias]
            pasos = [float(f["pasos_ri"]) for f in propias]
            pcts = [float(f["pct_tormentas_ri"]) for f in propias]
            pico_pasos = max(zip(pasos, anios))
            invs.append(_rec._investigacion(
                f"huracanes_rapida_intensificacion_{sufijo}_pasos",
                "ciclones",
                lugar,
                f"{nombre_cuenca} rapid intensification steps",
                f"Yearly count of 6-hour synoptic track intervals in the {nombre_cuenca} where maximum sustained wind "
                "rose by at least 30 knots in 24 hours.",
                "steps",
                anios,
                pasos,
                ib_fuente,
                notas=[
                    f"Peak season in {anios[0]}–{anios[-1]}: {pico_pasos[1]} with {pico_pasos[0]:.0f} rapid-intensification "
                    f"6-hour steps (average {sum(pasos) / len(pasos):.1f} steps per year).",
                    ESTUDIOS["huracanes_ri"],
                ],
            ))
            invs.append(_rec._investigacion(
                f"huracanes_rapida_intensificacion_{sufijo}_pct",
                "ciclones",
                lugar,
                f"{nombre_cuenca} storms with rapid intensification",
                f"Percentage of tracked {nombre_cuenca} storms each year that underwent at least one 24-hour wind jump "
                "of 30 knots or more in raw IBTrACS.",
                "%",
                anios,
                pcts,
                ib_fuente,
                notas=[
                    "Modern satellite and aircraft monitoring detect more short-lived weak tropical storms, which increases "
                    "the total storm denominator in raw IBTrACS.",
                    ESTUDIOS["huracanes_ri"],
                ],
            ))

    # 7. Equivalente de agua en nieve al 1 de abril en el oeste de EE. UU. (USDA SNOTEL)
    ruta = carpeta / "snotel_swe_abril_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        snotel_f = {
            "producto": "USDA NRCS National Water and Climate Center SNOTEL telemetered snowpack network (AWDB REST API v1)",
            "url": "https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html",
        }
        filas = _rec._leer_csv(ruta)
        meta_snotel = (
            ("blewett_pass_wa", "snotel_blewett_pass", "April 1 snowpack at Blewett Pass", "Washington Cascades"),
            ("arbuckle_mtn_or", "snotel_arbuckle_mtn", "April 1 snowpack at Arbuckle Mountain", "Oregon Blue Mountains"),
            ("bateman_nm", "snotel_bateman", "April 1 snowpack at Bateman", "New Mexico Southern Rockies"),
            ("niwot_co", "snotel_niwot", "April 1 snowpack at Niwot Ridge", "Colorado Front Range"),
        )
        for sitio, lugar, titulo, cordillera in meta_snotel:
            propias = sorted((f for f in filas if f["sitio"] == sitio), key=lambda f: int(f["anio"]))
            if not propias:
                continue
            anios = [int(f["anio"]) for f in propias]
            valores = [float(f["swe_mm"]) for f in propias]
            elev = propias[0]["elev_m"]
            invs.append(_rec._investigacion(
                f"oeste_eeuu_nieve_swe_abril_{sitio}",
                "polos",
                lugar,
                titulo,
                f"Snow water equivalent (water depth if the snowpack melted) measured on April 1 at {propias[0]['nombre']} "
                f"({cordillera}, {elev} m elevation).",
                "mm",
                anios,
                valores,
                snotel_f,
                notas=[
                    f"Average April 1 snow water equivalent ({anios[0]}–{anios[-1]}): {sum(valores) / len(valores):.0f} mm "
                    f"at {elev} m elevation.",
                    "Mid-elevation Pacific Northwest and Southwest sites lose snowpack fastest to winter warming, whereas "
                    "cold high-altitude Colorado sites (~3,000 m) stay below freezing longer.",
                    ESTUDIOS["snotel_swe"],
                ],
            ))

    # 8. Lagos del Altiplano (Titicaca, Poopó) y Sudamérica en NASA GSFC G-REALM
    ruta = carpeta / "grealm_lagos_sudamerica_anual.csv"
    if ruta.is_file():
        entradas.append(ruta)
        grealm_f = {
            "producto": "NASA GSFC Global Water Monitor (G-REALM) satellite radar altimetry lake levels",
            "url": "https://earth.gsfc.nasa.gov/gwm/lake/Index",
        }
        filas = _rec._leer_csv(ruta)
        meta_grealm = (
            (
                "poopo",
                "lago_poopo",
                "Lake Poopó water level",
                "Annual satellite radar altimetry surface elevation (EGM2008) of shallow endorheic Lake Poopó on the Bolivian Altiplano.",
                "Shallow saline basin (~3 m deep) that dried out completely in late 2015; radar altimetry reflects dry salt flats during desiccation spells and has a mission gap in 2002–2008.",
            ),
            (
                "titicaca",
                "lago_titicaca",
                "Lake Titicaca water level",
                "Annual satellite radar altimetry water surface elevation (EGM2008) of Lake Titicaca in the Andean Altiplano.",
                "Regulated outflow at the Desaguadero River gates and multi-year El Niño/La Niña cycles dominate short-term level swings.",
            ),
            (
                "mar_chiquita",
                "lago_mar_chiquita",
                "Mar Chiquita lake water level",
                "Annual satellite radar altimetry surface elevation (EGM2008) of endorheic Mar Chiquita lake in central Argentina.",
                "Closed saline lake whose level dropped by more than 4 m after its early-2000s highstand.",
            ),
            (
                "colhue_huapi",
                "lago_colhue_huapi",
                "Lake Colhué Huapi water level",
                "Annual satellite radar altimetry surface elevation (EGM2008) of shallow Lake Colhué Huapi in central Patagonia, Argentina.",
                "Shallow Patagonian lake affected by Senguer River diversions and wind evaporation.",
            ),
            (
                "argentino",
                "lago_argentino",
                "Lago Argentino water level",
                "Annual satellite radar altimetry surface elevation (EGM2008) of glacier-fed Lago Argentino in southern Patagonia.",
                "Fed by meltwater from the Southern Patagonian Ice Field (including Perito Moreno and Upsala glaciers).",
            ),
            (
                "junin",
                "lago_junin",
                "Lake Junín water level",
                "Annual satellite radar altimetry surface elevation (EGM2008) of high-Andean Lake Junín (Chinchaycocha) in central Peru.",
                "High-Andean regulated reservoir lake at ~4,080 m elevation.",
            ),
        )
        for lago_id, lugar, titulo, definicion, advertencia in meta_grealm:
            propias = sorted((f for f in filas if f["lago"] == lago_id), key=lambda f: int(f["anio"]))
            if len(propias) < 10:
                continue
            anios = [int(f["anio"]) for f in propias]
            valores = [float(f["nivel_m"]) for f in propias]
            rango_m = max(valores) - min(valores)
            invs.append(_rec._investigacion(
                f"altiplano_lagos_{lago_id}",
                "agua",
                lugar,
                titulo,
                definicion,
                "m",
                anios,
                valores,
                grealm_f,
                notas=[
                    f"Level range over {anios[0]}–{anios[-1]}: {min(valores):.2f} to {max(valores):.2f} m above sea level "
                    f"(span of {rango_m:.2f} m).",
                    advertencia,
                    ESTUDIOS["lagos_altiplano"],
                ],
            ))

    return invs, entradas
