/*
 * Table Order App — Steward mobile/tablet ordering interface
 * Designed for portrait phone / 10" tablet use by floor staff
 */
frappe.pages["table-order"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "Table Order",
		single_column: true,
	});
	wrapper.toa = new TableOrderApp(wrapper);
};

frappe.pages["table-order"].on_page_show = function (wrapper) {
	if (wrapper.toa) wrapper.toa.refresh();
};

class TableOrderApp {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;

		// State
		this.outlet = null;
		this.table = null;
		this.order = null;
		this.pendingItems = [];   // items not yet sent (KOT not fired)
		this.sentItems = [];      // items already in kitchen
		this.allMenuItems = [];
		this.categories = [];
		this.activeCategory = "All";
		this.searchQuery = "";
		this.view = "tables";     // "tables" | "order"

		this.page.main.css({ padding: 0, overflow: "hidden" });
		this.injectStyles();
		this.render();
		this.loadOutlets();
	}

	// ─── Styles ───────────────────────────────────────────────────────────────
	injectStyles() {
		if (document.getElementById("toa-styles")) return;
		const s = document.createElement("style");
		s.id = "toa-styles";
		s.textContent = `
:root{
  --toa-bg:#0f1117;--toa-surface:#1a1d2e;--toa-surface2:#232640;
  --toa-border:#2d3152;--toa-accent:#4f7fff;--toa-green:#22c55e;
  --toa-orange:#f97316;--toa-red:#ef4444;--toa-gold:#f59e0b;
  --toa-text:#e2e8f0;--toa-muted:#94a3b8;--toa-dim:#64748b;
  --toa-radius:12px;--toa-radius-sm:8px;
}
.toa-wrap{display:flex;flex-direction:column;height:100vh;background:var(--toa-bg);color:var(--toa-text);font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;max-width:600px;margin:0 auto}

/* Top bar */
.toa-topbar{display:flex;align-items:center;gap:10px;padding:10px 16px;background:var(--toa-surface);border-bottom:1px solid var(--toa-border);min-height:52px}
.toa-back-btn{width:36px;height:36px;border-radius:50%;border:1px solid var(--toa-border);background:var(--toa-surface2);color:var(--toa-text);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.toa-back-btn:hover{border-color:var(--toa-accent);color:var(--toa-accent)}
.toa-title{font-size:16px;font-weight:800;flex:1}
.toa-subtitle{font-size:11px;color:var(--toa-muted);flex:1;text-align:right}
.toa-outlet-sel{background:var(--toa-surface2);border:1px solid var(--toa-border);color:var(--toa-text);border-radius:var(--toa-radius-sm);padding:5px 10px;font-size:12px;flex:1;outline:none}

/* ── Tables View ── */
.toa-section-head{padding:12px 16px 6px;font-size:11px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--toa-muted)}
.toa-tables-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:8px 16px;overflow-y:auto;flex:1}
.toa-table-card{aspect-ratio:1;border-radius:var(--toa-radius);border:2px solid transparent;cursor:pointer;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;transition:all .15s;position:relative}
.toa-table-card.available{background:rgba(34,197,94,.1);border-color:var(--toa-green);color:var(--toa-green)}
.toa-table-card.occupied{background:rgba(239,68,68,.12);border-color:var(--toa-red);color:var(--toa-red)}
.toa-table-card.reserved{background:rgba(245,158,11,.1);border-color:var(--toa-gold);color:var(--toa-gold)}
.toa-table-card.dirty{background:rgba(71,85,105,.2);border-color:var(--toa-dim);color:var(--toa-dim);cursor:default}
.toa-table-card.blocked{background:rgba(239,68,68,.04);border-color:rgba(239,68,68,.2);color:var(--toa-dim);cursor:not-allowed}
.toa-table-card:hover:not(.dirty):not(.blocked){transform:scale(1.04);box-shadow:0 4px 20px rgba(0,0,0,.3)}
.toa-tnum{font-size:18px;font-weight:900}
.toa-tcap{font-size:9px;opacity:.7}
.toa-ttot{font-size:10px;font-weight:700;position:absolute;bottom:6px;right:7px}

/* ── Order View ── */
.toa-order-wrap{display:flex;flex-direction:column;flex:1;overflow:hidden}

/* Tab strip */
.toa-tabs{display:flex;border-bottom:2px solid var(--toa-border)}
.toa-tab{flex:1;padding:10px;text-align:center;font-size:12px;font-weight:700;cursor:pointer;color:var(--toa-muted);border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s}
.toa-tab.active{color:var(--toa-accent);border-bottom-color:var(--toa-accent)}

/* Menu sub-view */
.toa-menu-view{display:flex;flex-direction:column;flex:1;overflow:hidden}
.toa-cats{display:flex;gap:6px;padding:8px 12px;overflow-x:auto;scrollbar-width:none}
.toa-cats::-webkit-scrollbar{display:none}
.toa-cat-btn{flex-shrink:0;padding:5px 14px;border-radius:20px;font-size:11px;font-weight:600;cursor:pointer;border:1px solid var(--toa-border);background:var(--toa-surface);color:var(--toa-muted);transition:all .15s}
.toa-cat-btn:hover{border-color:var(--toa-accent);color:var(--toa-accent)}
.toa-cat-btn.active{background:var(--toa-accent);border-color:var(--toa-accent);color:#fff}
.toa-search{padding:6px 12px}
.toa-search input{width:100%;background:var(--toa-surface);border:1px solid var(--toa-border);border-radius:var(--toa-radius-sm);padding:7px 12px;color:var(--toa-text);font-size:13px;outline:none;box-sizing:border-box}
.toa-search input:focus{border-color:var(--toa-accent)}
.toa-search input::placeholder{color:var(--toa-dim)}
.toa-item-list{flex:1;overflow-y:auto;padding:4px 8px}
.toa-item-row{display:flex;align-items:center;gap:10px;padding:10px 8px;border-radius:var(--toa-radius-sm);cursor:pointer;transition:background .1s;border-bottom:1px solid rgba(45,49,82,.5)}
.toa-item-row:hover{background:rgba(79,127,255,.07)}
.toa-item-row:active{background:rgba(79,127,255,.14)}
.toa-item-emoji{width:36px;height:36px;border-radius:8px;background:var(--toa-surface2);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}
.toa-item-info{flex:1}
.toa-item-name{font-size:13px;font-weight:600}
.toa-item-station{font-size:10px;color:var(--toa-dim)}
.toa-item-price{font-size:14px;font-weight:800;color:var(--toa-accent)}
.toa-item-add{width:30px;height:30px;border-radius:50%;border:none;background:var(--toa-accent);color:#fff;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .1s}
.toa-item-add:active{transform:scale(.9)}

/* Order items sub-view */
.toa-order-view{flex:1;overflow-y:auto;padding:4px 0}
.toa-ord-section{padding:8px 14px 4px;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--toa-muted)}
.toa-ord-row{display:flex;align-items:center;gap:8px;padding:9px 14px;border-bottom:1px solid rgba(45,49,82,.4)}
.toa-ord-name{flex:1;font-size:13px;font-weight:600}
.toa-ord-note{font-size:10px;color:var(--toa-dim)}
.toa-ord-status{font-size:9px;font-weight:700;padding:2px 8px;border-radius:10px}
.toa-ord-status.pending{background:rgba(79,127,255,.15);color:var(--toa-accent)}
.toa-ord-status.in-prep{background:rgba(249,115,22,.15);color:var(--toa-orange)}
.toa-ord-status.ready{background:rgba(34,197,94,.15);color:var(--toa-green)}
.toa-ord-status.served{background:rgba(71,85,105,.2);color:var(--toa-dim)}
.toa-ord-qty{font-size:11px;color:var(--toa-muted);white-space:nowrap}
.toa-ord-amt{font-size:13px;font-weight:700;min-width:48px;text-align:right}
.toa-serve-btn{padding:4px 10px;font-size:11px;font-weight:700;border-radius:20px;border:1px solid var(--toa-green);background:transparent;color:var(--toa-green);cursor:pointer}
.toa-serve-btn:hover{background:rgba(34,197,94,.15)}

/* Pending items cart badge */
.toa-pending-badge{background:var(--toa-orange);color:#fff;font-size:10px;font-weight:800;padding:1px 6px;border-radius:10px;margin-left:6px}

/* Bottom action bar */
.toa-bottom-bar{padding:12px 16px;background:var(--toa-surface);border-top:1px solid var(--toa-border);display:flex;gap:10px}
.toa-action-btn{flex:1;padding:12px;border-radius:var(--toa-radius);font-size:14px;font-weight:700;cursor:pointer;border:none;transition:all .15s;display:flex;align-items:center;justify-content:center;gap:6px}
.toa-action-btn:disabled{opacity:.4;cursor:not-allowed}
.toa-action-btn:active:not(:disabled){transform:scale(.97)}
.toa-btn-kot{background:linear-gradient(135deg,#f97316,#ef4444);color:#fff}
.toa-btn-kot:hover:not(:disabled){box-shadow:0 4px 15px rgba(239,68,68,.4)}
.toa-btn-new{background:rgba(34,197,94,.15);border:1px solid var(--toa-green);color:var(--toa-green)}

/* Quick add qty dialog */
.toa-modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.65);display:flex;align-items:flex-end;justify-content:center;z-index:1000;backdrop-filter:blur(3px)}
.toa-modal{background:var(--toa-surface);border-radius:20px 20px 0 0;padding:24px 20px 32px;width:100%;max-width:600px;box-shadow:0 -10px 40px rgba(0,0,0,.5)}
.toa-modal-title{font-size:16px;font-weight:800;margin-bottom:16px;color:var(--toa-text)}
.toa-modal-body{display:flex;align-items:center;gap:16px;margin-bottom:16px;justify-content:center}
.toa-modal-qty-btn{width:44px;height:44px;border-radius:50%;border:1px solid var(--toa-border);background:var(--toa-surface2);color:var(--toa-text);font-size:22px;cursor:pointer;display:flex;align-items:center;justify-content:center}
.toa-modal-qty-btn:hover{background:var(--toa-accent);border-color:var(--toa-accent)}
.toa-modal-qty{font-size:28px;font-weight:900;min-width:48px;text-align:center}
.toa-modal-note{width:100%;background:var(--toa-surface2);border:1px solid var(--toa-border);border-radius:var(--toa-radius-sm);padding:10px 12px;color:var(--toa-text);font-size:13px;margin-bottom:14px;outline:none;box-sizing:border-box}
.toa-modal-note:focus{border-color:var(--toa-accent)}
.toa-modal-note::placeholder{color:var(--toa-dim)}
.toa-modal-btns{display:flex;gap:10px}
.toa-modal-cancel{flex:1;padding:12px;border-radius:var(--toa-radius);border:1px solid var(--toa-border);background:transparent;color:var(--toa-muted);cursor:pointer;font-size:14px;font-weight:600}
.toa-modal-confirm{flex:2;padding:12px;border-radius:var(--toa-radius);border:none;background:linear-gradient(135deg,#4f7fff,#7c3aed);color:#fff;cursor:pointer;font-size:14px;font-weight:700}

/* Covers dialog */
.toa-covers-overlay{position:fixed;inset:0;background:rgba(0,0,0,.65);display:flex;align-items:center;justify-content:center;z-index:1001;backdrop-filter:blur(3px)}
.toa-covers-box{background:var(--toa-surface);border:1px solid var(--toa-border);border-radius:var(--toa-radius);padding:28px;width:280px;text-align:center}
.toa-covers-title{font-size:16px;font-weight:800;margin-bottom:16px}
.toa-covers-input{width:80px;background:var(--toa-surface2);border:1px solid var(--toa-border);border-radius:var(--toa-radius-sm);padding:10px;color:var(--toa-text);font-size:22px;font-weight:800;text-align:center;outline:none;margin-bottom:16px}
.toa-covers-input:focus{border-color:var(--toa-accent)}
.toa-empty{display:flex;flex-direction:column;align-items:center;justify-content:center;color:var(--toa-dim);gap:8px;padding:48px 20px;text-align:center}
.toa-empty-icon{font-size:48px;opacity:.3}
.toa-toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--toa-surface2);border:1px solid var(--toa-border);border-radius:var(--toa-radius);padding:12px 20px;font-size:13px;font-weight:600;box-shadow:0 8px 30px rgba(0,0,0,.4);z-index:9999;animation:tSlide .3s ease;color:var(--toa-text);white-space:nowrap}
.toa-toast.success{border-left:4px solid var(--toa-green)}
.toa-toast.error{border-left:4px solid var(--toa-red)}
.toa-toast.info{border-left:4px solid var(--toa-accent)}
@keyframes tSlide{from{opacity:0;transform:translateX(-50%) translateY(16px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}
`;
		document.head.appendChild(s);
	}

	// ─── Render ───────────────────────────────────────────────────────────────
	render() {
		this.page.main.html(`
<div class="toa-wrap">

  <!-- Top bar -->
  <div class="toa-topbar" id="toa-topbar">
    <div class="toa-title">🍽️ Table Order</div>
    <select class="toa-outlet-sel" id="toa-outlet-sel">
      <option value="">— Outlet —</option>
    </select>
  </div>

  <!-- Tables view -->
  <div id="toa-tables-view" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
    <div class="toa-section-head">SELECT TABLE</div>
    <div class="toa-tables-grid" id="toa-tables-grid">
      <div class="toa-empty" style="grid-column:1/-1">
        <div class="toa-empty-icon">🏠</div>
        <div>Select an outlet</div>
      </div>
    </div>
  </div>

  <!-- Order view (hidden initially) -->
  <div id="toa-order-view" style="display:none;flex-direction:column;flex:1;overflow:hidden">

    <!-- Back + table name -->
    <div class="toa-topbar" id="toa-order-topbar">
      <button class="toa-back-btn" id="toa-back-btn">←</button>
      <div class="toa-title" id="toa-order-title">Table —</div>
      <div class="toa-subtitle" id="toa-order-ref"></div>
    </div>

    <!-- Tabs: Menu | Order -->
    <div class="toa-tabs">
      <div class="toa-tab active" id="toa-tab-menu" data-tab="menu">
        Menu
        <span class="toa-pending-badge" id="toa-pending-count" style="display:none">0</span>
      </div>
      <div class="toa-tab" id="toa-tab-order" data-tab="order">Kitchen Status</div>
    </div>

    <!-- Menu sub-view -->
    <div class="toa-menu-view" id="toa-menu-sub">
      <div class="toa-cats" id="toa-cats"></div>
      <div class="toa-search"><input type="text" id="toa-search" placeholder="Search…" /></div>
      <div class="toa-item-list" id="toa-item-list">
        <div class="toa-empty"><div class="toa-empty-icon">🔍</div><div>Loading menu…</div></div>
      </div>
    </div>

    <!-- Order status sub-view -->
    <div id="toa-order-sub" style="display:none;flex:1;overflow-y:auto">
      <div id="toa-order-items-list">
        <div class="toa-empty"><div class="toa-empty-icon">🛒</div><div>No items yet</div></div>
      </div>
    </div>

    <!-- Bottom action bar -->
    <div class="toa-bottom-bar">
      <button class="toa-action-btn toa-btn-kot" id="toa-btn-kot" disabled>
        🔥 Fire KOT
      </button>
    </div>
  </div>

</div>

<!-- Item add bottom sheet -->
<div class="toa-modal-overlay" id="toa-add-modal" style="display:none">
  <div class="toa-modal">
    <div class="toa-modal-title" id="toa-add-item-name">Add Item</div>
    <div class="toa-modal-body">
      <button class="toa-modal-qty-btn" id="toa-add-dec">−</button>
      <div class="toa-modal-qty" id="toa-add-qty">1</div>
      <button class="toa-modal-qty-btn" id="toa-add-inc">+</button>
    </div>
    <input class="toa-modal-note" id="toa-add-note" type="text" placeholder="Special instructions (optional)…" />
    <div class="toa-modal-btns">
      <button class="toa-modal-cancel" id="toa-add-cancel">Cancel</button>
      <button class="toa-modal-confirm" id="toa-add-confirm">Add to Order</button>
    </div>
  </div>
</div>

<!-- Covers bottom sheet -->
<div class="toa-covers-overlay" id="toa-covers-modal" style="display:none">
  <div class="toa-covers-box">
    <div class="toa-covers-title">👥 Covers</div>
    <input class="toa-covers-input" id="toa-covers-inp" type="number" min="1" max="20" value="2" />
    <div style="display:flex;gap:8px">
      <button class="toa-modal-cancel" id="toa-covers-cancel" style="flex:1;padding:10px;border-radius:10px;border:1px solid var(--toa-border);background:transparent;color:var(--toa-muted);cursor:pointer;font-size:14px">Cancel</button>
      <button class="toa-modal-confirm" id="toa-covers-ok" style="flex:2;padding:10px;border-radius:10px;border:none;background:linear-gradient(135deg,#4f7fff,#7c3aed);color:#fff;cursor:pointer;font-size:14px;font-weight:700">Open Order</button>
    </div>
  </div>
</div>
`);
		this.bindEvents();
	}

	// ─── Bindings ─────────────────────────────────────────────────────────────
	bindEvents() {
		const $ = (id) => document.getElementById(id);

		$("toa-outlet-sel").addEventListener("change", (e) => this.selectOutlet(e.target.value));

		// Tab switch (Menu / Order)
		document.querySelectorAll(".toa-tab").forEach((tab) => {
			tab.addEventListener("click", () => {
				document.querySelectorAll(".toa-tab").forEach((t) => t.classList.remove("active"));
				tab.classList.add("active");
				const which = tab.dataset.tab;
				$("toa-menu-sub").style.display = which === "menu" ? "flex" : "none";
				$("toa-order-sub").style.display = which === "order" ? "block" : "none";
				if (which === "order") this.loadOrderStatus();
			});
		});

		// Back button
		$("toa-back-btn").addEventListener("click", () => this.showTablesView());

		// Category filter
		$("toa-cats").addEventListener("click", (e) => {
			const btn = e.target.closest(".toa-cat-btn");
			if (!btn) return;
			this.activeCategory = btn.dataset.cat;
			document.querySelectorAll(".toa-cat-btn").forEach((b) => b.classList.remove("active"));
			btn.classList.add("active");
			this.renderItemList();
		});

		// Search
		$("toa-search").addEventListener("input", (e) => {
			this.searchQuery = e.target.value.toLowerCase();
			this.renderItemList();
		});

		// KOT
		$("toa-btn-kot").addEventListener("click", () => this.fireKOT());

		// Add item modal
		$("toa-add-dec").addEventListener("click", () => {
			const el = $("toa-add-qty");
			el.textContent = Math.max(1, parseInt(el.textContent) - 1);
		});
		$("toa-add-inc").addEventListener("click", () => {
			const el = $("toa-add-qty");
			el.textContent = parseInt(el.textContent) + 1;
		});
		$("toa-add-cancel").addEventListener("click", () => {
			$("toa-add-modal").style.display = "none";
		});
		$("toa-add-confirm").addEventListener("click", () => {
			const qty = parseInt($("toa-add-qty").textContent) || 1;
			const note = $("toa-add-note").value.trim();
			$("toa-add-modal").style.display = "none";
			this.doAddItem(this._pendingItem, qty, note);
		});

		// Covers modal
		$("toa-covers-cancel").addEventListener("click", () => {
			$("toa-covers-modal").style.display = "none";
			this.table = null;
		});
		$("toa-covers-ok").addEventListener("click", () => {
			const covers = parseInt($("toa-covers-inp").value) || 1;
			$("toa-covers-modal").style.display = "none";
			this.createOrder(covers);
		});
	}

	// ─── Outlets ──────────────────────────────────────────────────────────────
	loadOutlets() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_outlets",
			callback: (r) => {
				const sel = document.getElementById("toa-outlet-sel");
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
		this.loadTables();
		this.loadMenu();
	}

	refresh() {
		if (this.outlet) {
			this.loadTables();
			if (this.order) this.loadPendingItems();
		}
	}

	// ─── Tables ───────────────────────────────────────────────────────────────
	loadTables() {
		frappe.call({
			method: "hospitality.restaurant.page.table_order.table_order.get_steward_tables",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.tables = r.message || [];
				this.renderTableGrid();
			},
		});
	}

	renderTableGrid() {
		const grid = document.getElementById("toa-tables-grid");
		const tables = this.tables || [];

		if (!tables.length) {
			grid.innerHTML = `<div class="toa-empty" style="grid-column:1/-1">
				<div class="toa-empty-icon">🪑</div><div>No tables found</div>
			</div>`;
			return;
		}

		grid.innerHTML = tables.map((t) => {
			const st = (t.current_status || "Available").toLowerCase().replace(" ", "-");
			const cls = { available: "available", occupied: "occupied", reserved: "reserved",
				dirty: "dirty", blocked: "blocked" }[st] || "available";
			const totalHtml = t.order_total
				? `<div class="toa-ttot">${frappe.format(t.order_total, { fieldtype: "Currency" })}</div>` : "";
			return `<div class="toa-table-card ${cls}" data-table="${t.name}" data-status="${cls}">
				<div class="toa-tnum">${t.table_number}</div>
				<div class="toa-tcap">cap ${t.seating_capacity}</div>
				${totalHtml}
			</div>`;
		}).join("");

		grid.querySelectorAll(".toa-table-card").forEach((card) => {
			card.addEventListener("click", () => {
				const st = card.dataset.status;
				if (st === "blocked" || st === "dirty") return;
				this.selectTable(card.dataset.table, st);
			});
		});
	}

	selectTable(tableName, statusClass) {
		this.table = tableName;
		const t = (this.tables || []).find((x) => x.name === tableName);
		document.getElementById("toa-order-title").textContent =
			`Table ${t ? t.table_number : tableName}`;

		if (statusClass === "occupied") {
			this.loadActiveOrder();
		} else {
			document.getElementById("toa-covers-inp").value = 2;
			document.getElementById("toa-covers-modal").style.display = "flex";
		}
	}

	showTablesView() {
		document.getElementById("toa-tables-view").style.display = "flex";
		document.getElementById("toa-order-view").style.display = "none";
		this.table = null;
		this.order = null;
		this.pendingItems = [];
		this.loadTables();
	}

	showOrderView() {
		document.getElementById("toa-tables-view").style.display = "none";
		document.getElementById("toa-order-view").style.display = "flex";
		// Switch to menu tab
		document.querySelectorAll(".toa-tab").forEach((t) => t.classList.remove("active"));
		document.getElementById("toa-tab-menu").classList.add("active");
		document.getElementById("toa-menu-sub").style.display = "flex";
		document.getElementById("toa-order-sub").style.display = "none";
	}

	// ─── Order ────────────────────────────────────────────────────────────────
	loadActiveOrder() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_active_order",
			args: { table: this.table },
			callback: (r) => {
				if (r.message) {
					this.order = r.message.name;
					document.getElementById("toa-order-ref").textContent = this.order;
					this.showOrderView();
					this.loadPendingItems();
				} else {
					this.showOrderView();
					this.order = null;
				}
			},
		});
	}

	createOrder(covers) {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.new_order",
			args: { outlet: this.outlet, table: this.table, covers },
			callback: (r) => {
				this.order = r.message;
				document.getElementById("toa-order-ref").textContent = this.order;
				this.showOrderView();
				this.toast("Order opened", "success");
			},
		});
	}

	loadPendingItems() {
		if (!this.order) return;
		frappe.call({
			method: "hospitality.restaurant.page.table_order.table_order.get_pending_items",
			args: { order: this.order },
			callback: (r) => {
				this.pendingItems = r.message || [];
				this.updatePendingBadge();
				document.getElementById("toa-btn-kot").disabled = this.pendingItems.length === 0;
			},
		});
	}

	updatePendingBadge() {
		const badge = document.getElementById("toa-pending-count");
		const count = this.pendingItems.length;
		badge.style.display = count > 0 ? "inline" : "none";
		badge.textContent = count;
	}

	// ─── Menu ─────────────────────────────────────────────────────────────────
	loadMenu() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_menu_categories",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.categories = r.message || [];
				this.renderCategories();
			},
		});
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_menu_items",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.allMenuItems = r.message || [];
				this.renderItemList();
			},
		});
	}

	renderCategories() {
		const bar = document.getElementById("toa-cats");
		bar.innerHTML =
			`<button class="toa-cat-btn active" data-cat="All">All</button>` +
			this.categories.map((c) => `<button class="toa-cat-btn" data-cat="${c}">${c}</button>`).join("");
	}

	renderItemList() {
		const list = document.getElementById("toa-item-list");
		const stationEmoji = { "Hot Kitchen": "🔥", "Cold Kitchen": "🧊", Grill: "🥩", Tandoor: "🫙", Desserts: "🍮", Bar: "🍹" };

		let items = this.allMenuItems;
		if (this.activeCategory !== "All") items = items.filter((i) => i.category === this.activeCategory);
		if (this.searchQuery) items = items.filter((i) => i.item_name.toLowerCase().includes(this.searchQuery));

		if (!items.length) {
			list.innerHTML = `<div class="toa-empty"><div class="toa-empty-icon">🔍</div><div>No items</div></div>`;
			return;
		}

		list.innerHTML = items.map((item) => {
			const dim = !item.is_available ? ' style="opacity:.4;pointer-events:none"' : "";
			return `<div class="toa-item-row" data-item="${item.name}"${dim}>
				<div class="toa-item-emoji">${stationEmoji[item.kitchen_station] || "🍽️"}</div>
				<div class="toa-item-info">
					<div class="toa-item-name">${item.item_name}</div>
					<div class="toa-item-station">${item.kitchen_station || item.category || ""}</div>
				</div>
				<div class="toa-item-price">${frappe.format(item.selling_price, { fieldtype: "Currency" })}</div>
				<button class="toa-item-add" data-item="${item.name}">+</button>
			</div>`;
		}).join("");

		list.querySelectorAll(".toa-item-add").forEach((btn) => {
			btn.addEventListener("click", (e) => {
				e.stopPropagation();
				if (!this.order) {
					this.toast("Open an order first", "error");
					return;
				}
				const itemName = btn.dataset.item;
				const row = list.querySelector(`[data-item="${itemName}"] .toa-item-name`);
				this._pendingItem = itemName;
				document.getElementById("toa-add-item-name").textContent =
					row ? row.textContent : "Add Item";
				document.getElementById("toa-add-qty").textContent = "1";
				document.getElementById("toa-add-note").value = "";
				document.getElementById("toa-add-modal").style.display = "flex";
			});
		});
	}

	// ─── Add Item ─────────────────────────────────────────────────────────────
	doAddItem(menuItem, qty, note) {
		this._pendingItem = null;
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.add_item",
			args: { order: this.order, menu_item: menuItem, qty, special_instructions: note },
			callback: () => {
				this.loadPendingItems();
				this.toast("Item added", "success");
			},
		});
	}

	// ─── Kitchen Status ───────────────────────────────────────────────────────
	loadOrderStatus() {
		if (!this.order) {
			document.getElementById("toa-order-items-list").innerHTML =
				`<div class="toa-empty"><div class="toa-empty-icon">🛒</div><div>No active order</div></div>`;
			return;
		}

		frappe.call({
			method: "hospitality.restaurant.page.table_order.table_order.get_sent_items",
			args: { order: this.order },
			callback: (r) => {
				const sentItems = r.message || [];
				const pending = this.pendingItems || [];
				this.renderOrderStatus(pending, sentItems);
			},
		});
	}

	renderOrderStatus(pending, sent) {
		const container = document.getElementById("toa-order-items-list");
		let html = "";

		if (pending.length) {
			html += `<div class="toa-ord-section">Pending (not sent yet)</div>`;
			html += pending.map((item) => `
				<div class="toa-ord-row">
					<div class="toa-ord-name">${item.item_name}
						${item.special_instructions ? `<div class="toa-ord-note">${item.special_instructions}</div>` : ""}
					</div>
					<div class="toa-ord-qty">×${item.qty}</div>
					<div class="toa-ord-amt">${frappe.format(item.amount, { fieldtype: "Currency" })}</div>
					<span class="toa-ord-status pending">Pending</span>
				</div>`).join("");
		}

		if (sent.length) {
			html += `<div class="toa-ord-section">In Kitchen</div>`;
			html += sent.map((item) => {
				const cls = {
					"In Preparation": "in-prep",
					Ready: "ready",
					Served: "served",
				}[item.status] || "pending";
				const serveBtn = item.status === "Ready"
					? `<button class="toa-serve-btn" data-row="${item.name}">Served</button>` : "";
				return `<div class="toa-ord-row">
					<div class="toa-ord-name">${item.item_name}</div>
					<div class="toa-ord-qty">×${item.qty}</div>
					<div class="toa-ord-amt">${frappe.format(item.amount, { fieldtype: "Currency" })}</div>
					${serveBtn}
					<span class="toa-ord-status ${cls}">${item.status}</span>
				</div>`;
			}).join("");
		}

		if (!pending.length && !sent.length) {
			html = `<div class="toa-empty"><div class="toa-empty-icon">🛒</div><div>No items yet</div></div>`;
		}

		container.innerHTML = html;

		container.querySelectorAll(".toa-serve-btn").forEach((btn) => {
			btn.addEventListener("click", () => {
				frappe.call({
					method: "hospitality.restaurant.page.table_order.table_order.mark_served",
					args: { order: this.order, row_name: btn.dataset.row },
					callback: () => {
						this.toast("Marked as served", "success");
						this.loadOrderStatus();
					},
				});
			});
		});
	}

	// ─── Fire KOT ────────────────────────────────────────────────────────────
	fireKOT() {
		if (!this.order || !this.pendingItems.length) return;
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.fire_kot",
			args: { order: this.order },
			callback: () => {
				this.toast(`KOT fired 🔥 — ${this.pendingItems.length} item(s) sent to kitchen`, "success");
				this.pendingItems = [];
				this.updatePendingBadge();
				document.getElementById("toa-btn-kot").disabled = true;
			},
		});
	}

	// ─── Toast ────────────────────────────────────────────────────────────────
	toast(msg, type = "info") {
		const t = document.createElement("div");
		t.className = `toa-toast ${type}`;
		t.textContent = msg;
		document.body.appendChild(t);
		setTimeout(() => t.remove(), 3000);
	}
}
