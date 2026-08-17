/**
 * ViewToggleController — overall / per-category view toggle (FR-3, NFR-3).
 *
 * Renders two <button> elements ("Overall" and "By Category") and a
 * <select> for category selection.  Native <button> and <select> elements
 * provide keyboard accessibility out of the box (tab, Enter, Space, arrow
 * keys).
 *
 * The onViewChanged callback is invoked whenever the view selection changes:
 *   onViewChanged('overall', null)
 *   onViewChanged('category', 'engineering')
 *
 * Usage:
 *   const toggle = new ViewToggleController("toggle-container", (mode, cat) => {
 *     chart.load(currentPeriod, cat);
 *   });
 *   toggle.populateCategories([{ id: "eng", label: "Engineering" }]);
 */
class ViewToggleController {
  /**
   * @param {string} containerId - ID of the DOM element to render into.
   * @param {function(string, string|null): void} onViewChanged - Callback
   *   invoked with (mode, categoryId) on each view change.
   */
  constructor(containerId, onViewChanged) {
    this._container = document.getElementById(containerId);
    if (!this._container) {
      throw new Error(`ViewToggleController: container '#${containerId}' not found`);
    }
    this._onViewChanged = onViewChanged;
    this._mode = "overall";
    this._categoryId = null;
    this._render();
    // Fire initial callback so the chart loads on page load.
    this._notify();
  }

  _render() {
    this._container.innerHTML = `
      <div class="view-toggle" role="group" aria-label="View selection">
        <button id="btn-overall"   class="toggle-btn active"  type="button">Overall</button>
        <button id="btn-category"  class="toggle-btn"         type="button">By Category</button>
      </div>
      <div id="category-selector" style="display:none; margin-top:8px;">
        <label for="cat-select">Category:</label>
        <select id="cat-select" aria-label="Select category"></select>
      </div>`;

    this._btnOverall  = this._container.querySelector("#btn-overall");
    this._btnCategory = this._container.querySelector("#btn-category");
    this._catSelector = this._container.querySelector("#category-selector");
    this._catSelect   = this._container.querySelector("#cat-select");

    this._btnOverall.addEventListener("click", () => this._selectOverall());
    this._btnCategory.addEventListener("click", () => this._selectCategory());
    this._catSelect.addEventListener("change", () => {
      this._categoryId = this._catSelect.value || null;
      this._notify();
    });
  }

  _selectOverall() {
    this._mode = "overall";
    this._categoryId = null;
    this._btnOverall.classList.add("active");
    this._btnCategory.classList.remove("active");
    this._catSelector.style.display = "none";
    this._notify();
  }

  _selectCategory() {
    this._mode = "category";
    this._btnCategory.classList.add("active");
    this._btnOverall.classList.remove("active");
    this._catSelector.style.display = "";
    this._categoryId = this._catSelect.value || null;
    this._notify();
  }

  _notify() {
    if (typeof this._onViewChanged === "function") {
      this._onViewChanged(this._mode, this._categoryId);
    }
  }

  /**
   * Populate the category <select> from the budgets API response.
   * @param {Array<{id: string, label: string}>} categories
   */
  populateCategories(categories) {
    this._catSelect.innerHTML = `<option value="">-- select --</option>` +
      categories.map(c => `<option value="${c.id}">${c.label}</option>`).join("");
  }

  /** Current mode: 'overall' or 'category'. */
  get mode() { return this._mode; }

  /** Current selected category ID, or null for overall. */
  get categoryId() { return this._categoryId; }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { ViewToggleController };
} else {
  window.ViewToggleController = ViewToggleController;
}
