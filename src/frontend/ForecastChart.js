/**
 * ForecastChart — forecast overlay chart component (FR-1, FR-2, FR-3, NFR-1).
 *
 * Renders actual spend (solid series) and projected month-end total (dashed
 * reference line) using uPlot loaded from CDN (~40 KB gzipped — bundle-size
 * decision per Design Review revision item 2).
 *
 * Delegates caching to PeriodCache (in-memory only — Design Review revision
 * item 3). Risk flag and budget-absence rendering are centralised here; child
 * components (RiskFlagMarker, BudgetAbsenceNotice) receive pre-resolved values
 * and contain no threshold logic themselves.
 *
 * Usage:
 *   const chart = new ForecastChart({
 *     chartContainerId: "chart",
 *     riskFlagContainerId: "risk-flag",
 *     noticeContainerId: "budget-notice",
 *     apiBaseUrl: "http://127.0.0.1:5050",
 *     apiKey: null,  // set if SPEND_API_KEY is configured
 *   });
 *   await chart.load("2026-08", null);
 */
class ForecastChart {
  /**
   * @param {object} opts
   * @param {string} opts.chartContainerId
   * @param {string} opts.riskFlagContainerId
   * @param {string} opts.noticeContainerId
   * @param {string} [opts.apiBaseUrl=""]
   * @param {string|null} [opts.apiKey=null]
   */
  constructor(opts) {
    this._chartContainer = document.getElementById(opts.chartContainerId);
    this._apiBaseUrl = opts.apiBaseUrl || "";
    this._apiKey = opts.apiKey || null;
    this._cache = new window.PeriodCache();
    this._marker = new window.RiskFlagMarker(opts.riskFlagContainerId);
    this._notice = new window.BudgetAbsenceNotice(opts.noticeContainerId);
    this._uplot = null;
  }

  /**
   * Load forecast data for a period and render the chart.
   * Uses PeriodCache to avoid redundant API calls on cache hit.
   *
   * @param {string} period - YYYY-MM
   * @param {string|null} category - Category ID, or null for overall view.
   */
  async load(period, category) {
    let data = this._cache.get(period, category);

    if (!data) {
      data = await this._fetchForecast(period, category);
      if (data) {
        this._cache.set(period, category, data);
      }
    }

    if (data) {
      this.render(data);
    }
  }

  /**
   * Render the chart with the given forecast API response.
   * Centralises the conditional render decision for RiskFlagMarker and
   * BudgetAbsenceNotice (no logic in child components themselves).
   *
   * @param {object} data - Response from GET /api/spend/forecast
   */
  render(data) {
    const dates   = data.actual_spend.map(r => new Date(r.date).getTime() / 1000);
    const amounts = data.actual_spend.map(r => r.amount);
    const lastDate = dates[dates.length - 1];

    // Projected month-end: horizontal reference line at projected_total value.
    const projectedLine = dates.map(() => data.projected_total);

    const uplotData = [dates, amounts, projectedLine];

    const uplotOpts = {
      width:  this._chartContainer.clientWidth || 800,
      height: 300,
      series: [
        {},
        {
          label:  "Actual Spend",
          stroke: "#2563eb",
          width:  2,
        },
        {
          label:  `Projected (${data.period})`,
          stroke: "#dc2626",
          width:  2,
          dash:   [6, 4],
        },
      ],
      axes: [
        { label: "Date" },
        { label: "Amount ($)" },
      ],
    };

    if (this._uplot) {
      this._uplot.destroy();
    }
    // uPlot must be loaded from CDN in index.html before ForecastChart.js.
    this._uplot = new uPlot(uplotOpts, uplotData, this._chartContainer);

    // Centralised conditional rendering (design review policy).
    if (data.risk_flag !== null && data.risk_flag !== undefined) {
      // Budget exists — show risk flag if triggered, hide notice.
      this._marker.show(data.risk_flag);
      this._notice.hide();
    } else {
      // No budget configured — hide risk flag, show absence notice.
      this._marker.hide();
      this._notice.show();
    }
  }

  /**
   * Invalidate the cache for the current period and reload.
   * Called by the "Refresh" button.
   * @param {string} period
   * @param {string|null} category
   */
  async refresh(period, category) {
    this._cache.invalidate(period);
    await this.load(period, category);
  }

  // ------------------------------------------------------------------
  // Private helpers
  // ------------------------------------------------------------------

  async _fetchForecast(period, category) {
    const params = new URLSearchParams({ period });
    if (category) params.set("category", category);

    const headers = { "Content-Type": "application/json" };
    if (this._apiKey) headers["X-API-Key"] = this._apiKey;

    try {
      const resp = await fetch(
        `${this._apiBaseUrl}/api/spend/forecast?${params}`,
        { headers }
      );
      if (!resp.ok) {
        console.error(`ForecastChart: API error ${resp.status}`);
        return null;
      }
      return await resp.json();
    } catch (err) {
      console.error("ForecastChart: fetch failed", err);
      return null;
    }
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { ForecastChart };
} else {
  window.ForecastChart = ForecastChart;
}
