"""Pestaña «Help»: data/ayuda_preguntas.json tiene 100 preguntas válidas en inglés y español."""
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PREGUNTAS = json.loads((RAIZ / "data" / "ayuda_preguntas.json").read_text(encoding="utf-8"))
CAMPOS = {"id", "tema", "pregunta_en", "respuesta_en", "pregunta_es", "respuesta_es", "enlace"}
# Enlaces que no son ids del HTML sino botones que crea app/ayuda.js.
ENLACES_PROPIOS = {"ayuda-tour", "ayuda-idioma"}


def test_hay_100_preguntas_con_todos_los_campos():
    assert len(PREGUNTAS) == 100
    for p in PREGUNTAS:
        assert set(p) == CAMPOS, p.get("id")


def test_ids_unicos():
    ids = [p["id"] for p in PREGUNTAS]
    assert len(set(ids)) == len(ids)


def test_pregunta_y_respuesta_en_ingles_y_espanol():
    for p in PREGUNTAS:
        for campo in ("pregunta_en", "respuesta_en", "pregunta_es", "respuesta_es"):
            assert isinstance(p[campo], str) and len(p[campo].strip()) >= 3, (p["id"], campo)
        assert p["pregunta_en"] != p["pregunta_es"], p["id"]
        assert p["respuesta_en"] != p["respuesta_es"], p["id"]


def test_entre_8_y_10_temas_y_todos_conocidos_por_la_interfaz():
    temas = {p["tema"] for p in PREGUNTAS}
    assert 8 <= len(temas) <= 10
    js = (RAIZ / "app" / "ayuda.js").read_text(encoding="utf-8")
    for t in temas:
        assert re.search(rf"\b{t}:\[", js), t


def test_cada_enlace_lleva_a_algo_que_existe():
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'\bid="([^"]+)"', html))
    for p in PREGUNTAS:
        assert p["enlace"] in ids or p["enlace"] in ENLACES_PROPIOS, (p["id"], p["enlace"])


def test_sin_marca_nasa_en_el_personaje_ni_apis():
    tutorial = (RAIZ / "app" / "tutorial.js").read_text(encoding="utf-8")
    assert "Terra" in tutorial
    assert "NASA" not in tutorial and "fetch(" not in tutorial
    assert "localStorage" in tutorial and "try{" in tutorial


def test_index_solo_una_hoja_y_un_script_de_ayuda():
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    assert html.count('href="app/ayuda.css"') == 1
    assert html.count('src="app/ayuda.js"') == 1
    assert "tutorial.js" not in html
