export const HEAT_CURVE_DEFAULTS = {
	cv_curve: null,
	curve_set_minus12: null,
	curve_set_plus12: null,
	outdoor: null,
	curve_sensor: null,
	cv_min: null,
	cv_max: null,
};

const yTicksPlugin = {
	id: "forceYTicks",
	afterBuildTicks: (chart) => {
		const yScale = chart.scales.y;
		if (!yScale) return;
		const ticks = [];
		for (let v = 20; v <= 60; v += 10) ticks.push({ value: v });
		yScale.ticks = ticks;
		yScale._tickItems = ticks.map((t) => ({ value: t.value }));
	},
};

class HeatCurveCard extends HTMLElement {
	constructor() {
		super();
		this._entities = { ...HEAT_CURVE_DEFAULTS };
		this._title = "Kurvetemperatur";
		this._pendingHass = null;
		this._controlsCard = null;
	}

	async connectedCallback() {
		await this._ensureChartLib();
		this._renderSkeleton();
		this._ensureChart();
		if (this._pendingHass) {
			const pending = this._pendingHass;
			this._pendingHass = null;
			this.hass = pending;
		}
	}

	setConfig(config) {
		this.config = config || {};
		this._title = this.config.title || "Kurvetemperatur";
		if (config?.entities) {
			this._entities = {
				...HEAT_CURVE_DEFAULTS,
				...Object.fromEntries(
					Object.entries(config.entities).filter(([, value]) => !!value)
				),
			};
		}
		if (this.isConnected) {
			this._renderSkeleton();
			this._ensureChart(true);
		}
	}

	set hass(hass) {
		if (!this.isConnected) {
			this._pendingHass = hass;
			return;
		}
		this._hass = hass;

		const values = this._readValues();
		if (!values) return;

		this._updateChart(values);
		this._renderControls();
	}

	async _ensureChartLib() {
		if (!window.Chart) {
			await import("https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js");
		}
	}

	_renderSkeleton() {		
		const existingCard = this.querySelector("ha-card");
		if (!existingCard) {
			this.innerHTML = `
        
        <ha-card class="heat-curve-card" header="${this._title}">
          <div class="heat-curve-card__chart" data-role="chart">
            <canvas data-role="curveChart"></canvas>
          </div>
          <div class="heat-curve-card__controls" data-role="controls"></div>
        </ha-card>
      `;
		} else {
			existingCard.setAttribute("header", this._title);
		}
		this._canvas = this.querySelector('[data-role="curveChart"]');
		this._controls = this.querySelector('[data-role="controls"]');
	}

	_ensureChart(reset = false) {
		if (!this._canvas || !window.Chart) return;

		if (reset && this.chart) {
			this.chart.destroy();
			this.chart = null;
		}
		if (this.chart) return;

		const ctx = this._canvas.getContext("2d");
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
						pointRadius: 0,
					},
					{
						label: "Sensor Curve Temp",
						data: [],
						borderColor: "blue",
						pointBackgroundColor: "blue",
						showLine: false,
						pointRadius: 6,
					},
				],
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				animation: false,
				scales: {
					x: {
						title: { display: true, text: "Outdoor Temp (°C)" },
						min: -20,
						max: 32,
					},
					y: {
						title: { display: true, text: "CV Temp (°C)" },
						min: 10,
						max: 80,
						grid: { drawTicks: true },
						ticks: { callback: (v) => `${v}` },
					},
				},
				plugins: {
					legend: { display: true },
				},
			},
			plugins: [yTicksPlugin],
		});
	}

	_readValues() {
		if (!this._hass) return null;

		const readNumber = (key) => {
			const entityId = this._entities[key];
			if (!entityId) return NaN;
			const raw = this._hass.states[entityId]?.state;
			return raw === undefined ? NaN : parseFloat(raw);
		};

		const cvCurve = readNumber("cv_curve");
		const setPlus12 = readNumber("curve_set_plus12");
		const setMinus12 = readNumber("curve_set_minus12");
		const outdoorTemp = readNumber("outdoor");
		const curveTemp = readNumber("curve_sensor");
		const cvMax = readNumber("cv_max");
		const cvMin = readNumber("cv_min");

		if ([cvCurve, setPlus12, setMinus12, outdoorTemp, curveTemp].some((v) => Number.isNaN(v))) {
			return null;
		}

		return {
			cvCurve,
			setPlus12,
			setMinus12,
			outdoorTemp,
			curveTemp,
			cvMax: Number.isNaN(cvMax) ? undefined : cvMax,
			cvMin: Number.isNaN(cvMin) ? undefined : cvMin,
		};
	}

	_updateChart(values) {
		if (!this.chart) return;

		const temps = Array.from({ length: 53 }, (_, i) => i - 20);
		const shift = values.cvCurve - 10;
		const adjMinus12 = values.setMinus12 + shift;
		const adjPlus12 = values.setPlus12 + shift;
		const slope = (adjPlus12 - adjMinus12) / 24;
		const cvMin = Number.isFinite(values.cvMin) ? values.cvMin : 20;
		const cvMax = Number.isFinite(values.cvMax) ? values.cvMax : 55;

		const cvTemps = temps.map((t) => {
			const val = adjMinus12 + slope * (t + 12);
			return Math.max(cvMin, Math.min(cvMax, val));
		});

		this.chart.data.labels = temps;
		this.chart.data.datasets[0].data = cvTemps;

		const sensorData = new Array(temps.length).fill(null);
		const idx = temps.indexOf(Math.round(values.outdoorTemp));
		if (idx !== -1) sensorData[idx] = values.curveTemp;
		this.chart.data.datasets[1].data = sensorData;

		this.chart.update();
	}

	_renderControls() {
		if (!this._controls || !this._hass) return;

		const entities = [
			this._entities.cv_curve,
			this._entities.curve_set_minus12,
			this._entities.curve_set_plus12,
			this._entities.cv_min,
			this._entities.cv_max,
		].filter(Boolean);

		if (!entities.length) {
			this._controls.innerHTML = "";
			this._controlsCard = null;
			return;
		}

		if (!this._controlsCard) {
			this._controls.innerHTML = "";
			this._controlsCard = document.createElement("hui-entities-card");
			this._controls.appendChild(this._controlsCard);
		}

		this._controlsCard.setConfig({ entities });
		this._controlsCard.hass = this._hass;
	}
}

customElements.define("heat-curve-card", HeatCurveCard);
