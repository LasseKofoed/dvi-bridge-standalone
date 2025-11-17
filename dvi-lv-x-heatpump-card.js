class Lv12HeatpumpCard extends HTMLElement {
  // Base path for images, regardless of where HACS installs the card
   static get imageBase() {
     return new URL("./dvi-lv-x/", import.meta.url).href;
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
 
         /* Info sections */
         .grid {
           display: grid;
           grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
           gap: 8px 16px;
           align-items: start;
         }
         .block-title {
           font-weight: 600;
           margin-bottom: 4px;
         }
         .item-label {
           font-weight: 500;
         }
         .item-value {
           font-size: 1.05em;
           margin-bottom: 4px;
         }
         .small {
           font-size: 0.9em;
           color: var(--secondary-text-color);
         }
         button {
           padding: 2px 8px;
           border-radius: 4px;
           border: none;
           cursor: pointer;
           margin-right: 4px;
         }
       </style>
       <ha-card>
         <div class="header">DVI LV12 Compact varmepumpe</div>
         <div class="diagram" id="diagram"></div>
         <div class="grid" id="grid"></div>
       </ha-card>
     `;
   }
 
   set hass(hass) {
     this._hass = hass;
     if (!this._config) return;
 
     const cfg = this._config;
     const root = this._root;
     const diagram = root.getElementById("diagram");
     const grid = root.getElementById("grid");
     if (!diagram || !grid) return;
 
     const getState = (entityId) =>
       entityId && this._hass.states[entityId] ? this._hass.states[entityId].state : null;
 
     const getDomain = (entityId) =>
       entityId && entityId.includes(".") ? entityId.split(".")[0] : null;
 
     /* --- read states --- */
 
     // Modes/setpoints
     const cvMode = getState(cfg.cv_mode) ?? "unavailable";
     const vvMode = getState(cfg.vv_mode) ?? "unavailable";
     const cvNight = cfg.cv_night ? getState(cfg.cv_night) : null;
     const vvSchedule = cfg.vv_schedule ? getState(cfg.vv_schedule) : null;
     const auxHeating = cfg.aux_heating ? getState(cfg.aux_heating) : null;
     const vvSetpoint = cfg.vv_setpoint ? getState(cfg.vv_setpoint) : null;
 
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
 
     /* --- build diagram --- */
 
     diagram.innerHTML = `
       <img src="${Lv12HeatpumpCard.imageBase}/dvi.gif" class="diagram-base" alt="LV12 diagram" />
 
       ${
         outdoor !== null
           ? `<div class="diagram-label" style="top:13%; left:13%;  z-index:100;">${outdoor} °C</div>`
           : ""
       }
 
       <div class="diagram-label" style="top:13%; left:48%; z-index:100;">kurvetemperatur</div>
 
       ${
         curveTemp !== null
           ? `<div class="diagram-label" style="top:13%; left:68%; z-index:100;">${curveTemp} °C</div>`
           : ""
       }
 
       ${
         evapTemp !== null
           ? `<div class="diagram-label" style="top:77%; left:16%; z-index:100;">${evapTemp} °C</div>`
           : ""
       }
 
       ${
         hpTemp !== null
           ? `<div class="diagram-label" style="top:31%; left:43.5%; z-index:100;">${hpTemp} °C</div>`
           : ""
       }
 
       ${
         lpTemp !== null
           ? `<div class="diagram-label" style="top:31%; left:34%; z-index:100;">${lpTemp} °C</div>`
           : ""
       }
 
       ${
         tankCv !== null
           ? `<div class="diagram-label" style="top:72.5%; left:61%; z-index:100;">${tankCv} °C</div>`
           : ""
       }
 
       ${
         tankVv !== null
           ? `<div class="diagram-label" style="top:33%; left:85%; z-index:100;">${tankVv} °C</div>`
           : ""
       }
 
       ${
         cvForwardTemp !== null
           ? `<div class="diagram-label" style="top:77.4%; left:75%; z-index:100;">${cvForwardTemp} °C</div>`
           : ""
       }
 
       ${
         cvReturnTemp !== null
           ? `<div class="diagram-label" style="top:96%; left:75%;z-index:100;">${cvReturnTemp} °C</div>`
           : ""
       }
 
       <!-- CV pump + flow gifs -->
       <div class="diagram-icon" style="top:78%; left:89%; width:21%; opacity:${onOpacity(
         cvPumpState
       )};">
         <img src="${Lv12HeatpumpCard.imageBase}CV_on.gif" alt="CV pump" />
       </div>
       <div class="diagram-icon" style="top:89.9%; left:71.8%; width:14.2%; opacity:${onOpacity(
         cvPumpState
       )};">
         <img src="${Lv12HeatpumpCard.imageBase}CVflow_on.gif" alt="CV flow" />
       </div>
 
       <!-- Compressor / HP gifs -->
       <div class="diagram-icon" style="top:62.7%; left:18.4%; width:33.9%; opacity:${compState === "on" ? 1 : 0.0};">
         <img src="${Lv12HeatpumpCard.imageBase}HP_on.gif" alt="HP on" />
       </div>
       <div class="diagram-icon" style="top:62.75%; left:46%; width:21.3%; opacity:${compState === "on" ? 1 : 0.0};">
         <img src="${Lv12HeatpumpCard.imageBase}COMP_on.gif" alt="Compressor on" />
       </div>
 
       <!-- Defrost icon (snowflake) -->
       ${
         defrostState !== null
           ? `<ha-icon
                class="diagram-element"
                style="top:85%; left:15%; color:${
                  defrostState === "on" ? "orange" : "var(--disabled-text-color)"
                };"
                icon="mdi:snowflake-melt">
              </ha-icon>`
           : ""
       }
 
       <!-- Mode bar: Info / CV / VV / AUX -->
       <div class="mode-bar">
         ${
           cfg.info_entities && cfg.info_entities.length
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
           cfg.cv_entities && cfg.cv_entities.length
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
           cfg.vv_entities && cfg.vv_entities.length
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
           cfg.aux_entities && cfg.aux_entities.length
             ? `<div class="mode-chip popup-chip" data-popup="aux">
                  <ha-icon icon="mdi:lightning-bolt-outline" style="color:${auxIconColor};"></ha-icon>
                  <span class="chip-label">AUX</span>
                </div>`
             : ""
         }
       </div>
     `;
 
     /* --- browser_mod popups for chips --- */
 
     const firePopup = (type) => {
       if (!this._hass) return;
 
       let title;
       let entities = [];
 
       if (type === "info") {
         title = "Information";
         entities = cfg.info_entities || [];
       } else if (type === "cv") {
         title = "Centralvarme";
         entities = cfg.cv_entities || [];
       } else if (type === "vv") {
         title = "Varmtvandstemperatur";
         entities = cfg.vv_entities || [];
       } else if (type === "aux") {
         title = "El-patron / AUX";
         entities = cfg.aux_entities || [];
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
 
     /* --- build info grid --- */
 
     grid.innerHTML = `
       <div>
         <div class="block-title">Modes</div>
 
         <div class="item-label">CV mode</div>
         <div class="item-value">${cvMode}</div>
         <div class="small">
           <button id="cv_on">On</button>
           <button id="cv_off">Off</button>
         </div>
 
         <div class="item-label" style="margin-top:8px;">VV mode</div>
         <div class="item-value">${vvMode}</div>
         <div class="small">
           <button id="vv_on">On</button>
           <button id="vv_off">Off</button>
         </div>
 
         ${
           cvNight !== null
             ? `
         <div class="item-label" style="margin-top:8px;">CV night</div>
         <div class="item-value">${cvNight}</div>
         <div class="small">
           <button id="cv_night_timer">Timer</button>
           <button id="cv_night_day">Constant day</button>
           <button id="cv_night_night">Constant night</button>
         </div>`
             : ""
         }
 
         ${
           auxHeating !== null
             ? `
         <div class="item-label" style="margin-top:8px;">Aux heating</div>
         <div class="item-value">${auxHeating}</div>
         <div class="small">
           <button id="aux_off">Off</button>
           <button id="aux_auto">Automatic</button>
           <button id="aux_on">On</button>
         </div>`
             : ""
         }
       </div>
 
       <div>
         <div class="block-title">Temperatures</div>
 
         ${
           outdoor !== null
             ? `
         <div class="item-label">Outdoor</div>
         <div class="item-value">${outdoor} °C</div>`
             : ""
         }
 
         ${
           tankCv !== null
             ? `
         <div class="item-label" style="margin-top:8px;">Storage tank CV</div>
         <div class="item-value">${tankCv} °C</div>`
             : ""
         }
 
         ${
           tankVv !== null
             ? `
         <div class="item-label" style="margin-top:8px;">Storage tank VV</div>
         <div class="item-value">${tankVv} °C</div>`
             : ""
         }
 
         ${
           vvSetpoint !== null
             ? `
         <div class="item-label" style="margin-top:8px;">VV setpoint</div>
         <div class="item-value">${vvSetpoint} °C</div>
         <div class="small">
           <button id="vv_set_dec">-1</button>
           <button id="vv_set_inc">+1</button>
         </div>`
             : ""
         }
       </div>
 
       <div>
         <div class="block-title">Energy</div>
 
         ${
           power !== null
             ? `
         <div class="item-label">EM23 Power</div>
         <div class="item-value">${power} kW</div>`
             : ""
         }
 
         ${
           energy !== null
             ? `
         <div class="item-label" style="margin-top:8px;">EM23 Energy</div>
         <div class="item-value">${energy} kWh</div>`
             : ""
         }
       </div>
     `;
 
     /* --- bind buttons --- */
 
     const bindSelect = (id, entity, option) => {
       const el = root.getElementById(id);
       if (!el || !entity) return;
       el.onclick = () =>
         this._hass.callService("select", "select_option", {
           entity_id: entity,
           option,
         });
     };
 
     const bindNumberDelta = (id, entity, delta) => {
       const el = root.getElementById(id);
       if (!el || !entity) return;
       el.onclick = () => {
         const st = this._hass.states[entity];
         if (!st) return;
         const cur = Number(st.state);
         if (Number.isNaN(cur)) return;
         const value = cur + delta;
 
         const domain = getDomain(entity);
         const serviceDomain =
           domain === "input_number" ? "input_number" : "number";
 
         this._hass.callService(serviceDomain, "set_value", {
           entity_id: entity,
           value,
         });
       };
     };
 
     // CV/VV modes
     bindSelect("cv_on", cfg.cv_mode, "On");
     bindSelect("cv_off", cfg.cv_mode, "Off");
     bindSelect("vv_on", cfg.vv_mode, "On");
     bindSelect("vv_off", cfg.vv_mode, "Off");
 
     // CV night modes
     bindSelect("cv_night_timer", cfg.cv_night, "Timer");
     bindSelect("cv_night_day", cfg.cv_night, "Constant day");
     bindSelect("cv_night_night", cfg.cv_night, "Constant night");
 
     // Aux heating
     bindSelect("aux_off", cfg.aux_heating, "Off");
     bindSelect("aux_auto", cfg.aux_heating, "Automatic");
     bindSelect("aux_on", cfg.aux_heating, "On");
 
     // VV setpoint +/- 1°C
     bindNumberDelta("vv_set_dec", cfg.vv_setpoint, -1);
     bindNumberDelta("vv_set_inc", cfg.vv_setpoint, +1);
   }
 
   // static getConfigElement() {
   //   return document.createElement("hui-text-config-editor");
   // }
 
   static getConfigElement() {
     return document.createElement("lv12-heatpump-card-editor");
   }
 
     static getStubConfig(hass, entities) {
     // Default config used when you add the card from the UI
     return {
       type: "custom:lv12-heatpump-card",
 
       cv_mode: "select.dvi_lv12_cv_mode",
       vv_mode: "select.dvi_lv12_vv_mode",
       cv_night: "select.dvi_lv12_cv_night",
       vv_schedule: "select.dvi_lv12_vv_schedule",
       aux_heating: "select.dvi_lv12_aux_heating",
       vv_setpoint: "number.dvi_lv12_vv_setpoint",
 
       outdoor_temp: "sensor.dvi_lv12_outdoor",
       curve_temp: "sensor.dvi_lv12_curve_temp",
       storage_tank_cv: "sensor.dvi_lv12_storage_tank_cv",
       storage_tank_vv: "sensor.dvi_lv12_storage_tank_vv",
       evaporator_temp: "sensor.dvi_lv12_evaporator",
       hp_temp: "sensor.dvi_lv12_compressor_hp",
       lp_temp: "sensor.dvi_lv12_compressor_lp",
       cv_forward_temp: "sensor.dvi_lv12_cv_forward",
       cv_return_temp: "sensor.dvi_lv12_cv_return",
       em23_power: "sensor.dvi_lv12_em23_power",
       em23_energy: "sensor.dvi_lv12_em23_energy",
 
       comp_icon: "binary_sensor.dvi_lv12_soft_starter_compressor",
       cv_pump_icon: "binary_sensor.dvi_lv12_circ_pump_cv",
       defrost_icon: "binary_sensor.dvi_lv12_4_way_valve_defrost",
 
       info_entities: [
         "sensor.dvi_lv12_em23_energy",
         "sensor.dvi_lv12_comp_hours",
         "sensor.dvi_lv12_vv_hours",
         "sensor.dvi_lv12_heating_hours"
       ],
       cv_entities: [
         "select.dvi_lv12_cv_mode",
         "number.dvi_lv12_cv_curve",
         "select.dvi_lv12_aux_heating",
         "select.dvi_lv12_cv_night"
       ],
       vv_entities: [
         "number.dvi_lv12_vv_setpoint",
         "select.dvi_lv12_vv_mode",
         "select.dvi_lv12_vv_schedule"
       ],
       aux_entities: [
         "select.dvi_lv12_aux_heating",
         "sensor.dvi_lv12_heating_hours"
       ]
     };
   }
 
 }
 
 class Lv12HeatpumpCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._schema = [];
    this._hass = null;
    this._form = null;
  }

  setConfig(config) {
    this._config = config || {};
    this._buildSchema();
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) {
      this._form.hass = hass;
    }
  }

  _buildSchema() {
    if (this._schema && this._schema.length) return;

    this._schema = [
      // --- Core modes / selects ---
      {
        name: "cv_mode",
        label: "CV mode select entity",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "vv_mode",
        label: "VV mode select entity",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "cv_night",
        label: "CV night mode select entity",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "vv_schedule",
        label: "VV schedule select entity",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "aux_heating",
        label: "Aux heating select entity",
        selector: { entity: { domain: "select" } },
      },
      {
        name: "vv_setpoint",
        label: "VV setpoint number/input_number entity",
        selector: { entity: { domain: ["number", "input_number"] } },
      },

      // --- Temperatures / sensors ---
      {
        name: "outdoor_temp",
        label: "Outdoor temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "curve_temp",
        label: "Curve temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "storage_tank_cv",
        label: "Storage tank CV sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "storage_tank_vv",
        label: "Storage tank VV sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "evaporator_temp",
        label: "Evaporator temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "hp_temp",
        label: "High pressure temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "lp_temp",
        label: "Low pressure temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "cv_forward_temp",
        label: "CV forward temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "cv_return_temp",
        label: "CV return temperature sensor",
        selector: { entity: { domain: "sensor" } },
      },

      // --- Energy / power ---
      {
        name: "em23_power",
        label: "EM23 power sensor (kW)",
        selector: { entity: { domain: "sensor" } },
      },
      {
        name: "em23_energy",
        label: "EM23 energy sensor (kWh)",
        selector: { entity: { domain: "sensor" } },
      },

      // --- Binary sensor icons / states ---
      {
        name: "comp_icon",
        label: "Compressor state (binary_sensor)",
        selector: { entity: { domain: "binary_sensor" } },
      },
      {
        name: "cv_pump_icon",
        label: "CV pump state (binary_sensor)",
        selector: { entity: { domain: "binary_sensor" } },
      },
      {
        name: "defrost_icon",
        label: "Defrost state (binary_sensor)",
        selector: { entity: { domain: "binary_sensor" } },
      },

      // --- Popup entity lists ---
      {
        name: "info_entities",
        label: "Info popup entities",
        selector: {
          entity: {
            multiple: true,
          },
        },
      },
      {
        name: "cv_entities",
        label: "CV popup entities",
        selector: {
          entity: {
            multiple: true,
          },
        },
      },
      {
        name: "vv_entities",
        label: "VV popup entities",
        selector: {
          entity: {
            multiple: true,
          },
        },
      },
      {
        name: "aux_entities",
        label: "Aux popup entities",
        selector: {
          entity: {
            multiple: true,
          },
        },
      },
    ];
  }

  _render() {
    if (!this._hass) return;

    // Ryd tidligere indhold
    this.innerHTML = "";

    const container = document.createElement("div");
    container.className = "card-config";

    const form = document.createElement("ha-form");
    form.schema = this._schema;
    form.data = this._config;
    form.hass = this._hass;

    form.addEventListener("value-changed", (ev) => {
      // ha-form sender hele config i ev.detail.value
      this._config = ev.detail.value || {};
      this._dispatchConfigChanged();
    });

    container.appendChild(form);
    this.appendChild(container);

    this._form = form;
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
 
 customElements.define("lv12-heatpump-card-editor", Lv12HeatpumpCardEditor); 
 
 // Register card in the Lovelace card picker
 window.customCards = window.customCards || [];
 window.customCards.push({
   type: "lv12-heatpump-card",
   name: "DVI LV-X Heatpump Card",
   description: "Visual overview and control panel for a DVI LV-X heatpump.",
   preview: true,                 // gør at det dukker op under "Custom cards"
   documentationURL: "https://github.com/ruteclrp/dvi-bridge-standalone"
 });
 
 customElements.define("lv12-heatpump-card", Lv12HeatpumpCard);
 