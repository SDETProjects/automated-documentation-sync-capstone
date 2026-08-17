/**
 * RiskFlagMarker — accessible risk flag indicator component.
 *
 * Renders a warning icon + text label when a projected spend exceeds a budget.
 * Accessibility (NFR-3): uses role="alert" and aria-label so screen readers
 * announce the risk. The icon (⚠) is present alongside the text so color
 * is never the sole indicator.
 *
 * Design Review policy: this component contains NO threshold comparison logic.
 * It receives a pre-evaluated riskFlag object from the server and renders it.
 *
 * Usage:
 *   const marker = new RiskFlagMarker("risk-container");
 *   marker.show({ triggered: true, label: "Projected spend exceeds engineering budget" });
 *   marker.hide();
 */
class RiskFlagMarker {
  /**
   * @param {string} containerId - ID of the DOM element to render into.
   */
  constructor(containerId) {
    this._container = document.getElementById(containerId);
    if (!this._container) {
      throw new Error(`RiskFlagMarker: container '#${containerId}' not found`);
    }
    this._element = this._createElement();
    this._container.appendChild(this._element);
    this.hide();
  }

  _createElement() {
    const el = document.createElement("div");
    el.className = "risk-flag-marker";
    el.setAttribute("role", "alert");
    // aria-label is set dynamically in show(); initialise to empty.
    el.setAttribute("aria-label", "");
    el.innerHTML = `<span class="risk-flag-icon" aria-hidden="true">⚠</span>
                    <span class="risk-flag-label"></span>`;
    return el;
  }

  /**
   * Display the risk flag with the given label.
   * @param {{ triggered: boolean, label: string }} riskFlag
   */
  show(riskFlag) {
    if (!riskFlag || !riskFlag.triggered) {
      this.hide();
      return;
    }
    const label = riskFlag.label || "Risk: projected spend exceeds budget";
    this._element.querySelector(".risk-flag-label").textContent = label;
    this._element.setAttribute("aria-label", label);
    this._element.style.display = "";
  }

  /** Hide the risk flag marker. */
  hide() {
    this._element.style.display = "none";
    this._element.setAttribute("aria-label", "");
  }

  /** Whether the marker is currently visible. */
  get visible() {
    return this._element.style.display !== "none";
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { RiskFlagMarker };
} else {
  window.RiskFlagMarker = RiskFlagMarker;
}
