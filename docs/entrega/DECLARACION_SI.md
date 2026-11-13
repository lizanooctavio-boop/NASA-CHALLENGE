# Super Intelligence (SI / AI) Disclosure — Earth Trend Detective

> **Resumen en español (para el equipo)**  
> Este documento prepara la declaración de uso de herramientas de IA (*Super Intelligence*, SI) exigida por las guías de NASA Space Apps 2026. Incluye: (1) una plantilla honesta para que el equipo rellene qué decisiones tomó por su cuenta y qué trabajo propusieron o redactaron las herramientas de SI; (2) el inventario real de herramientas empleadas (**Claude Code (Opus)**, **Codex**, **Claude Opus**, **Gemini** y, de forma condicional, **ElevenLabs** u otra herramienta de medios si se usara en el vídeo); (3) las reglas obligatorias de **marca de agua visible**, **declaración en texto**, **metadatos**, exclusión de **menores de 18 años** y prohibición de logotipos oficiales; y (4) un **bloque limpio listo para pegar** en el formulario de la plataforma separado de la lista **`Pendiente del equipo`**.

---

## 1. Fillable Ownership & Accountability Template (`[CONFIRMAR]` / `[DECISIÓN DEL EQUIPO]`)

Complete and sign off internally on each line below before submitting the project so that the public disclosure reflects exact team responsibility:

- **Decisions made independently by human team members (`[CONFIRMAR]`):**
  - Selection of the Nicaragua and Canadian Prairies geographic study domains and comparative framing (`[CONFIRMAR: team member(s) responsible]`).
  - Adoption of conservative multi-method trend thresholds (`Trend detected`, `Not enough evidence of a trend`, `Methods disagree`, plus `MIN_ANIOS = 10` short-record guard and `NO_VALIDADA` SAR calibration gate) (`[CONFIRMAR: team member(s) responsible]`).
  - Determination not to fabricate missing outputs for queued `AppEEARS` jobs, pending `RCM` orders, or Cloudflare-blocked articles (`[CONFIRMAR]`).
  - Final go/no-go approval of submitted repository, open-source license choice, and pre-event work disclosure after consulting the Managua Local Lead (`[DECISIÓN DEL EQUIPO]`).
- **Work in which SI tools proposed approaches, generated code/text, or audited deliverables (`[CONFIRMAR]`):**
  - Scaffolding and refactoring Python ingestion scripts, statistical test modules, and FastAPI/CLI endpoints (`Claude Code (Opus)`, `Codex`).
  - Drafting frontend HTML/CSS/JavaScript components, 3D/2D map wiring, and plain-language *Learn* explanations (`Codex`, `Claude Code (Opus)`).
  - Reviewing statistical trade-offs, regional dataset caveats, submission compliance, accessibility checks, and drafting English/Spanish delivery documentation (`Claude Opus`, `Gemini`).
- **Human verification & accountability sign-off:**
  - *We confirm that every statistical figure, DOI, license entry, and visual shown in the final submission has been reviewed and verified by the human team against actual repository outputs and primary sources.* (`[CONFIRMAR: Team Lead / Date]`)

---

## 2. Inventory of Super Intelligence (SI) Tools Used

| SI Tool / Model | Scope of Assistance | Specific Artifacts & Tasks Assisted | Human Oversight Required |
| --- | --- | --- | --- |
| **Claude Code (Opus)** | Software engineering & statistical backend scaffolding | Data ingestion adapters, climate indices, trend and FDR test modules, test scaffolding | `[CONFIRMAR]` Team verification of statistical formulas, parameter choices, and test passes. |
| **Codex** | Code authoring, cross-source verification scripts & UI implementation | Data-processing pipelines, cross-check scripts, web UI (*Investigate / Learn / Sources*), submission documentation revisions | `[CONFIRMAR]` Team review of generated JSON outputs, UI behavior, and scientific caveats. |
| **Claude Opus** | Methodological review & caveat synthesis | Multi-method comparison design, autocorrelation/multiple-testing rationale, regional interpretation notes | `[CONFIRMAR]` Team validation of methodological framing against project data. |
| **Gemini** | Compliance checking, delivery drafting & accessibility audit | Review against 2026 submission guides, drafting and refinement of submission forms, demo scripts, license tables, and static accessibility checks | `[CONFIRMAR]` Team sign-off on final wording and manual verification of blocked/pending items. |
| **ElevenLabs / Media SI tool *(conditional)*** | Demo voiceover or visual media generation *(only if used)* | Spoken narration track or slide/video visual asset if not recorded by team members | `[CONFIRMAR]` Remove row if 100% human-recorded; otherwise enforce Section 3 rules. |

