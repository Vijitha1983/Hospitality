frappe.pages["bar-pos"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "Bar POS",
		single_column: true,
	});
	wrapper.bpos = new BarPOS(wrapper);
};

frappe.pages["bar-pos"].on_page_show = function (wrapper) {
	if (wrapper.bpos) wrapper.bpos.refresh();
};

class BarPOS {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;

		// State
		this.outlet = null;
		this.activeTab = null;
		this.tabItems = [];
		this.allDrinks = [];
		this.categories = [];
		this.openTabs = [];
		this.paymentModes = [];
		this.activeCategory = "All";
		this.searchQuery = "";
		this._tipPct = 0;
		this._selectedPayMode = null;

		this.page.main.css({ padding: 0, overflow: "hidden" });
		this.render();
		this.loadOutlets();
		this.startClock();
	}

	// ─── Render skeleton ──────────────────────────────────────────────────────
	render() {
		this.page.main.html(`
<div class="bpos-wrap">
  <!-- Header -->
  <div class="bpos-header">
    <div class="bpos-logo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:22px;height:22px">
        <path d="M8 22H5a2 2 0 0 1-2-2V6l3-4h11l3 4v14a2 2 0 0 1-2 2h-3"/>
        <path d="M9 22V12h6v10"/><line x1="12" y1="6" x2="12" y2="10"/>
      </svg>
      Bar POS
    </div>
    <div class="bpos-header-center">
      <select class="bpos-select" id="bpos-outlet-sel">
        <option value="">— Select Bar Outlet —</option>
      </select>
    </div>
    <div class="bpos-header-right">
      <span class="bpos-status-dot green" id="bpos-dot"></span>
      <span class="bpos-badge" id="bpos-outlet-badge">No Bar</span>
      <span class="bpos-clock" id="bpos-clock"></span>
    </div>
  </div>

  <!-- Body: 3 columns -->
  <div class="bpos-body">

    <!-- LEFT: Open Tabs -->
    <div class="bpos-tabs-panel">
      <div class="bpos-panel-header">
        <span>Open Tabs</span>
        <span id="bpos-tab-count" style="font-size:11px;color:var(--bpos-text-dim)"></span>
      </div>
      <div class="bpos-tabs-list" id="bpos-tabs-list">
        <div class="bpos-empty">
          <div class="bpos-empty-icon">🍹</div>
          <div>No open tabs</div>
        </div>
      </div>
      <div class="bpos-panel-footer">
        <button class="bpos-btn bpos-btn-new-tab" id="bpos-open-tab-btn" disabled>
          + New Tab
        </button>
      </div>
    </div>

    <!-- CENTER: Drink Menu -->
    <div class="bpos-menu">
      <div class="bpos-categories" id="bpos-categories"></div>
      <div class="bpos-search-bar">
        <input class="bpos-search-input" id="bpos-search" placeholder="Search drinks…" type="text" />
      </div>
      <div class="bpos-menu-grid" id="bpos-menu-grid">
        <div class="bpos-empty" style="grid-column:1/-1">
          <div class="bpos-empty-icon">🥃</div>
          <div>Select or open a tab to order</div>
        </div>
      </div>
    </div>

    <!-- RIGHT: Tab Detail / Order Panel -->
    <div class="bpos-order">
      <div class="bpos-order-head">
        <div class="bpos-order-label">Current Tab</div>
        <div class="bpos-order-tab-name" id="bpos-order-tab">No Tab</div>
        <div class="bpos-order-meta" id="bpos-order-meta"></div>
      </div>

      <div class="bpos-order-items" id="bpos-order-items">
        <div class="bpos-empty">
          <div class="bpos-empty-icon">🛒</div>
          <div>Tab is empty</div>
        </div>
      </div>

      <div class="bpos-totals" id="bpos-totals" style="display:none">
        <div class="bpos-total-row"><span>Tab Total</span><span id="bpos-total">0.00</span></div>
      </div>

      <div class="bpos-actions">
        <button class="bpos-btn bpos-btn-bot" id="bpos-btn-bot" disabled>
          🍸 Fire BOT
        </button>
        <button class="bpos-btn bpos-btn-bill" id="bpos-btn-bill" disabled>
          💳 Close &amp; Bill Tab
        </button>
        <button class="bpos-btn bpos-btn-void" id="bpos-btn-cancel-tab" disabled>
          ✕ Cancel Tab
        </button>
      </div>
    </div>
  </div>
</div>

<!-- New Tab Modal -->
<div class="bpos-modal-overlay" id="bpos-new-tab-modal" style="display:none">
  <div class="bpos-modal">
    <div class="bpos-modal-title">🍹 Open New Tab</div>
    <div style="margin-bottom:10px">
      <label class="bpos-field-label">Tab Type</label>
      <select class="bpos-modal-input" id="bpos-tab-type">
        <option value="Counter Tab">Counter Tab</option>
        <option value="Table Tab">Table Tab</option>
        <option value="Room Service Tab">Room Service Tab</option>
        <option value="Event Tab">Event Tab</option>
      </select>
    </div>
    <div style="margin-bottom:16px">
      <label class="bpos-field-label">Guest / Name</label>
      <input class="bpos-modal-input" id="bpos-tab-guest" type="text" placeholder="Guest name or walk-in" value="Walk-in" />
    </div>
    <div class="bpos-modal-actions">
      <button class="bpos-modal-cancel" id="bpos-new-tab-cancel">Cancel</button>
      <button class="bpos-modal-confirm" id="bpos-new-tab-confirm">Open Tab</button>
    </div>
  </div>
</div>

<!-- Add Drink Modal (modifiers + note) -->
<div class="bpos-modal-overlay" id="bpos-drink-modal" style="display:none">
  <div class="bpos-modal" style="width:340px">
    <div class="bpos-modal-title">🥃 <span id="bpos-drink-modal-name"></span></div>
    <div style="margin-bottom:10px">
      <label class="bpos-field-label">Quantity</label>
      <div style="display:flex;align-items:center;gap:12px">
        <button class="bpos-qty-btn" id="bpos-drink-dec">−</button>
        <span class="bpos-qty-val" id="bpos-drink-qty">1</span>
        <button class="bpos-qty-btn" id="bpos-drink-inc">+</button>
      </div>
    </div>
    <div style="margin-bottom:10px">
      <label class="bpos-field-label">Modifier / Note</label>
      <input class="bpos-modal-input" id="bpos-drink-note" type="text" placeholder="e.g. On the rocks, no ice…" />
    </div>
    <div style="margin-bottom:16px;display:flex;align-items:center;gap:8px">
      <input type="checkbox" id="bpos-drink-comp" style="width:16px;height:16px;accent-color:var(--bpos-accent)" />
      <label style="font-size:13px;color:var(--bpos-text-muted);cursor:pointer" for="bpos-drink-comp">Complimentary</label>
    </div>
    <div class="bpos-modal-actions">
      <button class="bpos-modal-cancel" id="bpos-drink-cancel">Cancel</button>
      <button class="bpos-modal-confirm" id="bpos-drink-confirm">Add to Tab</button>
    </div>
  </div>
</div>

<!-- Payment Modal -->
<div class="bpos-modal-overlay" id="bpos-pay-modal" style="display:none">
  <div class="bpos-modal">
    <div class="bpos-modal-title">💳 Close Tab &amp; Collect Payment</div>
    <div class="bpos-modal-amount" id="bpos-pay-amount">0.00</div>
    <div class="bpos-pay-methods" id="bpos-pay-methods"></div>
    <div style="margin-bottom:8px;font-size:11px;color:var(--bpos-text-muted)">TIP</div>
    <div class="bpos-tip-row" id="bpos-tip-row">
      <button class="bpos-tip-btn selected" data-pct="0">No Tip</button>
      <button class="bpos-tip-btn" data-pct="5">5%</button>
      <button class="bpos-tip-btn" data-pct="10">10%</button>
      <button class="bpos-tip-btn" data-pct="15">15%</button>
    </div>
    <div class="bpos-modal-actions">
      <button class="bpos-modal-cancel" id="bpos-pay-cancel">Cancel</button>
      <button class="bpos-modal-confirm" id="bpos-pay-confirm">Confirm &amp; Close Tab</button>
    </div>
  </div>
</div>
`);
		this.injectStyles();
		this.bindStaticEvents();
	}

	// ─── Bar POS styles (dark amber theme) ───────────────────────────────────
	injectStyles() {
		if (document.getElementById("bpos-styles")) return;
		const s = document.createElement("style");
		s.id = "bpos-styles";
		s.textContent = `
:root {
  --bpos-bg:#0f1117;--bpos-surface:#1a1d2e;--bpos-surface2:#232640;
  --bpos-border:#2d3152;--bpos-accent:#f59e0b;--bpos-accent2:#ef4444;
  --bpos-success:#22c55e;--bpos-danger:#ef4444;
  --bpos-text:#e2e8f0;--bpos-text-muted:#94a3b8;--bpos-text-dim:#64748b;
  --bpos-gold:#f59e0b;--bpos-radius:10px;--bpos-radius-sm:6px;
}
.bpos-wrap{display:grid;grid-template-rows:56px 1fr;height:100vh;background:var(--bpos-bg);color:var(--bpos-text);font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;overflow:hidden}
.bpos-header{display:flex;align-items:center;justify-content:space-between;padding:0 20px;background:var(--bpos-surface);border-bottom:1px solid var(--bpos-border);gap:16px}
.bpos-logo{font-size:16px;font-weight:700;color:var(--bpos-gold);display:flex;align-items:center;gap:8px}
.bpos-header-center{display:flex;align-items:center;gap:12px;flex:1}
.bpos-select{background:var(--bpos-surface2);border:1px solid var(--bpos-border);color:var(--bpos-text);border-radius:var(--bpos-radius-sm);padding:6px 12px;font-size:13px;cursor:pointer;outline:none}
.bpos-select:focus{border-color:var(--bpos-gold)}
.bpos-header-right{display:flex;align-items:center;gap:12px}
.bpos-badge{font-size:11px;padding:3px 10px;border-radius:20px;font-weight:600;background:rgba(245,158,11,.15);color:var(--bpos-gold)}
.bpos-clock{font-size:13px;color:var(--bpos-text-muted);font-variant-numeric:tabular-nums}
.bpos-status-dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.bpos-status-dot.green{background:var(--bpos-success);box-shadow:0 0 6px var(--bpos-success)}
.bpos-body{display:grid;grid-template-columns:280px 1fr 340px;overflow:hidden}

/* LEFT tabs list */
.bpos-tabs-panel{background:var(--bpos-surface);border-right:1px solid var(--bpos-border);display:flex;flex-direction:column;overflow:hidden}
.bpos-panel-header{padding:12px 16px;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--bpos-text-muted);border-bottom:1px solid var(--bpos-border);display:flex;align-items:center;justify-content:space-between}
.bpos-tabs-list{flex:1;overflow-y:auto;padding:8px}
.bpos-panel-footer{padding:10px;border-top:1px solid var(--bpos-border)}

.bpos-tab-card{background:var(--bpos-surface2);border:1px solid var(--bpos-border);border-radius:var(--bpos-radius-sm);padding:10px 14px;margin-bottom:6px;cursor:pointer;transition:all .15s}
.bpos-tab-card:hover{border-color:var(--bpos-gold);background:rgba(245,158,11,.05)}
.bpos-tab-card.active{border-color:var(--bpos-gold);background:rgba(245,158,11,.1)}
.bpos-tab-name{font-size:13px;font-weight:700;color:var(--bpos-text)}
.bpos-tab-meta{font-size:11px;color:var(--bpos-text-dim);margin-top:2px}
.bpos-tab-amount{font-size:14px;font-weight:800;color:var(--bpos-gold);float:right;margin-top:-18px}

/* CENTER menu */
.bpos-menu{display:flex;flex-direction:column;background:var(--bpos-bg);overflow:hidden}
.bpos-categories{display:flex;gap:6px;padding:10px 16px;overflow-x:auto;border-bottom:1px solid var(--bpos-border);scrollbar-width:none}
.bpos-categories::-webkit-scrollbar{display:none}
.bpos-cat-btn{flex-shrink:0;padding:6px 16px;border-radius:20px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--bpos-border);background:var(--bpos-surface);color:var(--bpos-text-muted);transition:all .15s}
.bpos-cat-btn:hover{border-color:var(--bpos-gold);color:var(--bpos-gold)}
.bpos-cat-btn.active{background:var(--bpos-gold);border-color:var(--bpos-gold);color:#000}
.bpos-search-bar{padding:8px 16px}
.bpos-search-input{width:100%;background:var(--bpos-surface);border:1px solid var(--bpos-border);border-radius:var(--bpos-radius-sm);padding:8px 12px;color:var(--bpos-text);font-size:13px;outline:none}
.bpos-search-input:focus{border-color:var(--bpos-gold)}
.bpos-search-input::placeholder{color:var(--bpos-text-dim)}
.bpos-menu-grid{flex:1;overflow-y:auto;padding:12px 16px;display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;align-content:start}
.bpos-drink-card{background:var(--bpos-surface);border:1px solid var(--bpos-border);border-radius:var(--bpos-radius);padding:14px 10px;cursor:pointer;display:flex;flex-direction:column;gap:6px;transition:all .15s;position:relative}
.bpos-drink-card:hover{border-color:var(--bpos-gold);background:var(--bpos-surface2);transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.3)}
.bpos-drink-card:active{transform:scale(.97)}
.bpos-drink-img-ph{width:100%;height:70px;border-radius:var(--bpos-radius-sm);background:var(--bpos-surface2);display:flex;align-items:center;justify-content:center;font-size:28px}
.bpos-drink-name{font-size:12px;font-weight:600;color:var(--bpos-text);line-height:1.3}
.bpos-drink-price{font-size:14px;font-weight:800;color:var(--bpos-gold)}
.bpos-drink-ml{font-size:9px;color:var(--bpos-text-dim);text-transform:uppercase}

/* RIGHT order panel */
.bpos-order{background:var(--bpos-surface);border-left:1px solid var(--bpos-border);display:flex;flex-direction:column;overflow:hidden}
.bpos-order-head{padding:12px 16px;border-bottom:1px solid var(--bpos-border)}
.bpos-order-label{font-size:11px;color:var(--bpos-text-muted);text-transform:uppercase;letter-spacing:.5px}
.bpos-order-tab-name{font-size:18px;font-weight:800;color:var(--bpos-text)}
.bpos-order-meta{font-size:11px;color:var(--bpos-text-dim);margin-top:2px}
.bpos-order-items{flex:1;overflow-y:auto;padding:8px 0}
.bpos-order-item{display:grid;grid-template-columns:1fr auto auto;align-items:center;gap:6px;padding:8px 14px;border-bottom:1px solid rgba(45,49,82,.5)}
.bpos-oi-name{font-size:12px;font-weight:600}
.bpos-oi-note{font-size:10px;color:var(--bpos-text-dim)}
.bpos-oi-comp{font-size:9px;color:var(--bpos-success);font-weight:700}
.bpos-oi-amount{font-size:13px;font-weight:700;min-width:56px;text-align:right}
.bpos-totals{padding:12px 16px;border-top:1px solid var(--bpos-border);display:flex;flex-direction:column;gap:4px}
.bpos-total-row{display:flex;justify-content:space-between;font-size:16px;font-weight:800;color:var(--bpos-text)}
.bpos-actions{padding:12px 16px;display:flex;flex-direction:column;gap:8px;border-top:1px solid var(--bpos-border)}

/* Buttons */
.bpos-btn{width:100%;padding:12px;border-radius:var(--bpos-radius);font-size:14px;font-weight:700;cursor:pointer;border:none;transition:all .15s;display:flex;align-items:center;justify-content:center;gap:8px;letter-spacing:.3px}
.bpos-btn:active{transform:scale(.98)}
.bpos-btn:disabled{opacity:.4;cursor:not-allowed}
.bpos-btn-new-tab{background:rgba(245,158,11,.15);border:1px solid var(--bpos-gold);color:var(--bpos-gold);font-size:13px;padding:8px}
.bpos-btn-new-tab:hover:not(:disabled){background:rgba(245,158,11,.25)}
.bpos-btn-bot{background:linear-gradient(135deg,#f59e0b,#d97706);color:#000}
.bpos-btn-bot:hover:not(:disabled){box-shadow:0 4px 15px rgba(245,158,11,.4)}
.bpos-btn-bill{background:linear-gradient(135deg,#4f7fff,#7c3aed);color:#fff}
.bpos-btn-bill:hover:not(:disabled){box-shadow:0 4px 15px rgba(79,127,255,.4)}
.bpos-btn-void{background:transparent;border:1px solid var(--bpos-border);color:var(--bpos-danger)}
.bpos-btn-void:hover:not(:disabled){background:rgba(239,68,68,.1);border-color:var(--bpos-danger)}

/* Modals */
.bpos-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:1000;backdrop-filter:blur(4px)}
.bpos-modal{background:var(--bpos-surface);border:1px solid var(--bpos-border);border-radius:16px;padding:28px;width:400px;box-shadow:0 24px 60px rgba(0,0,0,.5)}
.bpos-modal-title{font-size:18px;font-weight:800;margin-bottom:20px;color:var(--bpos-text)}
.bpos-modal-amount{text-align:center;font-size:40px;font-weight:900;color:var(--bpos-gold);margin-bottom:20px}
.bpos-field-label{font-size:11px;color:var(--bpos-text-muted);text-transform:uppercase;letter-spacing:.5px;display:block;margin-bottom:6px}
.bpos-modal-input{width:100%;background:var(--bpos-surface2);border:1px solid var(--bpos-border);border-radius:var(--bpos-radius-sm);padding:10px 12px;color:var(--bpos-text);font-size:14px;margin-bottom:4px;outline:none;box-sizing:border-box}
.bpos-modal-input:focus{border-color:var(--bpos-gold)}
.bpos-modal-actions{display:flex;gap:10px;margin-top:4px}
.bpos-modal-cancel{flex:1;padding:12px;border-radius:var(--bpos-radius);border:1px solid var(--bpos-border);background:transparent;color:var(--bpos-text-muted);cursor:pointer;font-size:14px;font-weight:600}
.bpos-modal-confirm{flex:2;padding:12px;border-radius:var(--bpos-radius);border:none;background:linear-gradient(135deg,#f59e0b,#d97706);color:#000;cursor:pointer;font-size:14px;font-weight:700}
.bpos-modal-confirm:hover{box-shadow:0 4px 15px rgba(245,158,11,.4)}
.bpos-pay-methods{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:16px}
.bpos-pay-btn{padding:12px 8px;border-radius:var(--bpos-radius-sm);border:2px solid var(--bpos-border);background:var(--bpos-surface2);color:var(--bpos-text);cursor:pointer;font-size:12px;font-weight:600;text-align:center;transition:all .15s}
.bpos-pay-btn:hover{border-color:var(--bpos-gold)}
.bpos-pay-btn.selected{border-color:var(--bpos-gold);background:rgba(245,158,11,.15);color:var(--bpos-gold)}
.bpos-tip-row{display:flex;gap:8px;margin-bottom:16px}
.bpos-tip-btn{flex:1;padding:8px;border-radius:var(--bpos-radius-sm);border:1px solid var(--bpos-border);background:var(--bpos-surface2);color:var(--bpos-text-muted);cursor:pointer;font-size:12px;transition:all .15s}
.bpos-tip-btn:hover{border-color:var(--bpos-gold);color:var(--bpos-gold)}
.bpos-tip-btn.selected{border-color:var(--bpos-gold);color:var(--bpos-gold);background:rgba(245,158,11,.1)}
.bpos-qty-btn{width:32px;height:32px;border-radius:50%;border:1px solid var(--bpos-border);background:var(--bpos-surface2);color:var(--bpos-text);font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.bpos-qty-btn:hover{background:var(--bpos-gold);border-color:var(--bpos-gold);color:#000}
.bpos-qty-val{font-size:20px;font-weight:800;min-width:32px;text-align:center}
.bpos-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--bpos-text-dim);gap:8px;padding:40px 20px;text-align:center}
.bpos-empty-icon{font-size:48px;opacity:.3}
.bpos-toast{position:fixed;bottom:24px;right:24px;background:var(--bpos-surface2);border:1px solid var(--bpos-border);border-radius:var(--bpos-radius);padding:12px 20px;font-size:13px;font-weight:600;box-shadow:0 8px 30px rgba(0,0,0,.4);z-index:9999;animation:bSlideIn .3s ease;color:var(--bpos-text)}
.bpos-toast.success{border-left:4px solid var(--bpos-success)}
.bpos-toast.error{border-left:4px solid var(--bpos-danger)}
.bpos-toast.info{border-left:4px solid var(--bpos-gold)}
@keyframes bSlideIn{from{transform:translateX(30px);opacity:0}to{transform:translateX(0);opacity:1}}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--bpos-border);border-radius:2px}
`;
		document.head.appendChild(s);
	}

	// ─── Static bindings ──────────────────────────────────────────────────────
	bindStaticEvents() {
		const $ = (id) => document.getElementById(id);

		$("bpos-outlet-sel").addEventListener("change", (e) => this.selectOutlet(e.target.value));

		// New tab
		$("bpos-open-tab-btn").addEventListener("click", () => {
			$("bpos-tab-guest").value = "Walk-in";
			$("bpos-tab-type").value = "Counter Tab";
			$("bpos-new-tab-modal").style.display = "flex";
		});
		$("bpos-new-tab-cancel").addEventListener("click", () => {
			$("bpos-new-tab-modal").style.display = "none";
		});
		$("bpos-new-tab-confirm").addEventListener("click", () => {
			const guest = $("bpos-tab-guest").value.trim() || "Walk-in";
			const type = $("bpos-tab-type").value;
			$("bpos-new-tab-modal").style.display = "none";
			this.openTab(type, guest);
		});

		// Categories
		$("bpos-categories").addEventListener("click", (e) => {
			const btn = e.target.closest(".bpos-cat-btn");
			if (!btn) return;
			this.activeCategory = btn.dataset.cat;
			document.querySelectorAll(".bpos-cat-btn").forEach((b) => b.classList.remove("active"));
			btn.classList.add("active");
			this.renderDrinkGrid();
		});

		// Search
		$("bpos-search").addEventListener("input", (e) => {
			this.searchQuery = e.target.value.toLowerCase();
			this.renderDrinkGrid();
		});

		// BOT
		$("bpos-btn-bot").addEventListener("click", () => this.fireBOT());

		// Bill
		$("bpos-btn-bill").addEventListener("click", () => this.openPayModal());

		// Cancel tab
		$("bpos-btn-cancel-tab").addEventListener("click", () => this.cancelTab());

		// Drink qty modal
		$("bpos-drink-dec").addEventListener("click", () => {
			const el = $("bpos-drink-qty");
			el.textContent = Math.max(1, parseInt(el.textContent) - 1);
		});
		$("bpos-drink-inc").addEventListener("click", () => {
			const el = $("bpos-drink-qty");
			el.textContent = parseInt(el.textContent) + 1;
		});
		$("bpos-drink-cancel").addEventListener("click", () => {
			$("bpos-drink-modal").style.display = "none";
		});
		$("bpos-drink-confirm").addEventListener("click", () => {
			$("bpos-drink-modal").style.display = "none";
			const qty = parseInt($("bpos-drink-qty").textContent) || 1;
			const note = $("bpos-drink-note").value.trim();
			const comp = $("bpos-drink-comp").checked ? 1 : 0;
			this.doAddDrink(this._pendingDrink, qty, note, comp);
		});

		// Payment modal
		$("bpos-pay-cancel").addEventListener("click", () => {
			$("bpos-pay-modal").style.display = "none";
		});
		$("bpos-pay-confirm").addEventListener("click", () => this.confirmPayment());

		// Tip
		$("bpos-tip-row").addEventListener("click", (e) => {
			const btn = e.target.closest(".bpos-tip-btn");
			if (!btn) return;
			document.querySelectorAll(".bpos-tip-btn").forEach((b) => b.classList.remove("selected"));
			btn.classList.add("selected");
			this._tipPct = parseInt(btn.dataset.pct);
		});
	}

	// ─── Clock ────────────────────────────────────────────────────────────────
	startClock() {
		const el = document.getElementById("bpos-clock");
		const tick = () => {
			el.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
		};
		tick();
		setInterval(tick, 1000);
	}

	// ─── Outlets ──────────────────────────────────────────────────────────────
	loadOutlets() {
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.get_bar_outlets",
			callback: (r) => {
				const sel = document.getElementById("bpos-outlet-sel");
				(r.message || []).forEach((o) => {
					const opt = document.createElement("option");
					opt.value = o.name;
					opt.textContent = o.outlet_name;
					sel.appendChild(opt);
				});
				if (r.message && r.message.length === 1) {
					sel.value = r.message[0].name;
					this.selectOutlet(r.message[0].name);
				}
			},
		});
	}

	selectOutlet(name) {
		if (!name) return;
		this.outlet = name;
		document.getElementById("bpos-outlet-badge").textContent = name;
		document.getElementById("bpos-open-tab-btn").disabled = false;
		this.loadTabs();
		this.loadDrinkMenu();
		this.loadPaymentModes();
	}

	refresh() {
		if (this.outlet) {
			this.loadTabs();
			if (this.activeTab) this.loadTabItems();
		}
	}

	// ─── Tabs ─────────────────────────────────────────────────────────────────
	loadTabs() {
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.get_open_tabs",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.openTabs = r.message || [];
				this.renderTabsList();
			},
		});
	}

	renderTabsList() {
		const list = document.getElementById("bpos-tabs-list");
		const count = document.getElementById("bpos-tab-count");
		count.textContent = `${this.openTabs.length} open`;

		if (!this.openTabs.length) {
			list.innerHTML = `<div class="bpos-empty">
				<div class="bpos-empty-icon">🍹</div>
				<div>No open tabs</div>
			</div>`;
			return;
		}

		list.innerHTML = this.openTabs
			.map((t) => {
				const active = this.activeTab === t.name ? " active" : "";
				const opened = frappe.datetime.str_to_user(t.open_time) || t.open_time;
				return `<div class="bpos-tab-card${active}" data-tab="${t.name}">
					<div class="bpos-tab-name">${t.tab_no} — ${t.guest_name || t.tab_type}</div>
					<div class="bpos-tab-amount">${frappe.format(t.total_amount, { fieldtype: "Currency" })}</div>
					<div class="bpos-tab-meta">${t.tab_type} · ${t.order_count || 0} round(s)</div>
					<div class="bpos-tab-meta">Opened: ${opened}</div>
				</div>`;
			})
			.join("");

		list.querySelectorAll(".bpos-tab-card").forEach((card) => {
			card.addEventListener("click", () => this.selectTab(card.dataset.tab));
		});
	}

	openTab(tabType, guestName) {
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.open_tab",
			args: { outlet: this.outlet, tab_type: tabType, guest_name: guestName },
			callback: (r) => {
				this.toast(`Tab ${r.message} opened`, "success");
				this.loadTabs();
				this.selectTab(r.message);
			},
		});
	}

	selectTab(tabName) {
		this.activeTab = tabName;
		const tab = this.openTabs.find((t) => t.name === tabName);
		if (tab) {
			document.getElementById("bpos-order-tab").textContent = `${tab.tab_no}`;
			document.getElementById("bpos-order-meta").textContent =
				`${tab.guest_name || tab.tab_type} · ${tab.tab_type}`;
		}
		// Highlight active
		document.querySelectorAll(".bpos-tab-card").forEach((c) => {
			c.classList.toggle("active", c.dataset.tab === tabName);
		});
		this.loadTabItems();
	}

	// ─── Tab Items ────────────────────────────────────────────────────────────
	loadTabItems() {
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.get_tab_items",
			args: { tab: this.activeTab },
			callback: (r) => {
				this.tabItems = r.message || [];
				this.renderTabPanel();
			},
		});
	}

	renderTabPanel() {
		const container = document.getElementById("bpos-order-items");
		const totalsEl = document.getElementById("bpos-totals");

		if (!this.tabItems.length) {
			container.innerHTML = `<div class="bpos-empty">
				<div class="bpos-empty-icon">🛒</div>
				<div>Tab is empty — add drinks</div>
			</div>`;
			totalsEl.style.display = "none";
		} else {
			container.innerHTML = this.tabItems
				.map(
					(item) => `
				<div class="bpos-order-item">
					<div>
						<div class="bpos-oi-name">${item.drink_item}</div>
						${item.special_instructions ? `<div class="bpos-oi-note">${item.special_instructions}</div>` : ""}
						${item.is_complimentary ? '<div class="bpos-oi-comp">COMP</div>' : ""}
					</div>
					<div style="font-size:12px;font-weight:700;color:var(--bpos-text-muted)">×${item.qty}</div>
					<div class="bpos-oi-amount">${frappe.format(item.amount, { fieldtype: "Currency" })}</div>
				</div>`
				)
				.join("");

			const total = this.tabItems.reduce((s, i) => s + (i.amount || 0), 0);
			document.getElementById("bpos-total").textContent = frappe.format(total, { fieldtype: "Currency" });
			totalsEl.style.display = "flex";
			this._tabTotal = total;
		}

		const hasItems = this.tabItems.length > 0;
		document.getElementById("bpos-btn-bot").disabled = !hasItems;
		document.getElementById("bpos-btn-bill").disabled = !hasItems;
		document.getElementById("bpos-btn-cancel-tab").disabled = !this.activeTab;
	}

	// ─── Drink Menu ───────────────────────────────────────────────────────────
	loadDrinkMenu() {
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.get_drink_categories",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.categories = r.message || [];
				this.renderCategories();
			},
		});
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.get_drink_items",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.allDrinks = r.message || [];
				this.renderDrinkGrid();
			},
		});
	}

	renderCategories() {
		const bar = document.getElementById("bpos-categories");
		bar.innerHTML =
			`<button class="bpos-cat-btn active" data-cat="All">All</button>` +
			this.categories.map((c) => `<button class="bpos-cat-btn" data-cat="${c}">${c}</button>`).join("");
	}

	renderDrinkGrid() {
		const grid = document.getElementById("bpos-menu-grid");
		const catEmoji = {
			Beer: "🍺", Wine: "🍷", Spirits: "🥃", Cocktails: "🍹",
			Mocktails: "🥤", "Soft Drinks": "🧃", "Hot Beverages": "☕",
		};

		let drinks = this.allDrinks;
		if (this.activeCategory !== "All") drinks = drinks.filter((d) => d.category === this.activeCategory);
		if (this.searchQuery) drinks = drinks.filter((d) => d.item_name.toLowerCase().includes(this.searchQuery));

		if (!drinks.length) {
			grid.innerHTML = `<div class="bpos-empty" style="grid-column:1/-1">
				<div class="bpos-empty-icon">🔍</div><div>No drinks found</div>
			</div>`;
			return;
		}

		grid.innerHTML = drinks
			.map((d) => {
				const img = d.image
					? `<img style="width:100%;height:70px;object-fit:cover;border-radius:var(--bpos-radius-sm)" src="${d.image}" alt="" />`
					: `<div class="bpos-drink-img-ph">${catEmoji[d.category] || "🥃"}</div>`;
				const ml = d.measure_ml ? `${d.measure_ml} ml` : "";
				return `<div class="bpos-drink-card" data-drink="${d.name}">
					${img}
					<div class="bpos-drink-name">${d.item_name}</div>
					<div class="bpos-drink-price">${frappe.format(d.selling_price, { fieldtype: "Currency" })}</div>
					<div class="bpos-drink-ml">${ml}</div>
				</div>`;
			})
			.join("");

		grid.querySelectorAll(".bpos-drink-card").forEach((card) => {
			card.addEventListener("click", () => {
				if (!this.activeTab) {
					this.toast("Open or select a tab first", "error");
					return;
				}
				this._pendingDrink = card.dataset.drink;
				document.getElementById("bpos-drink-qty").textContent = "1";
				document.getElementById("bpos-drink-note").value = "";
				document.getElementById("bpos-drink-comp").checked = false;
				document.getElementById("bpos-drink-modal-name").textContent =
					card.querySelector(".bpos-drink-name").textContent;
				document.getElementById("bpos-drink-modal").style.display = "flex";
			});
		});
	}

	// ─── Add Drink ────────────────────────────────────────────────────────────
	doAddDrink(drinkItem, qty, note, isComp) {
		this._pendingDrink = null;
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.add_drink_to_tab",
			args: {
				tab: this.activeTab,
				drink_item: drinkItem,
				qty,
				special_instructions: note,
				is_complimentary: isComp,
			},
			callback: () => {
				this.loadTabItems();
				this.loadTabs();
				this.toast(isComp ? "Complimentary drink added" : "Drink added to tab", "success");
			},
		});
	}

	// ─── BOT ─────────────────────────────────────────────────────────────────
	fireBOT() {
		if (!this.activeTab) return;
		const tabEl = this.openTabs.find((t) => t.name === this.activeTab);
		frappe.confirm(
			`Fire BOT for tab <b>${tabEl ? tabEl.tab_no : this.activeTab}</b>?`,
			() => {
				frappe.call({
					method: "hospitality.bar.page.bar_pos.bar_pos.fire_bot",
					args: { tab: this.activeTab },
					callback: (r) => {
						const cnt = (r.message.fired || []).length;
						this.toast(`BOT fired — ${cnt} order(s) sent to bartender 🍸`, "success");
						this.loadTabItems();
					},
				});
			}
		);
	}

	// ─── Payment ──────────────────────────────────────────────────────────────
	loadPaymentModes() {
		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.get_payment_modes",
			callback: (r) => {
				this.paymentModes = r.message || [];
			},
		});
	}

	openPayModal() {
		if (!this.activeTab) return;
		const total = this._tabTotal || 0;
		this._selectedPayMode = null;
		this._tipPct = 0;

		const modesEl = document.getElementById("bpos-pay-methods");
		const modes =
			this.paymentModes.length > 0
				? this.paymentModes
				: [{ name: "Cash" }, { name: "Credit Card" }, { name: "UPI" }];

		modesEl.innerHTML = modes
			.slice(0, 6)
			.map((m) => `<button class="bpos-pay-btn" data-mode="${m.name}">${m.name}</button>`)
			.join("");

		modesEl.querySelectorAll(".bpos-pay-btn").forEach((btn) => {
			btn.addEventListener("click", () => {
				modesEl.querySelectorAll(".bpos-pay-btn").forEach((b) => b.classList.remove("selected"));
				btn.classList.add("selected");
				this._selectedPayMode = btn.dataset.mode;
			});
		});

		document.querySelectorAll(".bpos-tip-btn").forEach((b) => b.classList.remove("selected"));
		document.querySelector('.bpos-tip-btn[data-pct="0"]').classList.add("selected");

		document.getElementById("bpos-pay-amount").textContent = frappe.format(total, { fieldtype: "Currency" });
		document.getElementById("bpos-pay-modal").style.display = "flex";
	}

	confirmPayment() {
		if (!this._selectedPayMode) {
			this.toast("Select a payment method", "error");
			return;
		}
		const total = this._tabTotal || 0;
		const tip = total * (this._tipPct || 0) / 100;

		frappe.call({
			method: "hospitality.bar.page.bar_pos.bar_pos.close_tab_with_payment",
			args: { tab: this.activeTab, payment_method: this._selectedPayMode, tip },
			callback: (r) => {
				document.getElementById("bpos-pay-modal").style.display = "none";
				this.toast(`Invoice ${r.message.invoice} — Tab closed ✓`, "success");
				this.activeTab = null;
				this.tabItems = [];
				document.getElementById("bpos-order-tab").textContent = "No Tab";
				document.getElementById("bpos-order-meta").textContent = "";
				document.getElementById("bpos-order-items").innerHTML = `<div class="bpos-empty">
					<div class="bpos-empty-icon">🛒</div><div>Tab is empty</div>
				</div>`;
				document.getElementById("bpos-totals").style.display = "none";
				["bpos-btn-bot", "bpos-btn-bill", "bpos-btn-cancel-tab"].forEach((id) => {
					document.getElementById(id).disabled = true;
				});
				this.loadTabs();
			},
		});
	}

	// ─── Cancel Tab ───────────────────────────────────────────────────────────
	cancelTab() {
		if (!this.activeTab) return;
		frappe.confirm("Cancel this tab? All orders on this tab will be voided.", () => {
			frappe.call({
				method: "hospitality.bar.page.bar_pos.bar_pos.cancel_tab",
				args: { tab: this.activeTab, reason: "Cancelled from POS" },
				callback: () => {
					this.toast("Tab cancelled", "info");
					this.activeTab = null;
					this.tabItems = [];
					document.getElementById("bpos-order-tab").textContent = "No Tab";
					document.getElementById("bpos-order-meta").textContent = "";
					document.getElementById("bpos-order-items").innerHTML = `<div class="bpos-empty">
						<div class="bpos-empty-icon">🛒</div><div>Tab is empty</div>
					</div>`;
					document.getElementById("bpos-totals").style.display = "none";
					["bpos-btn-bot", "bpos-btn-bill", "bpos-btn-cancel-tab"].forEach((id) => {
						document.getElementById(id).disabled = true;
					});
					this.loadTabs();
				},
			});
		});
	}

	// ─── Toast ────────────────────────────────────────────────────────────────
	toast(msg, type = "info") {
		const t = document.createElement("div");
		t.className = `bpos-toast ${type}`;
		t.textContent = msg;
		document.body.appendChild(t);
		setTimeout(() => t.remove(), 3200);
	}
}
