const MODE_LABELS   = ['おまかせ', '手動', '節電', '花粉', 'のど/はだ', 'サーキュ'];
const AIRVOL_LABELS = ['自動', '弱', '標準', '高', '最高'];
const HUMD_LABELS   = ['無', '弱', '標準', '高'];

const STYLES = `
  :host { display: block; }

  ha-card {
    cursor: pointer;
    padding: 16px 20px;
    box-sizing: border-box;
  }

  .card-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .icon-wrap {
    width: 44px; height: 44px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: var(--primary-color);
    color: #fff;
    flex-shrink: 0;
    transition: background 0.2s;
  }
  .icon-wrap.off { background: var(--disabled-color, #9e9e9e); }

  .info { flex: 1; min-width: 0; }
  .info .name {
    font-size: 14px; font-weight: 500;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .info .status {
    font-size: 12px;
    color: var(--secondary-text-color);
    margin-top: 2px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }

  /* ---- overlay ---- */
  .overlay {
    display: none;
    position: fixed; inset: 0;
    background: rgba(0,0,0,.45);
    z-index: 9999;
    align-items: flex-end;
    justify-content: center;
    padding-bottom: env(safe-area-inset-bottom, 0);
  }
  .overlay.open { display: flex; }

  /* ---- bottom-sheet dialog ---- */
  .sheet {
    background: var(--card-background-color, #fff);
    border-radius: 20px 20px 0 0;
    padding: 0 20px 24px;
    width: 100%; max-width: 480px;
    box-shadow: 0 -4px 24px rgba(0,0,0,.18);
    animation: slide-up .22s ease;
  }
  @keyframes slide-up {
    from { transform: translateY(60px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }

  .sheet-handle {
    width: 36px; height: 4px;
    background: var(--divider-color, #ddd);
    border-radius: 2px;
    margin: 12px auto 16px;
  }

  .sheet-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
  }
  .sheet-title { font-size: 17px; font-weight: 600; }
  .close-btn {
    background: var(--secondary-background-color, #f0f0f0);
    border: none; border-radius: 50%;
    width: 28px; height: 28px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 14px;
    color: var(--secondary-text-color);
  }

  /* power row */
  .power-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 18px;
    border-bottom: 1px solid var(--divider-color, #eee);
    margin-bottom: 18px;
  }
  .power-label { font-size: 15px; font-weight: 500; }
  .toggle {
    position: relative; width: 48px; height: 28px;
  }
  .toggle input { opacity: 0; width: 0; height: 0; }
  .toggle-track {
    position: absolute; inset: 0;
    border-radius: 14px;
    background: var(--disabled-color, #ccc);
    transition: background .2s;
    cursor: pointer;
  }
  .toggle-track.on { background: var(--primary-color); }
  .toggle-thumb {
    position: absolute;
    top: 3px; left: 3px;
    width: 22px; height: 22px;
    border-radius: 50%;
    background: #fff;
    transition: transform .2s;
    pointer-events: none;
    box-shadow: 0 1px 4px rgba(0,0,0,.25);
  }
  .toggle-track.on .toggle-thumb { transform: translateX(20px); }

  /* sections */
  .section { margin-bottom: 16px; }
  .section-label {
    font-size: 11px; font-weight: 600; letter-spacing: .6px;
    text-transform: uppercase;
    color: var(--secondary-text-color);
    margin-bottom: 8px;
  }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip {
    padding: 6px 13px;
    border-radius: 16px;
    border: 1.5px solid var(--divider-color, #ddd);
    background: transparent;
    cursor: pointer;
    font-size: 13px;
    color: var(--primary-text-color);
    transition: background .15s, border-color .15s, color .15s;
    -webkit-tap-highlight-color: transparent;
  }
  .chip.active {
    background: var(--primary-color);
    border-color: var(--primary-color);
    color: #fff;
  }
  .chip:hover:not(.active):not(:disabled) {
    border-color: var(--primary-color);
    color: var(--primary-color);
  }
  .chip:disabled {
    opacity: 0.35;
    cursor: default;
  }
  .section.dimmed .section-label { opacity: 0.4; }
`;

class DaikinAircleanerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
  }

  setConfig(config) {
    if (!config.entity) throw new Error('"entity" is required');
    this._config = config;
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    this._update();
  }

  _build() {
    const root = this.shadowRoot;
    root.innerHTML = `
      <style>${STYLES}</style>
      <ha-card>
        <div class="card-row" id="trigger">
          <div class="icon-wrap off" id="icon">
            <ha-icon icon="mdi:air-purifier"></ha-icon>
          </div>
          <div class="info">
            <div class="name" id="name">Daikin Air Cleaner</div>
            <div class="status" id="status">-</div>
          </div>
        </div>
      </ha-card>

      <div class="overlay" id="overlay">
        <div class="sheet" id="sheet">
          <div class="sheet-handle"></div>
          <div class="sheet-header">
            <span class="sheet-title" id="sheet-title">Daikin Air Cleaner</span>
            <button class="close-btn" id="close">✕</button>
          </div>

          <div class="power-row">
            <span class="power-label">電源</span>
            <label class="toggle">
              <input type="checkbox" id="power-cb">
              <div class="toggle-track" id="toggle-track">
                <div class="toggle-thumb"></div>
              </div>
            </label>
          </div>

          <div class="section">
            <div class="section-label">モード</div>
            <div class="chips" id="mode-chips"></div>
          </div>
          <div class="section">
            <div class="section-label">風量</div>
            <div class="chips" id="airvol-chips"></div>
          </div>
          <div class="section">
            <div class="section-label">加湿</div>
            <div class="chips" id="humd-chips"></div>
          </div>
        </div>
      </div>
    `;

    this._buildChips('mode-chips', MODE_LABELS, (v) =>
      this._call('select', 'select_option', { option: v }, this._config.mode_entity));
    this._buildChips('airvol-chips', AIRVOL_LABELS, (v) =>
      this._call('select', 'select_option', { option: v }, this._config.airvol_entity));
    this._buildChips('humd-chips', HUMD_LABELS, (v) =>
      this._call('select', 'select_option', { option: v }, this._config.humd_entity));

    root.getElementById('trigger').addEventListener('click', () => this._open());
    root.getElementById('close').addEventListener('click', () => this._close());
    root.getElementById('overlay').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) this._close();
    });
    root.getElementById('toggle-track').addEventListener('click', () => {
      const isOn = root.getElementById('power-cb').checked;
      this._call('fan', isOn ? 'turn_off' : 'turn_on', {}, this._config.entity);
    });
  }

  _buildChips(id, labels, onClick) {
    const wrap = this.shadowRoot.getElementById(id);
    labels.forEach(label => {
      const btn = document.createElement('button');
      btn.className = 'chip';
      btn.textContent = label;
      btn.dataset.value = label;
      btn.addEventListener('click', () => onClick(label));
      wrap.appendChild(btn);
    });
  }

  _update() {
    if (!this._hass || !this._config) return;

    const fan = this._hass.states[this._config.entity];
    if (!fan) return;

    const isOn = fan.state === 'on';
    const mode = this._state(this._config.mode_entity);
    const airvol = this._state(this._config.airvol_entity);
    const humd   = this._state(this._config.humd_entity);
    const name   = fan.attributes.friendly_name || 'Daikin Air Cleaner';

    this.shadowRoot.getElementById('name').textContent = name;
    this.shadowRoot.getElementById('sheet-title').textContent = name;
    this.shadowRoot.getElementById('icon').className = `icon-wrap${isOn ? '' : ' off'}`;
    this.shadowRoot.getElementById('status').textContent =
      isOn ? [mode, `風量:${airvol}`, `加湿:${humd}`].filter(Boolean).join(' · ') : 'オフ';

    const cb = this.shadowRoot.getElementById('power-cb');
    cb.checked = isOn;
    this.shadowRoot.getElementById('toggle-track').className = `toggle-track${isOn ? ' on' : ''}`;

    this._setActive('mode-chips', mode);
    this._setActive('airvol-chips', airvol);
    this._setActive('humd-chips', humd);

    // おまかせ / のど/はだ 中は風量・加湿を無効化
    const fixedMode = mode !== '手動' && mode !== '';
    this._setDisabled('airvol-chips', fixedMode);
    this._setDisabled('humd-chips', fixedMode);
    this.shadowRoot.getElementById('airvol-chips').closest('.section').classList.toggle('dimmed', fixedMode);
    this.shadowRoot.getElementById('humd-chips').closest('.section').classList.toggle('dimmed', fixedMode);
  }

  _state(entityId) {
    return entityId && this._hass.states[entityId]
      ? this._hass.states[entityId].state
      : '';
  }

  _setActive(containerId, value) {
    this.shadowRoot.getElementById(containerId)
      ?.querySelectorAll('.chip')
      .forEach(c => c.classList.toggle('active', c.dataset.value === value));
  }

  _setDisabled(containerId, disabled) {
    this.shadowRoot.getElementById(containerId)
      ?.querySelectorAll('.chip')
      .forEach(c => { c.disabled = disabled; });
  }

  _open()  { this.shadowRoot.getElementById('overlay').classList.add('open'); }
  _close() { this.shadowRoot.getElementById('overlay').classList.remove('open'); }

  _call(domain, service, data, entityId) {
    if (!entityId || !this._hass) return;
    this._hass.callService(domain, service, { entity_id: entityId, ...data });
  }

  getCardSize() { return 1; }

  static getStubConfig() {
    return {
      entity: 'fan.aircleaner',
      mode_entity:   'select.aircleaner_mode',
      airvol_entity: 'select.aircleaner_airvol',
      humd_entity:   'select.aircleaner_humd',
    };
  }
}

customElements.define('daikin-aircleaner-card', DaikinAircleanerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type:        'daikin-aircleaner-card',
  name:        'Daikin Air Cleaner',
  description: 'Daikin Air Cleaner card with popup controls',
});
