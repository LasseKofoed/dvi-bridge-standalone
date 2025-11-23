class LvHeatpumpCard extends HTMLElement {
  // Base path for images, regardless of where HACS installs the card
  static get imageBase() {
    return new URL("./dvi-lv/", import.meta.url).href;
  }

  setConfig(config) {
    if (!config.cv_mode || !config.vv_mode) {
      throw new Error("You must define at least 'cv_mode' and 'vv_mode' entities");
    }

    this._config = config;
    this._root = this.attachShadow({ mode: "open" });

    this._root.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .header {
          margin-bottom: 8px;
          font-size: 1.2em;
          font-weight: 600;
        }

        /* Diagram */
        .diagram {
          position: relative;
          width: 100%;
          max-width: 600px;
          margin: 0 auto 16px;
        }
        .diagram-base {
          width: 100%;
          display: block;
        }
        .diagram-element {
          position: absolute;
          transform: translate(-50%, -50%);
        }
        .diagram-label {
          position: absolute;
          transform: translate(-50%, -50%);
          font-size: 0.9em;
          color: rgb(8, 0, 0);
          font-weight: normal;
          white-space: nowrap;
          text-shadow: 0 0 3px rgba(255,255,255,0.7);
        }
        .diagram-icon {
          position: absolute;
          transform: translate(-50%, -50%);
        }
        .diagram-icon img {
          width: 100%;
          height: auto;
        }

        /* Mode bar + chips */
        .mode-bar {
          position: absolute;
          top: 4%;
          right: 3%;
          display: flex;
          flex-direction: row;
          gap: 6px;
          /*z-index: 120;*/
        }
        .mode-chip {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 2px 8px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.9);
          box-shadow: 0 0 4px rgba(0, 0, 0, 0.25);
          cursor: pointer;
        }
        .mode-chip ha-icon {
          --mdc-icon-size: 18px;
        }
        .small-mode-icon {
          --mdc-icon-size: 14px;
          opacity: 0.9;
        }
        .chip-label {
          font-size: 0.75em;
        }
        .chip-value {
          font-size: 0.75em;
          font-weight: 600;
        }
      </style>
      <ha-card>
        <div class="header">DVI LV Compact varmepumpe</div>
        <div class="diagram" id="diagram"></div>
      </ha-card>
    `;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._config) return;

    const cfg = this._config;
    const root = this._root;
    const diagram = root.getElementById("diagram");
    if (!diagram) return;

    const getState = (entityId) =>
      entityId && this._hass.states[entityId] ? this._hass.states[entityId].state : null;

    const getUnit = (entityId) =>
      entityId && this._hass.states[entityId]
        ? this._hass.states[entityId].attributes.unit_of_measurement || ""
        : "";

    const showUnit = cfg.show_temp_unit ?? false; // default: true

    /* --- read states --- */

    // Modes
    const cvMode = getState(cfg.cv_mode) ?? "unavailable";
    const vvMode = getState(cfg.vv_mode) ?? "unavailable";
    const cvNight = cfg.cv_night ? getState(cfg.cv_night) : null;
    const vvSchedule = cfg.vv_schedule ? getState(cfg.vv_schedule) : null;
    const auxHeating = cfg.aux_heating ? getState(cfg.aux_heating) : null;

    // Temps/energy
    const outdoor = cfg.outdoor_temp ? getState(cfg.outdoor_temp) : null;
    const curveTemp = cfg.curve_temp ? getState(cfg.curve_temp) : null;
    const tankCv = cfg.storage_tank_cv ? getState(cfg.storage_tank_cv) : null;
    const tankVv = cfg.storage_tank_vv ? getState(cfg.storage_tank_vv) : null;
    const power = cfg.em23_power ? getState(cfg.em23_power) : null;
    const energy = cfg.em23_energy ? getState(cfg.em23_energy) : null;

    // Diagram temps
    const evapTemp = cfg.evaporator_temp ? getState(cfg.evaporator_temp) : null;
    const hpTemp = cfg.hp_temp ? getState(cfg.hp_temp) : null;
    const lpTemp = cfg.lp_temp ? getState(cfg.lp_temp) : null;
    const cvForwardTemp = cfg.cv_forward_temp ? getState(cfg.cv_forward_temp) : null;
    const cvReturnTemp = cfg.cv_return_temp ? getState(cfg.cv_return_temp) : null;

    // Icons (binary sensors)
    const compState = cfg.comp_icon ? getState(cfg.comp_icon) : null;
    const cvPumpState = cfg.cv_pump_icon ? getState(cfg.cv_pump_icon) : null;
    const defrostState = cfg.defrost_icon ? getState(cfg.defrost_icon) : null;

    const onOpacity = (state) => (state === "on" ? 1 : 0.25);

    /* --- farver og små ikoner til mode-bar --- */

    const cvIconColor =
      cvMode === "Off" || cvMode === "unavailable"
        ? "var(--disabled-text-color)"
        : "var(--state-climate-heat-color, var(--accent-color))";

    const vvIconColor =
      vvMode === "Off" || vvMode === "unavailable"
        ? "var(--disabled-text-color)"
        : "var(--state-water-heater-heat-color, var(--accent-color))";

    const auxIconColor =
      auxHeating && auxHeating !== "Off"
        ? "var(--warning-color, #fdd835)"
        : "var(--disabled-text-color)";

    const cvNightIcon = (() => {
      switch (cvNight) {
        case "Timer":
          return "mdi:clock-outline";
        case "Constant day":
          return "mdi:weather-sunny";
        case "Constant night":
          return "mdi:weather-night";
        default:
          return null;
      }
    })();

    const vvScheduleIcon = (() => {
      switch (vvSchedule) {
        case "Timer":
          return "mdi:clock-outline";
        case "Constant on":
          return "mdi:toggle-switch";
        case "Constant off":
          return "mdi:toggle-switch-off-outline";
        default:
          return null;
      }
    })();

    const vvScheduleColor =
      vvSchedule && vvSchedule !== "Constant off"
        ? "var(--secondary-text-color)"
        : "var(--disabled-text-color)";

    // Popup-lister (kan være sat af auto-fill eller YAML)
    const infoEntities = Array.isArray(cfg.info_entities) ? cfg.info_entities : [];
    const cvEntities = Array.isArray(cfg.cv_entities) ? cfg.cv_entities : [];
    const vvEntities = Array.isArray(cfg.vv_entities) ? cfg.vv_entities : [];
    const auxEntities = Array.isArray(cfg.aux_entities) ? cfg.aux_entities : [];

    // Map mellem "keys" og entityId til history-popup
    const stateEntityMap = {
      outdoor: cfg.outdoor_temp,
      curve: cfg.curve_temp,
      tankCv: cfg.storage_tank_cv,
      tankVv: cfg.storage_tank_vv,
      evap: cfg.evaporator_temp,
      hp: cfg.hp_temp,
      lp: cfg.lp_temp,
      cvForward: cfg.cv_forward_temp,
      cvReturn: cfg.cv_return_temp,
    };

    const unitForKey = (key) => {
      if (!showUnit) return "";
      const eid = stateEntityMap[key];
      if (!eid) return "";
      const u = getUnit(eid);
      return u ? ` ${u}` : "";
    };

    // Map for binary / aux ikon-klik
    const iconEntityMap = {
      defrost: cfg.defrost_icon,
      comp: cfg.comp_icon,
      cvPump: cfg.cv_pump_icon,
      aux: cfg.aux_heating, // klik på AUX-ikon åbner select-entity
    };

    /* --- build diagram --- */

    diagram.innerHTML = `
      <img src="${LvHeatpumpCard.imageBase}/dvi.gif" class="diagram-base" alt="LV diagram" />

      ${
        outdoor !== null
          ? `<div class="diagram-label" data-key="outdoor" style="top:11%; left:13%;  z-index:5;">${outdoor}${unitForKey(
              "outdoor"
            )}</div>`
          : ""
      }

      <div class="diagram-label" style="top:18%; left:50%; z-index:5;">Kurvetemperatur</div>

      ${
        curveTemp !== null
          ? `<div class="diagram-label" data-key="curve" style="top:18%; left:68%; z-index:5;">${curveTemp}${unitForKey(
              "curve"
            )}</div>`
          : ""
      }

      ${
        evapTemp !== null
          ? `<div class="diagram-label" data-key="evap" style="top:77%; left:16%; z-index:5;">${evapTemp}${unitForKey(
              "evap"
            )}</div>`
          : ""
      }

      ${
        hpTemp !== null
          ? `<div class="diagram-label" data-key="hp" style="top:31%; left:43.5%; z-index:5;">${hpTemp}${unitForKey(
              "hp"
            )}</div>`
          : ""
      }

      ${
        lpTemp !== null
          ? `<div class="diagram-label" data-key="lp" style="top:31%; left:34%; z-index:5;">${lpTemp}${unitForKey(
              "lp"
            )}</div>`
          : ""
      }

      ${
        tankCv !== null
          ? `<div class="diagram-label" data-key="tankCv" style="top:72.5%; left:61%; z-index:5;">${tankCv}${unitForKey(
              "tankCv"
            )}</div>`
          : ""
      }

      ${
        tankVv !== null
          ? `<div class="diagram-label" data-key="tankVv" style="top:33%; left:80%; z-index:5;">${tankVv}${unitForKey(
              "tankVv"
            )}</div>`
          : ""
      }

      ${
        cvForwardTemp !== null
          ? `<div class="diagram-label" data-key="cvForward" style="top:79.2%; left:73%; z-index:5;">${cvForwardTemp}${unitForKey(
              "cvForward"
            )}</div>`
          : ""
      }

      ${
        cvReturnTemp !== null
          ? `<div class="diagram-label" data-key="cvReturn" style="top:94%; left:73%;z-index:5;">${cvReturnTemp}${unitForKey(
              "cvReturn"
            )}</div>`
          : ""
      }

      <!-- CV pump + flow gifs -->
      <div class="diagram-icon" data-icon-key="cvPump" style="top:79.3%; left:88.8%; width:21%; opacity:${onOpacity(
        cvPumpState
      )};">
        <img src="${LvHeatpumpCard.imageBase}CV_on.gif" alt="CV pump" />
      </div>
      <div class="diagram-icon" data-icon-key="cvPump" style="top:89.95%; left:71.7%; width:14.2%; opacity:${onOpacity(
        cvPumpState
      )};">
        <img src="${LvHeatpumpCard.imageBase}CVflow_on.gif" alt="CV flow" />
      </div>

      <!-- Compressor / HP gifs -->
      <div class="diagram-icon" data-icon-key="comp" style="top:63.75%; left:18.4%; width:33.9%; opacity:${compState === "on" ? 1 : 0.0};">
        <img src="${LvHeatpumpCard.imageBase}HP_on.gif" alt="HP on" />
      </div>
      <div class="diagram-icon" data-icon-key="comp" style="top:63.75%; left:46%; width:21.3%; opacity:${compState === "on" ? 1 : 0.0};">
        <img src="${LvHeatpumpCard.imageBase}COMP_on.gif" alt="Compressor on" />
      </div>

      <!-- Defrost icon (snowflake) -->
      ${
        defrostState !== null
          ? `<ha-icon
               class="diagram-element"
               data-icon-key="defrost"
               style="top:85%; left:15%; color:${
                 defrostState === "on" ? "orange" : "var(--disabled-text-color)"
               };"
               icon="mdi:snowflake-melt">
             </ha-icon>`
          : ""
      }

      <!-- AUX icon on buffer tank (only when AUX != Off) -->
      ${
        auxHeating && auxHeating !== "Off"
          ? `<ha-icon
               class="diagram-element"
               data-icon-key="aux"
               style="top:70%; left:69%; color:var(--warning-color, #fdd835);"
               icon="mdi:lightning-bolt-outline">
             </ha-icon>`
          : ""
      }

      <!-- Mode bar: Info / CV / VV / AUX -->
      <div class="mode-bar">
        ${
          infoEntities.length
            ? `<div class="mode-chip popup-chip" data-popup="info">
                 <ha-icon icon="mdi:information-slab-circle"></ha-icon>
                 <span class="chip-label">Info</span>
                 ${
                   power !== null
                     ? `<span class="chip-value">${power} kW</span>`
                     : ""
                 }
               </div>`
            : ""
        }

        ${
          cvEntities.length
            ? `<div class="mode-chip popup-chip" data-popup="cv">
                 <ha-icon icon="mdi:radiator" style="color:${cvIconColor};"></ha-icon>
                 ${
                   cvNightIcon
                     ? `<ha-icon class="small-mode-icon"
                               icon="${cvNightIcon}"
                               style="color:${cvIconColor};"></ha-icon>`
                     : ""
                 }
                 <span class="chip-label">CV</span>
               </div>`
            : ""
        }

        ${
          vvEntities.length
            ? `<div class="mode-chip popup-chip" data-popup="vv">
                 <ha-icon icon="mdi:shower-head" style="color:${vvIconColor};"></ha-icon>
                 ${
                   vvScheduleIcon
                     ? `<ha-icon class="small-mode-icon"
                               icon="${vvScheduleIcon}"
                               style="color:${vvScheduleColor};"></ha-icon>`
                     : ""
                 }
                 <span class="chip-label">VV</span>
               </div>`
            : ""
        }

        ${
          auxEntities.length
            ? `<div class="mode-chip popup-chip" data-popup="aux">
                 <ha-icon icon="mdi:lightning-bolt-outline" style="color:${auxIconColor};"></ha-icon>
                 <span class="chip-label">AUX</span>
               </div>`
            : ""
        }
      </div>
    `;

    /* --- native HA history popup på labels --- */
    Object.entries(stateEntityMap).forEach(([key, entityId]) => {
      if (!entityId) return;
      const el = diagram.querySelector(`.diagram-label[data-key="${key}"]`);
      if (!el) return;

      el.style.cursor = "pointer";
      el.addEventListener("click", () => {
        const ev = new CustomEvent("hass-more-info", {
          detail: { entityId },
          bubbles: true,
          composed: true,
        });
        this.dispatchEvent(ev);
      });
    });

    /* --- native HA more-info popup på binary/AUX ikoner --- */
    Object.entries(iconEntityMap).forEach(([key, entityId]) => {
      if (!entityId) return;
      diagram.querySelectorAll(`[data-icon-key="${key}"]`).forEach((el) => {
        el.style.cursor = "pointer";
        el.addEventListener("click", () => {
          const ev = new CustomEvent("hass-more-info", {
            detail: { entityId },
            bubbles: true,
            composed: true,
          });
          this.dispatchEvent(ev);
        });
      });
    });

    /* --- browser_mod popups for chips --- */

    const firePopup = (type) => {
      if (!this._hass) return;

      let title;
      let entities = [];

      if (type === "info") {
        title = "Information";
        entities = infoEntities;
      } else if (type === "cv") {
        title = "Centralvarme";
        entities = cvEntities;
      } else if (type === "vv") {
        title = "Varmtvandstemperatur";
        entities = vvEntities;
      } else if (type === "aux") {
        title = "El-patron / AUX";
        entities = auxEntities;
      }

      if (!entities || entities.length === 0) return;

      this._hass.callService("browser_mod", "popup", {
        title,
        content: {
          type: "entities",
          entities,
        },
      });
    };

    diagram.querySelectorAll(".popup-chip").forEach((el) => {
      const type = el.getAttribute("data-popup");
      if (!type) return;
      el.addEventListener("click", () => firePopup(type));
    });
  }

  static getConfigElement() {
    return document.createElement("lv-heatpump-card-editor");
  }

  static getStubConfig(hass, entities) {
    // Default config used when you add the card from the UI
    return {
      show_temp_unit: false,
    };
  }
}

/* ------------------ EDITOR ------------------ */

class LvHeatpumpCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
    this._formBasic = null;
    this._formAdvanced = null;
    this._basicSchema = [];
    this._advancedSchema = [];
  }

  setConfig(config) {
    this._config = config || {};
    this._buildSchema();
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._formBasic) this._formBasic.hass = hass;
    if (this._formAdvanced) this._formAdvanced.hass = hass;
  }

  _buildSchema() {
    // Basic: kun device
    this._basicSchema = [
      {
        name: "device_id",
        label: "DVI X MQTT device",
        selector: {
          device: {
            integration: "mqtt",
          },
        },
      },
      // --- Settings ---
      {
        name: "show_temp_unit",
        label: "Show temperature unit (°C/°F)",
        selector: { boolean: {} },
      },
    ];

    // Advanced: core entities og sensorer (popup-listerne er ikke længere bruger-opsætning)
    this._advancedSchema = [
      // --- Core modes / selects ---
      {
        name: "cv_mode",
        label: "Central heating mode (cv_mode)",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "vv_mode",
        label: "Hot water mode (vv_mode)",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "cv_night",
        label: "CV night mode (cv_night)",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "vv_schedule",
        label: "VV schedule (vv_schedule)",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "aux_heating",
        label: "Aux / electric heater mode (aux_heating)",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "vv_setpoint",
        label: "Warm water setpoint (vv_setpoint)",
        selector: { entity: { domain: ["number", "input_number"] } },
      },

      // --- Temperatures / sensors ---
      {
        name: "outdoor_temp",
        label: "Outdoor temperature (outdoor_temp)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "curve_temp",
        label: "Curve temperature (curve_temp)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "storage_tank_cv",
        label: "Storage tank CV (storage_tank_cv)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "storage_tank_vv",
        label: "Storage tank VV (storage_tank_vv)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "evaporator_temp",
        label: "Evaporator temperature (evaporator_temp)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "hp_temp",
        label: "High pressure temperature (hp_temp)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "lp_temp",
        label: "Low pressure temperature (lp_temp)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "cv_forward_temp",
        label: "CV forward temperature (cv_forward_temp)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "cv_return_temp",
        label: "CV return temperature (cv_return_temp)",
        selector: { entity: { domain: "sensor" } },
      },

      // --- Energy / power ---
      {
        name: "em23_power",
        label: "EM23 power (em23_power)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "em23_energy",
        label: "EM23 energy (em23_energy)",
        selector: { entity: { domain: "sensor" } },
      },

      // --- Binary sensor icons / states ---
      {
        name: "comp_icon",
        label: "Compressor state (comp_icon)",
        selector: { entity: { domain: "binary_sensor" } },
      },
      {
        name: "cv_pump_icon",
        label: "CV pump state (cv_pump_icon)",
        selector: { entity: { domain: "binary_sensor" } },
      },
      {
        name: "defrost_icon",
        label: "Defrost state (defrost_icon)",
        selector: { entity: { domain: "binary_sensor" } },
      },      
    ];
  }

  _render() {
    if (!this._hass) return;

    this.innerHTML = "";

    const container = document.createElement("div");
    container.className = "card-config";

    // --- BASIC FORM (device) ---
    const basicForm = document.createElement("ha-form");
    basicForm.schema = this._basicSchema;
    basicForm.data = this._config;
    basicForm.hass = this._hass;

    basicForm.addEventListener("value-changed", (ev) => {
      const oldDevice = this._config.device_id;
      this._config = { ...this._config, ...ev.detail.value };
      const newDevice = this._config.device_id;

      if (newDevice && newDevice !== oldDevice) {
        // hver gang device skifter, auto-map alle felter
        this._autoFillFromDevice(newDevice);
      }

      this._dispatchConfigChanged();
    });

    container.appendChild(basicForm);
    this._formBasic = basicForm;

    // --- ADVANCED (fold-ud) ---
    const details = document.createElement("details");
    details.style.marginTop = "16px";

    const summary = document.createElement("summary");
    summary.textContent = "Advanced entity mapping";
    summary.style.cursor = "pointer";
    details.appendChild(summary);

    const advWrapper = document.createElement("div");
    advWrapper.style.marginTop = "8px";

    const advForm = document.createElement("ha-form");
    advForm.schema = this._advancedSchema;
    advForm.data = this._config;
    advForm.hass = this._hass;

    advForm.addEventListener("value-changed", (ev) => {
      this._config = { ...this._config, ...ev.detail.value };
      this._dispatchConfigChanged();
    });

    advWrapper.appendChild(advForm);

    // Reset / auto-fill knap
    const resetBtn = document.createElement("button");
    resetBtn.type = "button";
    resetBtn.textContent = "Auto-fill from device";
    resetBtn.style.marginTop = "8px";
    resetBtn.addEventListener("click", () => {
      if (!this._config.device_id) return;
      this._autoFillFromDevice(this._config.device_id);
      this._dispatchConfigChanged();
    });

    advWrapper.appendChild(resetBtn);

    details.appendChild(advWrapper);
    container.appendChild(details);

    this.appendChild(container);

    this._formAdvanced = advForm;
  }

  _autoFillFromDevice(deviceId) {
    if (!this._hass || !this._hass.entities) return;

    // Find alle entities på den valgte device
    const entityIds = Object.keys(this._hass.states).filter((eid) => {
      const reg = this._hass.entities[eid];
      return reg && reg.device_id === deviceId;
    });

    const find = (domain, suffix) =>
      entityIds.find(
        (eid) =>
          eid.startsWith(domain + ".") &&
          (suffix.startsWith("_")
            ? eid.endsWith(suffix)
            : eid.endsWith("_" + suffix))
      );

    const patch = {
      // Core
      cv_mode: find("select", "cv_mode"),
      vv_mode: find("select", "vv_mode"),
      cv_night: find("select", "cv_night"),
      vv_schedule: find("select", "vv_schedule"),
      aux_heating: find("select", "aux_heating"),
      vv_setpoint: find("number", "vv_setpoint") || find("input_number", "vv_setpoint"),

      // Temps
      outdoor_temp: find("sensor", "outdoor"),
      curve_temp: find("sensor", "curve_temp"),
      storage_tank_cv: find("sensor", "storage_tank_cv"),
      storage_tank_vv: find("sensor", "storage_tank_vv"),
      evaporator_temp: find("sensor", "evaporator"),
      hp_temp: find("sensor", "compressor_hp"),
      lp_temp: find("sensor", "compressor_lp"),
      cv_forward_temp: find("sensor", "cv_forward"),
      cv_return_temp: find("sensor", "cv_return"),

      // Energy
      em23_power: find("sensor", "em23_power"),
      em23_energy: find("sensor", "em23_energy"),

      // Binary
      comp_icon: find("binary_sensor", "soft_starter_compressor"),
      cv_pump_icon: find("binary_sensor", "circ_pump_cv"),
      defrost_icon: find("binary_sensor", "4_way_valve_defrost"),
    };

    // Popup-lister – bygges helt forfra når vi auto-filler (men er ikke redigerbare i UI)
    const info_entities = [
      patch.em23_energy,
      patch.em23_power,
      entityIds.find((e) => e.endsWith("_comp_hours")),
      entityIds.find((e) => e.endsWith("_vv_hours")),
      entityIds.find((e) => e.endsWith("_heating_hours")),
    ].filter(Boolean);

    const cv_entities = [
      patch.cv_mode,
      entityIds.find((e) => e.startsWith("number.") && e.endsWith("_cv_curve")),
      patch.aux_heating,
      patch.cv_night,
    ].filter(Boolean);

    const vv_entities = [
      patch.vv_setpoint,
      patch.vv_mode,
      patch.vv_schedule,
    ].filter(Boolean);

    const aux_entities = [
      patch.aux_heating,
      entityIds.find((e) => e.startsWith("sensor.") && e.endsWith("_heating_hours")),
    ].filter(Boolean);

    this._config = {
      ...this._config,
      ...patch,
      info_entities,
      cv_entities,
      vv_entities,
      aux_entities,
    };

    // Re-render så advanced felter opdateres
    this._render();
  }

  _dispatchConfigChanged() {
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: this._config },
        bubbles: true,
        composed: true,
      })
    );
  }
}

customElements.define("lv-heatpump-card-editor", LvHeatpumpCardEditor);

// Register card in the Lovelace card picker
window.customCards = window.customCards || [];
window.customCards.push({
  type: "lv-heatpump-card",
  name: "DVI LV Heatpump Card",
  description: "Visual overview and control panel for a DVI LV heatpump.",
  preview: true, // gør at det dukker op under "Custom cards"
  documentationURL: "https://github.com/ruteclrp/dvi-bridge-standalone",
});

customElements.define("lv-heatpump-card", LvHeatpumpCard);
