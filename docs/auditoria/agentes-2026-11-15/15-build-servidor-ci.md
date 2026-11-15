# Agente 15: Build, Servidor Local y CI

- **Base auditada:** `origin/main` (`20bec48`)
- **Fecha:** 2026-11-15

---

## Build, Deploy, Local Server & CI Audit (`wt_audit20`, HEAD `20bec48`)

### Confirmed Findings

1. **[High] Silent build failure, exit code `0`, and inconsistent `global_meta.json` when forecast tasks fail**
   - **File:Line (Symbol):** `scripts/preparar_meteo.mjs:46-52, 76-79` (top-level `ejecutar` + `guardar('global_meta', ...)`)
   - **What happens & why it is a bug:** If `/api/global_meta` succeeds and then downstream tasks in `tareas` fail (even 100% failure, `0/N` resources), `preparar_meteo.mjs` still overwrites `public/clima-base/global_meta.json` with the new `meta.corrida_utc`, prints only `console.warn('Datos meteorológicos parciales:', ...)`, and exits with code `0`.
     - On a clean build (no prior snapshot), this violates lines 44–45 (which require failing the build on a clean clone so Render keeps the prior deployment instead of publishing a broken demo with no forecast grids/layers/CSVs).
     - On a build with an existing snapshot, overwriting `global_meta.json` with the new `corrida_utc` while `global-*.json` tasks fail leaves stale `global-<var>-<paso>.json` files from the previous `corrida_utc` on disk (rejected by `app/campo.js:44` and `app/globo.js:17` as `corrida_utc` mismatch / `'Stale run'`). On a later `global_meta` outage, line 46 (`existsSync('public/clima-base/global_meta.json')`) also treats that empty/broken `global_meta.json` as a valid prior snapshot and exits `0`.
   - **Verification/Repro evidence:** Reproduced in an isolated temp directory with `node --input-type=module -e` against a mock HTTP server returning `200` for `/api/global_meta` (`horas_utc` length 1) and `404` for all other endpoints:
     - `exit: 0`
     - `stdout: Malla meteorológica 2026-11-15T12:00:00Z: 0/17 recursos.`
     - `stderr: Datos meteorológicos parciales: ... (17 HTTP 404 failures)`
     - `files: [ 'global_meta.json' ]`

2. **[Medium] Missing `.md` MIME type (and case-sensitive extension lookup) in local static server**
   - **File:Line (Symbol):** `scripts/servir-local.mjs:7, 21` (`types`, `http.createServer` handler)
   - **What happens & why it is a bug:** `index.html:158` links to `<a href="data/hidrologia/fuentes_y_limites.md" target="_blank" rel="noopener">`, and `scripts/preparar_render.mjs:29` copies `data/hidrologia/fuentes_y_limites.md` into `public/data/hidrologia/`. Because `.md` is missing from `types`, `servir-local.mjs` falls back to `application/octet-stream`, causing browsers to download the file instead of opening/displaying it in the new tab. Additionally, `types[path.extname(file)]` does not lowercase the extension, and `.gz` (`public/data/hidrologia/*.geojson.gz`) is absent from `types` (though `app/hidrologia.js:27-32` handles `.gz` via `arrayBuffer()` + `DecompressionStream`).
   - **Verification/Repro evidence:** Verified with Node `path.extname`:
     - `types[path.extname('data/hidrologia/fuentes_y_limites.md')] || 'application/octet-stream'` -> `'application/octet-stream'`
     - `types[path.extname('foto.JPG')] || 'application/octet-stream'` -> `'application/octet-stream'`
   - **Path traversal check:** Clean. Lines 16–18 (`path.resolve(root, '.' + decodeURIComponent(url.pathname))` + `path.relative(root, file)` checking `relative.startsWith('..') || path.isAbsolute(relative)` with `root` ending in path separator) blocked `/..%5cpackage.json` (`rel: ..\package.json`, `blocked: true`), while `new URL(..., 'http://127.0.0.1')` normalized `/%2e%2e/package.json` to `/package.json` and `//evil.com/test` to `/test` inside `root`.

3. **[Medium] UTF-8 without BOM in `scripts/iniciar-local.ps1` causes string mojibake in Windows PowerShell 5.1**
   - **File:Line (Symbol):** `scripts/iniciar-local.ps1:8, 13, 25, 27` (invoked by `INICIAR-APP.cmd:2` via `powershell.exe`)
   - **What happens & why it is a bug:** `INICIAR-APP.cmd:2` launches `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\iniciar-local.ps1"`. Because `scripts/iniciar-local.ps1` is UTF-8 without BOM (`utf8_bom=False`), Windows PowerShell 5.1 decodes it using the system ANSI codepage (Windows-1252) rather than UTF-8, corrupting accented Spanish output and error messages (`aplicación` -> `aplicaciÃ³n`, `está` -> `estÃ¡`, `respondió` -> `respondiÃ³`, `Aplicación` -> `AplicaciÃ³n`).
   - **Verification/Repro evidence:** Checked file bytes (`utf8_bom=False`) and parsed the script with Windows PowerShell 5.1 `[System.Management.Automation.Language.Parser]::ParseFile(...)`:
     - `8: No se pudo compilar la aplicaciÃ³n.`
     - `13: El puerto 8996 estÃ¡ ocupado por otra aplicaciÃ³n.`
     - `25: El servidor local no respondiÃ³.`
     - `27: AplicaciÃ³n disponible en http://127.0.0.1:8996/`