---

## 3. Compliance with 2026 Media Watermark, Privacy & Branding Rules

1. **SI-Generated Images, Video & Voiceover Rule (Demo Video & Slides):**
   - **If 100% human-recorded screen captures and human team narration are used:** No visible media watermark is required on visuals; state explicitly in both the submission form and video/slide metadata that captures and narration contain no SI-generated media, while disclosing SI software/documentation assistance listed in Section 2.
   - **If any SI-generated voiceover (e.g., ElevenLabs), image, or video clip is included:**
     - **Visible On-Screen Watermark (MANDATORY):** Place a permanent, readable watermark directly on every affected frame or slide (e.g., `SI-Generated Audio: ElevenLabs` or `SI-Generated Visual: <Tool Name>`).
     - **Text Disclosure (MANDATORY):** Name the exact SI media tool in the Space Apps project form and in Slide 7 / video end credits.
     - **Metadata Disclosure (MANDATORY):** Include the SI media tool attribution in the uploaded video description and PDF/presentation document properties (`Author / Subject / Comments`).
2. **Minors (`< 18` years) Privacy Rule (*Participant Terms*):**
   - «Recognizable names, voices, and likenesses of persons under the age of 18 should not be included in any submission.» Verify ages of anyone speaking, filmed, or credited in the demo and slides.
3. **No Agency Logos Rule:**
   - Do **not** include NASA, CSA, or NOAA logos, Space Apps mission badges, or official flags on any generated or human-made graphic. Use text credits only.

---

## 4. Textos para la plataforma NASA Space Apps

### (a) Bloque limpio, listo para pegar (`Use of Super Intelligence` / plataforma — en inglés)

> We developed Earth Trend Detective with human-directed scientific design and final verification, supported by Super Intelligence (SI) tools: Claude Code (Opus), Codex, Claude Opus, and Gemini assisted with Python data-ingestion scripts, statistical test modules, web interface implementation, accessibility review, and documentation drafting. Team members directed the research questions, multi-method trend criteria (requiring consensus across effective-df OLS, Newey–West HAC, Theil–Sen, and modified Mann–Kendall), interpretation of conflicting datasets, and manual verification of pending or inaccessible endpoints. Screen captures and human narration in our demo contain no SI-generated images, video, or synthetic voice; all datasets and methods are cited in text without agency logos.

---

### (b) Pendiente del equipo (NO pegar en la plataforma)

- **`[CONFIRMAR]`** Verificar si todos los roles reales de **Claude Code (Opus)**, **Codex**, **Claude Opus** y **Gemini** en la tabla §2 coinciden exactamente con lo usado por los 5 autores del repositorio y completar la plantilla de autoría humana de §1.
- **`[CONFIRMAR]`** Si graban el vídeo o las diapositivas con **voz sintética (p. ej. ElevenLabs) o visuales generados por IA**, **sustituir la última oración** del bloque limpio `(a)` por esta versión exacta (rellenando solo el nombre real de la herramienta antes de pegar):
  - *"Synthetic voiceover and/or visuals generated with `<SI Tool Name>` carry a permanent visible on-screen watermark in every affected frame/slide and are disclosed in the file metadata and credits; all remaining UI screen captures are genuine application recordings."*
- **`[CONFIRMAR]`** Comprobar que ninguna persona menor de `18` años aparezca por nombre reconocible, voz o imagen en el vídeo, audio, diapositivas o créditos.
- **`[DECISIÓN DEL EQUIPO]`** Aprobar el texto final de declaración de autoría y trabajo previo antes de marcar **`Confirm All Work is Original`** en el envío.
