const MODE_LABELS   = ['おまかせ', '風量自動', '手動', '節電', '花粉', 'のど/はだ', 'サーキュ'];
const AIRVOL_LABELS = ['弱', '標準', '高', '最高'];
const HUMD_LABELS   = ['無', '弱', '標準', '高'];

const CARD_STYLES = `
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
    pointer-events: none;
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
`;

const DIALOG_STYLES = `
  dialog.daikin-dialog {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    top: auto;
    margin: 0 auto;
    max-width: 480px;
    width: 100%;
    border: none;
    border-radius: 20px 20px 0 0;
    padding: 0 20px calc(24px + env(safe-area-inset-bottom, 0));
    background: var(--card-background-color, #fff);
    box-shadow: 0 -4px 24px rgba(0,0,0,.18);
    animation: daikin-slide-up .22s ease;
  }
  dialog.daikin-dialog::backdrop {
    background: rgba(0,0,0,.45);
  }
  @keyframes daikin-slide-up {
    from { transform: translateY(60px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }
  .daikin-handle {
    width: 36px; height: 4px;
    background: var(--divider-color, #ddd);
    border-radius: 2px;
    margin: 12px auto 16px;
  }
  .daikin-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 20px;
  }
  .daikin-title { font-size: 17px; font-weight: 600; color: var(--primary-text-color); }
  .daikin-close {
    background: var(--secondary-background-color, #f0f0f0);
    border: none; border-radius: 50%;
    width: 28px; height: 28px;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer; font-size: 14px;
    color: var(--secondary-text-color);
  }
  .daikin-power-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 0 18px;
    border-bottom: 1px solid var(--divider-color, #eee);
    margin-bottom: 18px;
  }
  .daikin-power-label { font-size: 15px; font-weight: 500; color: var(--primary-text-color); }
  .daikin-toggle { position: relative; width: 48px; height: 28px; cursor: pointer; }
  .daikin-toggle-track {
    position: absolute; inset: 0;
    border-radius: 14px;
    background: var(--disabled-color, #ccc);
    transition: background .2s;
  }
  .daikin-toggle-track.on { background: var(--primary-color); }
  .daikin-toggle-thumb {
    position: absolute;
    top: 3px; left: 3px;
    width: 22px; height: 22px;
    border-radius: 50%;
    background: #fff;
    transition: transform .2s;
    box-shadow: 0 1px 4px rgba(0,0,0,.25);
  }
  .daikin-toggle-track.on .daikin-toggle-thumb { transform: translateX(20px); }
  .daikin-section { margin-bottom: 16px; }
  .daikin-section-label {
    font-size: 11px; font-weight: 600; letter-spacing: .6px;
    text-transform: uppercase;
    color: var(--secondary-text-color);
    margin-bottom: 8px;
  }
  .daikin-section.dimmed .daikin-section-label { opacity: 0.4; }
  .daikin-chips { display: flex; flex-wrap: wrap; gap: 6px; }
  .daikin-chip {
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
  .daikin-chip.active {
    background: var(--primary-color);
    border-color: var(--primary-color);
    color: #fff;
  }
  .daikin-chip:disabled { opacity: 0.35; cursor: default; pointer-events: none; }
`;

class DaikinAircleanerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._dialog = null;
  }

  connectedCallback() {
    if (this._config) this._build();
  }

  disconnectedCallback() {
    if (this._dialog) {
      this._dialog.remove();
      this._dialog = null;
    }
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

  _ensureDialogStyles() {
    if (document.getElementById('daikin-dialog-styles')) return;
    const style = document.createElement('style');
    style.id = 'daikin-dialog-styles';
    style.textContent = DIALOG_STYLES;
    document.head.appendChild(style);
  }

  _build() {
    const root = this.shadowRoot;
    root.innerHTML = `
      <style>${CARD_STYLES}</style>
      <ha-card>
        <div class="card-row">
          <div class="icon-wrap off" id="icon">
            <ha-icon icon="mdi:air-purifier"></ha-icon>
          </div>
          <div class="info">
            <div class="name" id="name">Daikin Air Cleaner</div>
            <div class="status" id="status">-</div>
          </div>
        </div>
      </ha-card>
    `;

    if (!this._clickHandler) {
      this._clickHandler = (e) => { e.stopPropagation(); this._open(); };
      this.addEventListener('click', this._clickHandler);
    }

    this._ensureDialogStyles();

    if (this._dialog) {
      this._dialog.remove();
      this._dialog = null;
    }

    const dialog = document.createElement('dialog');
    dialog.className = 'daikin-dialog';
    dialog.innerHTML = `
      <div class="daikin-handle"></div>
      <div class="daikin-header">
        <span class="daikin-title" id="daikin-title">Daikin Air Cleaner</span>
        <button type="button" class="daikin-close" id="daikin-close">✕</button>
      </div>
      <div class="daikin-power-row">
        <span class="daikin-power-label">電源</span>
        <div class="daikin-toggle" id="daikin-toggle">
          <div class="daikin-toggle-track" id="daikin-track">
            <div class="daikin-toggle-thumb"></div>
          </div>
        </div>
      </div>
      <div class="daikin-section">
        <div class="daikin-section-label">モード</div>
        <div class="daikin-chips" id="daikin-mode-chips"></div>
      </div>
      <div class="daikin-section" id="daikin-airvol-section">
        <div class="daikin-section-label">風量</div>
        <div class="daikin-chips" id="daikin-airvol-chips"></div>
      </div>
      <div class="daikin-section" id="daikin-humd-section">
        <div class="daikin-section-label">加湿</div>
        <div class="daikin-chips" id="daikin-humd-chips"></div>
      </div>
    `;
    document.body.appendChild(dialog);
    this._dialog = dialog;

    this._buildChips('daikin-mode-chips', MODE_LABELS, (v) =>
      this._call('fan', 'set_preset_mode', { preset_mode: v }, this._config.entity));
    this._buildChips('daikin-airvol-chips', AIRVOL_LABELS, (v) =>
      this._callService('daikin_aircleaner', 'set_airvol', { airvol: v }));
    this._buildChips('daikin-humd-chips', HUMD_LABELS, (v) =>
      this._callService('daikin_aircleaner', 'set_humd', { humd: v }));

    dialog.addEventListener('cancel', () => this._close());
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) this._close();
    });
    dialog.querySelector('#daikin-close').addEventListener('click', () => this._close());
    dialog.querySelector('#daikin-toggle').addEventListener('click', () => {
      const isOn = dialog.querySelector('#daikin-track').classList.contains('on');
      this._call('fan', isOn ? 'turn_off' : 'turn_on', {}, this._config.entity);
    });
  }

  _buildChips(id, labels, onClick) {
    const wrap = this._dialog.querySelector(`#${id}`);
    labels.forEach(label => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'daikin-chip';
      btn.textContent = label;
      btn.dataset.value = label;
      btn.addEventListener('click', () => onClick(label));
      wrap.appendChild(btn);
    });
  }

  _update() {
    if (!this._hass || !this._config || !this._dialog) return;

    const fan = this._hass.states[this._config.entity];
    if (!fan) return;

    const isOn = fan.state === 'on';
    const mode = fan.attributes.preset_mode || '';
    const airvol = fan.attributes.airvol || '';
    const humd   = fan.attributes.humd   || '';
    const name   = fan.attributes.friendly_name || 'Daikin Air Cleaner';

    this.shadowRoot.getElementById('name').textContent = name;
    this.shadowRoot.getElementById('icon').className = `icon-wrap${isOn ? '' : ' off'}`;
    this.shadowRoot.getElementById('status').textContent =
      isOn ? [mode, mode === '手動' ? `風量:${airvol}` : null, `加湿:${humd}`].filter(Boolean).join(' · ') : 'オフ';

    this._dialog.querySelector('#daikin-title').textContent = name;
    this._dialog.querySelector('#daikin-track').className =
      `daikin-toggle-track${isOn ? ' on' : ''}`;

    this._setActive('daikin-mode-chips', mode);
    this._setActive('daikin-airvol-chips', airvol);
    this._setActive('daikin-humd-chips', humd);

    const airvolDisabled = mode !== '手動';
    const humdDisabled   = mode !== '手動' && mode !== '風量自動';
    this._setDisabled('daikin-airvol-chips', airvolDisabled);
    this._setDisabled('daikin-humd-chips', humdDisabled);
    this._dialog.querySelector('#daikin-airvol-section').classList.toggle('dimmed', airvolDisabled);
    this._dialog.querySelector('#daikin-humd-section').classList.toggle('dimmed', humdDisabled);
  }

  _setActive(containerId, value) {
    this._dialog.querySelectorAll(`#${containerId} .daikin-chip`)
      .forEach(c => c.classList.toggle('active', c.dataset.value === value));
  }

  _setDisabled(containerId, disabled) {
    this._dialog.querySelectorAll(`#${containerId} .daikin-chip`)
      .forEach(c => { c.disabled = disabled; });
  }

  _open()  { if (this._dialog) this._dialog.showModal(); }
  _close() { if (this._dialog) this._dialog.close(); }

  _call(domain, service, data, entityId) {
    if (!entityId || !this._hass) return;
    this._hass.callService(domain, service, { entity_id: entityId, ...data })
      .catch(e => console.error('[daikin] callService ERROR', domain, service, e));
  }

  _callService(domain, service, data) {
    if (!this._hass) return;
    this._hass.callService(domain, service, data)
      .catch(e => console.error('[daikin] callService ERROR', domain, service, e));
  }

  getCardSize() { return 1; }

  static getStubConfig() {
    return { entity: 'fan.aircleaner' };
  }
}

customElements.define('daikin-aircleaner-card', DaikinAircleanerCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type:        'daikin-aircleaner-card',
  name:        'Daikin Air Cleaner',
  description: 'Daikin Air Cleaner card with popup controls',
});