4. **[Low] `scripts/preparar_render.sh` lacks executable mode (`100644`) in git**
   - **File:Line (Symbol):** `scripts/preparar_render.sh:1-4`
   - **What happens & why it is a bug:** Git blob stores `i/lf` line endings (`b'#!/bin/sh\nset -eu\nnode scripts/preparar_render.mjs\nnode scripts/preparar_meteo.mjs\n'`), so Linux checkouts get LF; however, its git file mode is `100644` (not `100755`), so direct execution (`./scripts/preparar_render.sh`) on Linux fails with `Permission denied` unless invoked explicitly via `sh scripts/preparar_render.sh`.
   - **Verification/Repro evidence:** `git ls-files -s scripts/ .github/` -> `100644 5aabcccdb0317e278a5fe4482279274379627b24 0 scripts/preparar_render.sh`; `git ls-files --eol` -> `i/lf`.

---

### Clean / Verified Components

- **`scripts/preparar_render.mjs`**: No stale or missing build file lists found.
  - Verified all 14 source paths copied by `preparar_render.mjs` exist on disk (`index.html`, `app`, `src`, `assets`, `visor`, `data/clima.json`, `data/dominios.geojson`, `data/lugares_mundo.json`, `data/fuentes/oni_2001_2024.csv`, `data/fenomenos_nicaragua.json`, `data/regiones_nicaragua.geojson`, `data/recursos_integrados.json`, `data/hidrologia`, `data/ayuda_preguntas.json`).
  - Verified all 27 frontend-referenced static paths in `index.html`, `app/`, and `src/` exist and are covered by `preparar_render.mjs` (`rutas` recursive copy + `data/hidrologia` recursive copy), and `VARIABLES` (`preparar_render.mjs:14`) includes all 6 variables read by `app/indicadores.js:12-16` (`temperatura_gistemp`, `lluvia_anual_imerg`, `lluvia_jun_nov_imerg`, `ndvi`, plus contrast series `t2m_media`, `lluvia_anual`). (Minor note: `cpSync('data/hidrologia', ...)` also copies `data/hidrologia/.gitattributes` into `public/data/hidrologia/`.)
- **`.github/workflows/actualizar-pronostico.yml`**: No trigger, Node-version, or commit defects found. Triggers (`schedule: cron: "47 */6 * * *"`, `workflow_dispatch`), `concurrency`, `curl -fsS` checks, and missing-secret guard (`RENDER_DEPLOY_HOOK`) are valid; no checkout/commit/Node steps are used. (Minor note: `permissions: {}` is not explicitly declared, and `curl -m 90` / `-m 60` bounds total time across `--retry 3 --retry-delay 20`.)

---

### Files Inspected & Checks Run

- **Files inspected:** `scripts/preparar_meteo.mjs`, `scripts/preparar_render.mjs`, `scripts/preparar_render.sh`, `scripts/servir-local.mjs`, `scripts/iniciar-local.ps1`, `.github/workflows/actualizar-pronostico.yml`, `INICIAR-APP.cmd`, `index.html`, `visor/index.html`, `app/config.js`, `app/hidrologia.js`, `app/indicadores.js`, `app/investigar.js`, `app/shell.js`, `app/campo.js`, `app/globo.js`, `app/graficas-meteo.js`, `src/fuentes-meteo.js`, `src/tendencias.js`, `.gitignore`, `README.md`, `docs/reproduccion.md`, `docs/GLOBO_DETALLE_2026-11-14.md`.
- **Checks run (all in `wt_audit20`, working tree left clean via `git status --short`):**
  - `node --version` (`v24.21.0`) and `node --check` on `scripts/preparar_meteo.mjs`, `scripts/preparar_render.mjs`, `scripts/servir-local.mjs`: **3/3 passed (exit 0)**.
  - Source/frontend path existence checks: **14/14** `preparar_render.mjs` source paths and **27/27** frontend asset/data paths exist.
  - `git ls-files --eol` & `git ls-files -s` on `scripts/` and `.github/`: verified `i/lf` and `100644` mode on `scripts/preparar_render.sh`.
  - Isolated `preparar_meteo.mjs` mock-HTTP reproducer: confirmed exit `0` on `0/17` resource fetches.
  - `servir-local.mjs` path-resolution & MIME lookup check: confirmed traversal blocks and missing `.md` / case-sensitive MIME lookups.
  - Windows PowerShell 5.1 `[System.Management.Automation.Language.Parser]::ParseFile` check on `scripts/iniciar-local.ps1`: confirmed mojibake on lines 8, 13, 25, 27.
