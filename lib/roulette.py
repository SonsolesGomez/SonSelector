"""Componente visual del selector animado (Custom Components v2)."""

from __future__ import annotations

import streamlit as st

_HTML = """
<div class="roulette-root">
  <button type="button" class="roulette-frame" id="roulette-btn" aria-label="Seleccionar alumno">
    <div class="roulette-label">Seleccionando…</div>
    <div class="roulette-name" id="roulette-name">¿Quién será?</div>
    <div class="roulette-hint" id="roulette-hint"></div>
  </button>
</div>
"""

_CSS = """
.roulette-root {
  width: 100%;
  font-family: inherit;
}
.roulette-frame {
  position: relative;
  width: 100%;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem 1.5rem;
  border: none;
  border-radius: 12px;
  background: linear-gradient(160deg, #0078D4 0%, #005A9E 55%, #004578 100%);
  color: #ffffff;
  box-shadow: 0 12px 28px rgba(0, 90, 158, 0.28);
  overflow: hidden;
  cursor: pointer;
  font: inherit;
  transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
}
.roulette-frame:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 16px 32px rgba(0, 90, 158, 0.34);
  filter: brightness(1.04);
}
.roulette-frame:active:not(:disabled) {
  transform: translateY(1px);
}
.roulette-frame:focus-visible {
  outline: 3px solid #FFB900;
  outline-offset: 3px;
}
.roulette-frame:disabled {
  cursor: not-allowed;
  filter: grayscale(0.25);
  opacity: 0.85;
}
.roulette-frame::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(255,255,255,0.18), transparent 45%),
    radial-gradient(circle at 80% 80%, rgba(255,255,255,0.1), transparent 40%);
  pointer-events: none;
}
.roulette-label {
  position: relative;
  font-size: 0.95rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  opacity: 0.85;
  font-weight: 600;
}
.roulette-name {
  position: relative;
  font-size: clamp(1.8rem, 5vw, 3.2rem);
  font-weight: 700;
  line-height: 1.15;
  text-align: center;
  min-height: 1.2em;
  transition: transform 0.08s ease, opacity 0.08s ease;
}
.roulette-name.is-spinning {
  transform: scale(1.03);
  opacity: 0.92;
}
.roulette-name.is-winner {
  transform: scale(1.08);
  text-shadow: 0 0 24px rgba(255, 255, 255, 0.45);
}
.roulette-hint {
  position: relative;
  min-height: 1.25em;
  font-size: 1rem;
  opacity: 0.9;
}
.roulette-frame.is-idle {
  background: linear-gradient(160deg, #5B9BD5 0%, #2B88D8 55%, #0078D4 100%);
}
.roulette-frame.is-done {
  background: linear-gradient(160deg, #107C10 0%, #0B6A0B 60%, #054B05 100%);
  box-shadow: 0 12px 28px rgba(16, 124, 16, 0.3);
}
.roulette-frame.is-done:hover:not(:disabled) {
  box-shadow: 0 16px 32px rgba(16, 124, 16, 0.36);
}
"""

_JS = """
export default function (component) {
  const { data, parentElement, setStateValue, setTriggerValue } = component;
  const root = parentElement.querySelector(".roulette-root");
  if (!root) return;

  const frame = root.querySelector("#roulette-btn");
  const nameEl = root.querySelector("#roulette-name");
  const hintEl = root.querySelector("#roulette-hint");
  const labelEl = root.querySelector(".roulette-label");
  if (!frame || !nameEl || !hintEl || !labelEl) return;

  const names = Array.isArray(data?.names) ? data.names.filter(Boolean) : [];
  const winner = data?.winner || "";
  const spinId = Number(data?.spinId ?? 0);
  const completedSpinId = Number(data?.completedSpinId ?? 0);
  const idleText = data?.idleText || "Pulsa aquí para seleccionar";
  const disabled = Boolean(data?.disabled);

  frame.disabled = disabled;

  frame.onclick = () => {
    if (disabled || root._spinning) return;
    setTriggerValue("select", Date.now());
  };

  const showIdle = () => {
    if (root._spinTimer) {
      clearTimeout(root._spinTimer);
      root._spinTimer = null;
    }
    root._spinning = false;
    frame.classList.remove("is-done");
    frame.classList.add("is-idle");
    nameEl.classList.remove("is-winner", "is-spinning");
    labelEl.textContent = disabled ? "Sin candidatos" : "Pulsa para elegir";
    nameEl.textContent = idleText;
    hintEl.textContent = disabled
      ? "No hay alumnos disponibles"
      : names.length
        ? names.length + " alumnos · pulsa el cuadro"
        : "Añade alumnos al grupo para empezar";
  };

  const showWinnerStatic = () => {
    if (root._spinTimer) {
      clearTimeout(root._spinTimer);
      root._spinTimer = null;
    }
    root._spinning = false;
    frame.classList.remove("is-idle");
    frame.classList.add("is-done");
    nameEl.classList.remove("is-spinning");
    nameEl.classList.add("is-winner");
    labelEl.textContent = "¡Elegido!";
    nameEl.textContent = winner;
    hintEl.textContent = disabled
      ? "Es el turno de " + winner
      : "Es el turno de " + winner + " · pulsa para otra vez";
  };

  if (!spinId || !winner) {
    showIdle();
    return;
  }

  if (spinId === completedSpinId) {
    showWinnerStatic();
    return;
  }

  if (root._spinTimer) {
    clearTimeout(root._spinTimer);
    root._spinTimer = null;
  }

  root._spinning = true;
  frame.classList.remove("is-done", "is-idle");
  nameEl.classList.remove("is-winner");
  nameEl.classList.add("is-spinning");
  labelEl.textContent = "Seleccionando…";
  hintEl.textContent = "";

  const pool = names.length ? names : [winner];
  const others = pool.filter((n) => n !== winner);
  const decoySource = others.length ? others : pool;
  const pick = () => decoySource[Math.floor(Math.random() * decoySource.length)];
  const sequence = [pick(), pick(), winner];

  let index = 0;
  const delays = [90, 140];
  const tick = () => {
    nameEl.textContent = sequence[index];
    if (index >= sequence.length - 1) {
      nameEl.classList.remove("is-spinning");
      nameEl.classList.add("is-winner");
      frame.classList.add("is-done");
      labelEl.textContent = "¡Elegido!";
      hintEl.textContent = "Es el turno de " + winner + " · pulsa para otra vez";
      root._spinning = false;
      setStateValue("completedSpinId", spinId);
      return;
    }
    const delay = delays[index] ?? 120;
    index += 1;
    root._spinTimer = setTimeout(tick, delay);
  };

  tick();
}
"""

_roulette = st.components.v2.component(
    "son_selector_roulette_btn",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def show_roulette(
    *,
    names: list[str],
    winner: str | None = None,
    spin_id: int = 0,
    enabled: bool = True,
    idle_text: str = "Pulsa aquí para seleccionar",
) -> bool:
    """Muestra el selector. Devuelve True si se ha pulsado el cuadro."""
    key = "son-selector-roulette"
    state = st.session_state.get(key, {}) or {}
    completed = state.get("completedSpinId", 0)

    result = _roulette(
        data={
            "names": names,
            "winner": winner or "",
            "spinId": spin_id,
            "completedSpinId": completed,
            "idleText": idle_text,
            "disabled": not enabled,
        },
        key=key,
        height="content",
        width="stretch",
        on_completedSpinId_change=lambda: None,
        on_select_change=lambda: None,
    )
    return getattr(result, "select", None) is not None
