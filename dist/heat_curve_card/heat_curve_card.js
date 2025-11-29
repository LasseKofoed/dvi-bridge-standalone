class HeatCurveCard extends HTMLElement {
  async connectedCallback() {
    // Load Chart.js if not already loaded
    if (!window.Chart) {
      await import("https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js");
    }

    this.innerHTML = `
      <ha-card header="Heat Pump Curve">
        <div id="chartWrap" style="width:100%; height:320px; padding:8px 8px 0 8px;">
          <canvas id="curveChart" style="width:100%; height:100%; display:block;"></canvas>
        </div>
        <div id="controls" style="display:flex; gap:10px; padding:10px;"></div>
      </ha-card>
    `;

    const ctx = this.querySelector("#curveChart");
    if (ctx && window.Chart) {
      // Plugin to force y-axis ticks at every 10°C (20, 30, 40, 50, 60)
      const yTicksPlugin = {
        id: "forceYTicks",
        afterBuildTicks: (chart) => {
          const yScale = chart.scales.y;
          if (!yScale) return;
          const min = 10; // chart option min
          const max = 80; // chart option max
          // Build ticks at clean 10°C steps within [min, max]
          const ticks = [];
          for (let v = 20; v <= 60; v += 10) ticks.push({ value: v });
          // Include min if you want a tick at 15 as well:
          // ticks.unshift({ value: 15 });
          yScale.ticks = ticks;
          yScale._tickItems = ticks.map(t => ({ value: t.value }));
        }
      };

      this.chart = new Chart(ctx, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "CV Temp Curve",
              data: [],
              borderColor: "red",
              fill: false,
              pointRadius: 0
            },
            {
              label: "Sensor Curve Temp",
              data: [],
              borderColor: "blue",
              pointBackgroundColor: "blue",
              showLine: false,
              pointRadius: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false, // allow the container's height to take effect
          animation: false,
          scales: {
            x: {
              title: { display: true, text: "Outdoor Temp (°C)" },
              min: -20,
              max: 32, // adjust to 30 if you want −20…+30
              ticks: {
                // Optional: cleaner ticks every 2°C
                // stepSize: 2
              }
            },
            y: {
              title: { display: true, text: "CV Temp (°C)" },
              min: 10,
              max: 80,
              grid: {
                // Ensure grid lines draw for the forced ticks
                drawTicks: true
              },
              ticks: {
                // stepSize often gets ignored; plugin above guarantees exact ticks
                // stepSize: 10
                callback: (v) => `${v}`
              }
            }
          },
          plugins: {
            legend: { display: true }
          }
        },
        plugins: [yTicksPlugin]
      });
    }
  }

  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;

    const cvCurve = parseInt(hass.states["number.dvi_lv12_cv_curve"]?.state);
    const setPlus12 = parseFloat(hass.states["number.dvi_lv12_curve_set_12_2"]?.state);
    const setMinus12 = parseFloat(hass.states["number.dvi_lv12_curve_set_12"]?.state);
    const outdoorTemp = parseFloat(hass.states["sensor.dvi_lv12_outdoor"]?.state);
    const curveTemp = (hass.states["sensor.dvi_lv12_curve_temp"]?.state);
    const cvMax = parseFloat(hass.states["number.dvi_lv12_cv_max"]?.state);
    const cvMin = parseFloat(hass.states["number.dvi_lv12_cv_min"]?.state);

    if (!cvCurve || !setPlus12 || !setMinus12 || !outdoorTemp || !curveTemp) return;

    this._updateChart(cvCurve, setMinus12, setPlus12, outdoorTemp, curveTemp, cvMax, cvMin);
    this._renderControls(cvCurve, setPlus12, setMinus12);
  }

  _updateChart(cvCurve, setMinus12, setPlus12, outdoorTemp, curveTemp, cvMax, cvMin) {
    if (!this.chart) return;
    const shift = cvCurve - 10;
    const adjMinus12 = setMinus12 + shift;
    const adjPlus12 = setPlus12 + shift;

    // X labels: fixed −20 … +20 (change to +30 if desired)
    const temps = Array.from({ length: 53 }, (_, i) => i - 20);

    // Use the same slope everywhere, then clamp to cv_min=20, cv_max=55
    const slope = (adjPlus12 - adjMinus12) / 24;
    const cvTemps = temps.map(t => {
      const val = adjMinus12 + slope * (t + 12);
      return Math.max(cvMin, Math.min(cvMax, val));
    });

    this.chart.data.labels = temps;
    this.chart.data.datasets[0].data = cvTemps;

    // Sensor point: show a single point at the rounded outdoor temp
    const sensorData = new Array(temps.length).fill(null);
    const idx = temps.indexOf(Math.round(outdoorTemp));
    if (idx !== -1) sensorData[idx] = curveTemp;
    this.chart.data.datasets[1].data = sensorData;

    this.chart.update();
  }

  _renderControls() {
    const container = this.querySelector("#controls");
    if (!container || !this._hass) return;

    // Create a nested entities card
    const card = document.createElement("hui-entities-card");
    card.setConfig({
      entities: [
        "number.dvi_lv12_cv_curve",
        "number.dvi_lv12_curve_set_12",
        "number.dvi_lv12_curve_set_12_2",
        "number.dvi_lv12_cv_min",
        "number.dvi_lv12_cv_max"
      ]
    });
    card.hass = this._hass;

    container.innerHTML = "";
    container.appendChild(card);
  }
}
customElements.define("heat-curve-card", HeatCurveCard);
