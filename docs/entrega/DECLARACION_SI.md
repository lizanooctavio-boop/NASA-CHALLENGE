# Super Intelligence (SI / AI) Disclosure — Earth Trend Detective

> **Resumen en español (para el equipo)**  
> Este documento recoge la declaración exigida por las guías oficiales de NASA Space Apps 2026 sobre el uso de herramientas de IA (*Super Intelligence*, SI). Detalla qué modelos se utilizaron en código, análisis, documentación y auditoría (**Claude Code (Opus)**, **Codex**, **Claude Opus** y **Gemini**), deja constancia de que la idea del proyecto, las decisiones científicas y estadísticas y las comprobaciones corresponden al equipo humano, e incorpora las reglas obligatorias de **marca de agua visible**, **declaración en el texto** y **metadatos** si el vídeo o las diapositivas de la entrega final incluyen voz, imágenes o vídeo generados por IA (por ejemplo, locución sintética con ElevenLabs). Revisa y valida todos los puntos marcados con **`[CONFIRMAR]`** antes de pulsar *Submit for Judging*.

---

## 1. Human Ownership & Core Responsibility

- **Team Ownership (`[CONFIRMAR]`):** The original concept, scientific questions focused on Nicaragua and contrasting regions (Central America and the Canadian Prairies), the choice of strict multi-method trend criteria (requiring agreement across adjusted-df OLS, Newey–West HAC, Theil–Sen, and modified Mann–Kendall rather than a single uncorrected p-value), and every analytical trade-off were directed, reviewed, and decided by the human team.
- **Accountability:** The team inspected datasets, verified statistical outputs against reproducible scripts and automated tests, documented data gaps and failed/pending endpoints transparently (*e.g.*, blocked Giovanni services, pending AppEEARS/RCM orders, short-record SWOT/OPERA boundaries), and holds full responsibility for the final submission (`[CONFIRMAR]`).

---

## 2. Inventory of Super Intelligence (SI) Tools Used

In compliance with NASA Space Apps Challenge 2026 Participant Terms, Participant FAQs, and Project Submission Guidelines, the team discloses the following SI assistants used during preparation and development:

| SI Tool / Model | Scope of Assistance | Specific Artifacts & Tasks Assisted | Human Oversight & Verification |
| --- | --- | --- | --- |
| **Claude Code (Opus)** | Code authoring, geospatial/statistical backend & refactoring | Backend adapters (`backend/clima_nic/fuentes/`), statistical pipeline (`tendencia_robusta.py`, `fdr.py`, `indicadores.py`, `modelo_estacional.py`), integration and test scaffolding (`[CONFIRMAR]`) | Team reviewed statistical formulas, verified outputs against contract rules (`tendencia.py`), and checked caveats on sample sites, Pettitt step breaks, and GLDAS/MERRA-2 divergence. |
| **Codex** | Code implementation, data-pipeline scripts, UI & cross-checks | Data preparation and validation scripts (`scripts/datos/`, `data/recursos/contraste/`, `data/recursos/csa/`, `data/recursos/tierra/`), 3D/2D web UI (`index.html`, `app/`, `src/`), and *Investigate / Learn / Sources* tabs (`[CONFIRMAR]`) | Team audited branch outputs (`resources`, cross-checks, SAR calibration gates), rejected unvalidated radar masks (`NO_VALIDADA`), and verified numerical consistency across JSON outputs. |
| **Claude Opus** | Scientific framing, methodological design & review | Literature/method comparison, design of statistical safeguards against autocorrelation and multiple comparisons, synthesis of regional climate caveats (`[CONFIRMAR]`) | Team validated methodological choices (e.g., annual aggregation + modified Mann–Kendall instead of inflated monthly OLS) against raw series and reference records. |
| **Gemini** | Submission compliance audit, documentation, accessibility review & script/deck drafting | Compliance checklist against official 2026 rules (`docs/entrega/REQUISITOS_ENTREGA_2026.md`), SI disclosure, English project form draft, 30 s video script & 7-slide deck draft, license/DOI verification, read-only accessibility audit (`docs/entrega/REVISION_ACCESIBILIDAD.md`) | Team reviews and approves all `[CONFIRMAR]`, `[ENLACE]`, and `[VERIFICAR]` placeholders before finalizing submission materials (`[CONFIRMAR]`). |

---

## 3. Compliance with 2026 Media Watermark, Text & Metadata Rules (Demo Video & Slides)

Per the 2026 NASA Space Apps Project Submission Guidelines and Participant FAQs:

1. **Images, Video & Voiceover Generated with SI (`[CONFIRMAR]` — select applicable option before export):**
   - **Option A — Purely human-recorded voice/screen capture (no SI voice or generated images):** State explicitly in the submission text and video/slide metadata: *"Screen captures of our web application, live charts, and team-recorded voiceover contain no SI-generated video, imagery, or synthetic voice. SI tools (Claude Code (Opus), Codex, Claude Opus, Gemini) assisted code development, data analysis scaffolding, documentation, and review."*
   - **Option B — SI-generated voiceover (e.g., ElevenLabs) or SI-generated graphics/clips included in the 30 s demo or slides:**
     - **Visible On-Screen Watermark (MANDATORY):** Place a permanent, clearly legible visual badge/watermark across every frame containing SI audio, imagery, or video — for example, bottom-right overlay: `SI-Generated Voiceover / SI-Assisted Media` (plus tool name, e.g., `Audio: ElevenLabs SI`).
     - **Written Text Disclosure (MANDATORY):** Disclose the specific SI media tool (`[CONFIRMAR: e.g., ElevenLabs / image tool]`) inside the *Project Submission Form* (`Use of Super Intelligence` / `Detailed Project Description`) and on the final slide (`Slide 7` credits).
     - **File & Platform Metadata (MANDATORY):** Include SI tool attribution in the video upload title/description (YouTube/Vimeo/Loom description), slide deck speaker notes/file properties (`Author/Comments`), and repository release notes.
2. **Prohibited Branding Check:**
   - Do **not** overlay NASA, CSA, or NOAA logos, Space Apps mission patches, or official agency flags onto SI-generated or team-created visuals. Text attribution of datasets and resources is used exclusively.

---

## 4. Short Disclosure Statement (Ready to Paste into the Space Apps Submission Form)

> We developed **Earth Trend Detective** with human-directed design, data selection, and scientific validation, supported by Super Intelligence (SI) software assistants: **Claude Code (Opus)**, **Codex**, **Claude Opus**, and **Gemini** assisted with Python/JavaScript implementation, Earthdata/NOAA/CSA data-ingestion scripts, statistical verification tests, accessibility auditing, and bilingual documentation. All research questions, statistical acceptance thresholds (requiring agreement across adjusted-df OLS, Newey–West HAC, Theil–Sen, and modified Mann–Kendall), interpretation of conflicting cross-checks, and final project decisions were made and verified by the team. `[CONFIRMAR: Specify whether the 30-second demo narration is human-recorded ("All demo narration and UI screen captures are team-recorded without synthetic media") OR uses synthetic voice/imagery ("Synthetic voiceover generated with <Tool> is visibly watermarked in the video frames and noted in the video metadata and project credits.")]`
