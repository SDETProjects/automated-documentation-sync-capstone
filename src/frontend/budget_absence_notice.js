/**
 * BudgetAbsenceNotice — informational notice shown when no budgets are configured.
 *
 * Implements FR-4: when GET /api/spend/budgets returns no budgets, this notice
 * explains to the user that budgets must be configured to enable risk flags.
 *
 * Contains no conditional logic beyond show/hide. All budget-presence
 * decisions are made by ForecastChart based on the API response.
 *
 * Usage:
 *   const notice = new BudgetAbsenceNotice("notice-container");
 *   notice.show();   // called by ForecastChart when budgets API returns empty
 *   notice.hide();   // called when budgets are present
 */
class BudgetAbsenceNotice {
  /**
   * @param {string} containerId - ID of the DOM element to render into.
   */
  constructor(containerId) {
    this._container = document.getElementById(containerId);
    if (!this._container) {
      throw new Error(`BudgetAbsenceNotice: container '#${containerId}' not found`);
    }
    this._element = this._createElement();
    this._container.appendChild(this._element);
    this.hide();
  }

  _createElement() {
    const el = document.createElement("p");
    el.className = "budget-absence-notice";
    el.setAttribute("role", "status");
    el.textContent = "Configure budgets to enable risk flags.";
    return el;
  }

  /** Show the notice. */
  show() {
    this._element.style.display = "";
  }

  /** Hide the notice. */
  hide() {
    this._element.style.display = "none";
  }

  /** Whether the notice is currently visible. */
  get visible() {
    return this._element.style.display !== "none";
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { BudgetAbsenceNotice };
} else {
  window.BudgetAbsenceNotice = BudgetAbsenceNotice;
}
