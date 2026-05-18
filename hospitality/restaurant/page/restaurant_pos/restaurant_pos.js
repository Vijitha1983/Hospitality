frappe.pages["restaurant-pos"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: "Restaurant POS",
		single_column: true,
	});
	wrapper.rpos = new RestaurantPOS(wrapper);
};

frappe.pages["restaurant-pos"].on_page_show = function (wrapper) {
	if (wrapper.rpos) wrapper.rpos.refresh();
};

class RestaurantPOS {
	constructor(wrapper) {
		this.wrapper = wrapper;
		this.page = wrapper.page;

		// State
		this.outlet = null;
		this.table = null;
		this.order = null;
		this.orderItems = [];
		this.paymentModes = [];
		this.categories = [];
		this.allMenuItems = [];
		this.activeCategory = "All";
		this.searchQuery = "";

		this.page.main.css({ padding: 0, overflow: "hidden" });
		this.render();
		this.loadOutlets();
		this.startClock();
	}

	// ─── Render skeleton ──────────────────────────────────────────────────────
	render() {
		this.page.main.html(`
<div class="rpos-wrap">
  <!-- Header -->
  <div class="rpos-header">
    <div class="rpos-logo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/>
        <line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/>
      </svg>
      Restaurant POS
    </div>
    <div class="rpos-header-center">
      <select class="rpos-select" id="rpos-outlet-sel">
        <option value="">— Select Outlet —</option>
      </select>
    </div>
    <div class="rpos-header-right">
      <span class="rpos-status-dot green" id="rpos-dot"></span>
      <span class="rpos-badge" id="rpos-outlet-badge">No Outlet</span>
      <span class="rpos-clock" id="rpos-clock"></span>
    </div>
  </div>

  <!-- Body -->
  <div class="rpos-body">

    <!-- LEFT: Floor Plan -->
    <div class="rpos-floor">
      <div class="rpos-panel-header">
        <span>Floor Plan</span>
        <span id="rpos-table-count" style="font-size:11px;color:var(--pos-text-dim)"></span>
      </div>
      <div class="rpos-table-grid" id="rpos-table-grid">
        <div class="rpos-order-empty" style="grid-column:1/-1">
          <div class="rpos-order-empty-icon">🏠</div>
          <div>Select an outlet</div>
        </div>
      </div>
      <div class="rpos-floor-actions">
        <button class="rpos-btn rpos-btn-new-order" id="rpos-refresh-tables">⟳ Refresh Tables</button>
      </div>
    </div>

    <!-- CENTER: Menu -->
    <div class="rpos-menu">
      <div class="rpos-categories" id="rpos-categories"></div>
      <div class="rpos-search-bar">
        <input class="rpos-search-input" id="rpos-search" placeholder="Search menu items…" type="text" />
      </div>
      <div class="rpos-menu-grid" id="rpos-menu-grid">
        <div class="rpos-order-empty" style="grid-column:1/-1">
          <div class="rpos-order-empty-icon">🍽️</div>
          <div>Select a table to start ordering</div>
        </div>
      </div>
    </div>

    <!-- RIGHT: Order Panel -->
    <div class="rpos-order">
      <div class="rpos-order-head">
        <div class="rpos-order-table-label">Current Order</div>
        <div class="rpos-order-table-name" id="rpos-order-table">No Table</div>
        <div class="rpos-order-meta" id="rpos-order-meta"></div>
      </div>

      <div class="rpos-order-items" id="rpos-order-items">
        <div class="rpos-order-empty">
          <div class="rpos-order-empty-icon">🛒</div>
          <div>Order is empty</div>
        </div>
      </div>

      <div class="rpos-totals" id="rpos-totals" style="display:none">
        <div class="rpos-total-row"><span>Subtotal</span><span id="rpos-subtotal">0.00</span></div>
        <div class="rpos-total-row"><span>Tax</span><span id="rpos-tax">0.00</span></div>
        <div class="rpos-total-row grand"><span>TOTAL</span><span id="rpos-total">0.00</span></div>
      </div>

      <div class="rpos-actions">
        <button class="rpos-btn rpos-btn-kot" id="rpos-btn-kot" disabled>
          🔥 Fire KOT
        </button>
        <button class="rpos-btn rpos-btn-bill" id="rpos-btn-bill" disabled>
          💳 Charge &amp; Bill
        </button>
        <button class="rpos-btn rpos-btn-void" id="rpos-btn-void" disabled>
          ✕ Void Order
        </button>
      </div>
    </div>
  </div>
</div>

<!-- Payment Modal -->
<div class="rpos-modal-overlay" id="rpos-pay-modal" style="display:none">
  <div class="rpos-modal">
    <div class="rpos-modal-title">💳 Collect Payment</div>
    <div class="rpos-modal-amount" id="rpos-pay-amount">0.00</div>
    <div class="rpos-pay-methods" id="rpos-pay-methods"></div>
    <div style="margin-bottom:8px;font-size:11px;color:var(--pos-text-muted)">TIP</div>
    <div class="rpos-tip-row" id="rpos-tip-row">
      <button class="rpos-tip-btn" data-pct="0">No Tip</button>
      <button class="rpos-tip-btn" data-pct="5">5%</button>
      <button class="rpos-tip-btn" data-pct="10">10%</button>
      <button class="rpos-tip-btn" data-pct="15">15%</button>
    </div>
    <div class="rpos-modal-actions">
      <button class="rpos-modal-cancel" id="rpos-pay-cancel">Cancel</button>
      <button class="rpos-modal-confirm" id="rpos-pay-confirm">Confirm Payment</button>
    </div>
  </div>
</div>

<!-- Covers Dialog -->
<div class="rpos-modal-overlay" id="rpos-covers-modal" style="display:none">
  <div class="rpos-modal" style="width:300px">
    <div class="rpos-modal-title">👥 Number of Covers</div>
    <input class="rpos-modal-input" id="rpos-covers-input" type="number" min="1" max="20" value="2" />
    <div class="rpos-modal-actions">
      <button class="rpos-modal-cancel" id="rpos-covers-cancel">Cancel</button>
      <button class="rpos-modal-confirm" id="rpos-covers-confirm">Open Order</button>
    </div>
  </div>
</div>

<!-- Special Instructions Dialog -->
<div class="rpos-modal-overlay" id="rpos-note-modal" style="display:none">
  <div class="rpos-modal" style="width:340px">
    <div class="rpos-modal-title">📝 Special Instructions</div>
    <textarea class="rpos-note-input" id="rpos-note-input" placeholder="e.g. No spice, extra sauce…"></textarea>
    <div class="rpos-modal-actions">
      <button class="rpos-modal-cancel" id="rpos-note-cancel">Skip</button>
      <button class="rpos-modal-confirm" id="rpos-note-confirm">Add Item</button>
    </div>
  </div>
</div>
`);
		this.bindStaticEvents();
	}

	// ─── Static event bindings ────────────────────────────────────────────────
	bindStaticEvents() {
		const $ = (id) => document.getElementById(id);

		// Outlet selector
		$("rpos-outlet-sel").addEventListener("change", (e) => {
			this.selectOutlet(e.target.value);
		});

		// Refresh tables
		$("rpos-refresh-tables").addEventListener("click", () => {
			if (this.outlet) this.loadTables();
		});

		// Category filter
		document.getElementById("rpos-categories").addEventListener("click", (e) => {
			const btn = e.target.closest(".rpos-cat-btn");
			if (!btn) return;
			this.activeCategory = btn.dataset.cat;
			document.querySelectorAll(".rpos-cat-btn").forEach((b) => b.classList.remove("active"));
			btn.classList.add("active");
			this.renderMenuGrid();
		});

		// Search
		$("rpos-search").addEventListener("input", (e) => {
			this.searchQuery = e.target.value.toLowerCase();
			this.renderMenuGrid();
		});

		// KOT button
		$("rpos-btn-kot").addEventListener("click", () => this.fireKOT());

		// Bill button
		$("rpos-btn-bill").addEventListener("click", () => this.openPayModal());

		// Void button
		$("rpos-btn-void").addEventListener("click", () => this.voidOrder());

		// Payment modal
		$("rpos-pay-cancel").addEventListener("click", () => this.closePayModal());
		$("rpos-pay-confirm").addEventListener("click", () => this.confirmPayment());

		// Tip buttons
		document.getElementById("rpos-tip-row").addEventListener("click", (e) => {
			const btn = e.target.closest(".rpos-tip-btn");
			if (!btn) return;
			document.querySelectorAll(".rpos-tip-btn").forEach((b) => b.classList.remove("selected"));
			btn.classList.add("selected");
			this._tipPct = parseInt(btn.dataset.pct);
		});

		// Covers modal
		$("rpos-covers-cancel").addEventListener("click", () => {
			$("rpos-covers-modal").style.display = "none";
			this.table = null;
		});
		$("rpos-covers-confirm").addEventListener("click", () => {
			const covers = parseInt($("rpos-covers-input").value) || 1;
			$("rpos-covers-modal").style.display = "none";
			this.createOrder(covers);
		});

		// Note modal
		$("rpos-note-cancel").addEventListener("click", () => {
			$("rpos-note-modal").style.display = "none";
			if (this._pendingItem) this.doAddItem(this._pendingItem, 1, "");
		});
		$("rpos-note-confirm").addEventListener("click", () => {
			const note = $("rpos-note-input").value.trim();
			$("rpos-note-modal").style.display = "none";
			if (this._pendingItem) this.doAddItem(this._pendingItem, 1, note);
		});
	}

	// ─── Clock ────────────────────────────────────────────────────────────────
	startClock() {
		const el = document.getElementById("rpos-clock");
		const tick = () => {
			const now = new Date();
			el.textContent = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
		};
		tick();
		setInterval(tick, 1000);
	}

	// ─── Outlets ──────────────────────────────────────────────────────────────
	loadOutlets() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_outlets",
			callback: (r) => {
				const sel = document.getElementById("rpos-outlet-sel");
				(r.message || []).forEach((o) => {
					const opt = document.createElement("option");
					opt.value = o.name;
					opt.textContent = o.outlet_name;
					sel.appendChild(opt);
				});
				// Auto-select if only one outlet
				if (r.message && r.message.length === 1) {
					sel.value = r.message[0].name;
					this.selectOutlet(r.message[0].name);
				}
			},
		});
	}

	selectOutlet(outletName) {
		if (!outletName) return;
		this.outlet = outletName;
		document.getElementById("rpos-outlet-badge").textContent = outletName;
		this.loadTables();
		this.loadMenu();
		this.loadPaymentModes();
	}

	refresh() {
		if (this.outlet) {
			this.loadTables();
			if (this.order) this.loadActiveOrder();
		}
	}

	// ─── Tables ───────────────────────────────────────────────────────────────
	loadTables() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_tables",
			args: { outlet: this.outlet },
			callback: (r) => {
				this.tables = r.message || [];
				this.renderTableGrid();
			},
		});
	}

	renderTableGrid() {
		const grid = document.getElementById("rpos-table-grid");
		const count = document.getElementById("rpos-table-count");
		const tables = this.tables || [];

		count.textContent = `${tables.length} tables`;

		if (!tables.length) {
			grid.innerHTML = `<div class="rpos-order-empty" style="grid-column:1/-1">
				<div class="rpos-order-empty-icon">🪑</div>
				<div>No tables configured</div>
			</div>`;
			return;
		}

		grid.innerHTML = tables
			.map((t) => {
				const st = (t.current_status || "Available").toLowerCase().replace(" ", "-");
				const stClass =
					{
						available: "available",
						occupied: "occupied",
						reserved: "reserved",
						dirty: "dirty",
						blocked: "blocked",
					}[st] || "available";

				const selected = this.table === t.name ? " selected" : "";
				const totalHtml = t.current_order
					? `<span class="rpos-table-total" id="ttot-${t.name}"></span>`
					: "";

				return `<button class="rpos-table-btn ${stClass}${selected}" data-table="${t.name}" data-status="${stClass}" title="${t.current_status}">
					<span class="rpos-table-name">${t.table_number}</span>
					<span class="rpos-table-covers">cap ${t.seating_capacity}</span>
					${totalHtml}
				</button>`;
			})
			.join("");

		grid.addEventListener(
			"click",
			(e) => {
				const btn = e.target.closest(".rpos-table-btn");
				if (!btn || btn.dataset.status === "blocked") return;
				this.selectTable(btn.dataset.table, btn.dataset.status);
			},
			{ once: true }
		);

		// Re-bind (remove once limitation by replacing the grid's listener each render)
		this._bindTableGrid();
	}

	_bindTableGrid() {
		const grid = document.getElementById("rpos-table-grid");
		if (this._tableGridListener) grid.removeEventListener("click", this._tableGridListener);
		this._tableGridListener = (e) => {
			const btn = e.target.closest(".rpos-table-btn");
			if (!btn || btn.dataset.status === "blocked") return;
			this.selectTable(btn.dataset.table, btn.dataset.status);
		};
		grid.addEventListener("click", this._tableGridListener);
	}

	selectTable(tableName, statusClass) {
		this.table = tableName;

		// Highlight selected
		document.querySelectorAll(".rpos-table-btn").forEach((b) => b.classList.remove("selected"));
		const btn = document.querySelector(`[data-table="${tableName}"]`);
		if (btn) btn.classList.add("selected");

		document.getElementById("rpos-order-table").textContent =
			btn ? btn.querySelector(".rpos-table-name").textContent : tableName;

		if (statusClass === "occupied") {
			this.loadActiveOrder();
		} else if (statusClass === "dirty") {
			this.toast("Table is dirty — needs cleaning before new order.", "error");
			this.clearOrderPanel();
		} else {
			// Prompt for covers then create order
			document.getElementById("rpos-covers-input").value = 2;
			document.getElementById("rpos-covers-modal").style.display = "flex";
		}
	}

	// ─── Order Management ─────────────────────────────────────────────────────
	loadActiveOrder() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_active_order",
			args: { table: this.table },
			callback: (r) => {
				if (r.message) {
					this.order = r.message.name;
					this.orderItems = r.message.items || [];
					this._subTotal = r.message.sub_total || 0;
					this._tax = r.message.tax_amount || 0;
					this._total = r.message.total_amount || 0;
					document.getElementById("rpos-order-meta").textContent =
						`Order: ${this.order} | ${r.message.num_covers} cover(s)`;
					this.renderOrderPanel();
				} else {
					this.clearOrderPanel();
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
				this.orderItems = [];
				this._subTotal = 0;
				this._tax = 0;
				this._total = 0;
				document.getElementById("rpos-order-meta").textContent =
					`Order: ${this.order} | ${covers} cover(s)`;
				this.renderOrderPanel();
				this.loadTables();
				this.toast("Order opened", "success");
			},
		});
	}

	clearOrderPanel() {
		this.order = null;
		this.orderItems = [];
		document.getElementById("rpos-order-meta").textContent = "";
		document.getElementById("rpos-order-items").innerHTML = `
			<div class="rpos-order-empty">
				<div class="rpos-order-empty-icon">🛒</div>
				<div>Order is empty</div>
			</div>`;
		document.getElementById("rpos-totals").style.display = "none";
		["rpos-btn-kot", "rpos-btn-bill", "rpos-btn-void"].forEach((id) => {
			document.getElementById(id).disabled = true;
		});
	}

	renderOrderPanel() {
		const container = document.getElementById("rpos-order-items");
		const totalsEl = document.getElementById("rpos-totals");

		if (!this.orderItems.length) {
			container.innerHTML = `<div class="rpos-order-empty">
				<div class="rpos-order-empty-icon">🛒</div>
				<div>Order is empty</div>
			</div>`;
			totalsEl.style.display = "none";
		} else {
			container.innerHTML = this.orderItems
				.map(
					(item) => `
				<div class="rpos-order-item" data-row="${item.name}">
					<div>
						<div class="rpos-oi-name">${item.item_name}</div>
						${item.special_instructions ? `<div class="rpos-oi-note">${item.special_instructions}</div>` : ""}
					</div>
					<div class="rpos-qty-ctrl">
						<button class="rpos-qty-btn" data-action="dec" data-row="${item.name}">−</button>
						<span class="rpos-qty-val">${item.qty}</span>
						<button class="rpos-qty-btn" data-action="inc" data-row="${item.name}" data-menu="${item.menu_item}">+</button>
					</div>
					<div class="rpos-oi-amount">${frappe.format(item.amount, { fieldtype: "Currency" })}</div>
					<button class="rpos-oi-remove" data-row="${item.name}" title="Remove">✕</button>
				</div>`
				)
				.join("");

			// Bind row events
			container.querySelectorAll(".rpos-qty-btn").forEach((btn) => {
				btn.addEventListener("click", (e) => {
					e.stopPropagation();
					const row = btn.dataset.row;
					const item = this.orderItems.find((i) => i.name === row);
					if (!item) return;
					const newQty = btn.dataset.action === "inc" ? item.qty + 1 : item.qty - 1;
					this.updateQty(row, newQty);
				});
			});

			container.querySelectorAll(".rpos-oi-remove").forEach((btn) => {
				btn.addEventListener("click", (e) => {
					e.stopPropagation();
					this.removeItem(btn.dataset.row);
				});
			});

			// Recalc totals
			const sub = this.orderItems.reduce((s, i) => s + (i.amount || 0), 0);
			this._subTotal = sub;
			// Tax from server values if available, else estimate
			const tax = this._tax || 0;
			const total = sub + tax;

			document.getElementById("rpos-subtotal").textContent = frappe.format(sub, { fieldtype: "Currency" });
			document.getElementById("rpos-tax").textContent = frappe.format(tax, { fieldtype: "Currency" });
			document.getElementById("rpos-total").textContent = frappe.format(total, { fieldtype: "Currency" });
			totalsEl.style.display = "flex";
		}

		// Button states
		const hasItems = this.orderItems.length > 0;
		document.getElementById("rpos-btn-kot").disabled = !hasItems;
		document.getElementById("rpos-btn-bill").disabled = !hasItems;
		document.getElementById("rpos-btn-void").disabled = !this.order;
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
				this.renderMenuGrid();
			},
		});
	}

	renderCategories() {
		const bar = document.getElementById("rpos-categories");
		bar.innerHTML =
			`<button class="rpos-cat-btn active" data-cat="All">All</button>` +
			this.categories.map((c) => `<button class="rpos-cat-btn" data-cat="${c}">${c}</button>`).join("");
	}

	renderMenuGrid() {
		const grid = document.getElementById("rpos-menu-grid");
		let items = this.allMenuItems;

		if (this.activeCategory !== "All") {
			items = items.filter((i) => i.category === this.activeCategory);
		}
		if (this.searchQuery) {
			items = items.filter((i) => i.item_name.toLowerCase().includes(this.searchQuery));
		}

		if (!items.length) {
			grid.innerHTML = `<div class="rpos-order-empty" style="grid-column:1/-1">
				<div class="rpos-order-empty-icon">🔍</div>
				<div>No items found</div>
			</div>`;
			return;
		}

		const stationEmoji = {
			"Hot Kitchen": "🔥",
			"Cold Kitchen": "🧊",
			Grill: "🥩",
			Tandoor: "🫙",
			Desserts: "🍮",
			Bar: "🍹",
		};

		grid.innerHTML = items
			.map((item) => {
				const unavailable = !item.is_available ? ' style="opacity:0.4;pointer-events:none"' : "";
				const imgHtml = item.image
					? `<img class="rpos-item-img" src="${item.image}" alt="" />`
					: `<div class="rpos-item-img-placeholder">${stationEmoji[item.kitchen_station] || "🍽️"}</div>`;

				return `<div class="rpos-item-card" data-item="${item.name}"${unavailable}>
					${imgHtml}
					<div class="rpos-item-name">${item.item_name}</div>
					<div class="rpos-item-price">${frappe.format(item.selling_price, { fieldtype: "Currency" })}</div>
					<div class="rpos-item-station">${item.kitchen_station || ""}</div>
					${!item.is_available ? '<div style="font-size:9px;color:var(--pos-red);font-weight:700">86\'D</div>' : ""}
				</div>`;
			})
			.join("");

		grid.querySelectorAll(".rpos-item-card").forEach((card) => {
			card.addEventListener("click", () => {
				if (!this.order) {
					this.toast("Select a table first", "error");
					return;
				}
				this._pendingItem = card.dataset.item;
				document.getElementById("rpos-note-input").value = "";
				document.getElementById("rpos-note-modal").style.display = "flex";
				document.getElementById("rpos-note-input").focus();
			});
		});
	}

	// ─── Item Operations ──────────────────────────────────────────────────────
	doAddItem(menuItem, qty, note) {
		this._pendingItem = null;
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.add_item",
			args: { order: this.order, menu_item: menuItem, qty, special_instructions: note },
			callback: () => {
				this.loadActiveOrder();
				this.toast("Item added", "success");
			},
		});
	}

	removeItem(rowName) {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.remove_item",
			args: { order: this.order, row_name: rowName },
			callback: () => {
				this.loadActiveOrder();
			},
		});
	}

	updateQty(rowName, newQty) {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.update_qty",
			args: { order: this.order, row_name: rowName, qty: newQty },
			callback: () => {
				this.loadActiveOrder();
			},
		});
	}

	// ─── KOT ─────────────────────────────────────────────────────────────────
	fireKOT() {
		if (!this.order) return;
		frappe.confirm(
			`Fire KOT for <b>${document.getElementById("rpos-order-table").textContent}</b>?`,
			() => {
				frappe.call({
					method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.fire_kot",
					args: { order: this.order },
					callback: (r) => {
						this.toast("KOT fired — kitchen notified 🔥", "success");
						this.loadActiveOrder();
						this.loadTables();
					},
				});
			}
		);
	}

	// ─── Payment ──────────────────────────────────────────────────────────────
	loadPaymentModes() {
		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.get_payment_modes",
			callback: (r) => {
				this.paymentModes = r.message || [];
			},
		});
	}

	openPayModal() {
		if (!this.order) return;
		const total = (this._subTotal || 0) + (this._tax || 0);
		this._selectedPayMode = null;
		this._tipPct = 0;

		// Render payment method buttons
		const modesEl = document.getElementById("rpos-pay-methods");
		const modes =
			this.paymentModes.length > 0
				? this.paymentModes
				: [{ name: "Cash" }, { name: "Credit Card" }, { name: "UPI" }];

		modesEl.innerHTML = modes
			.slice(0, 6)
			.map((m) => `<button class="rpos-pay-btn" data-mode="${m.name}">${m.name}</button>`)
			.join("");

		modesEl.querySelectorAll(".rpos-pay-btn").forEach((btn) => {
			btn.addEventListener("click", () => {
				modesEl.querySelectorAll(".rpos-pay-btn").forEach((b) => b.classList.remove("selected"));
				btn.classList.add("selected");
				this._selectedPayMode = btn.dataset.mode;
			});
		});

		// Reset tip selection
		document.querySelectorAll(".rpos-tip-btn").forEach((b) => b.classList.remove("selected"));
		document.querySelector('.rpos-tip-btn[data-pct="0"]').classList.add("selected");

		document.getElementById("rpos-pay-amount").textContent = frappe.format(total, { fieldtype: "Currency" });
		document.getElementById("rpos-pay-modal").style.display = "flex";
	}

	closePayModal() {
		document.getElementById("rpos-pay-modal").style.display = "none";
	}

	confirmPayment() {
		if (!this._selectedPayMode) {
			this.toast("Select a payment method", "error");
			return;
		}
		const baseTotal = (this._subTotal || 0) + (this._tax || 0);
		const tip = baseTotal * (this._tipPct || 0) / 100;

		frappe.call({
			method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.process_payment",
			args: {
				order: this.order,
				amount: baseTotal,
				payment_method: this._selectedPayMode,
				tip,
			},
			callback: (r) => {
				this.closePayModal();
				this.toast(`Invoice ${r.message.invoice} created ✓`, "success");
				this.order = null;
				this.table = null;
				document.getElementById("rpos-order-table").textContent = "No Table";
				this.clearOrderPanel();
				this.loadTables();
			},
		});
	}

	// ─── Void ─────────────────────────────────────────────────────────────────
	voidOrder() {
		if (!this.order) return;
		frappe.confirm(
			`Void the entire order for <b>${document.getElementById("rpos-order-table").textContent}</b>? This cannot be undone.`,
			() => {
				frappe.call({
					method: "hospitality.restaurant.page.restaurant_pos.restaurant_pos.void_order",
					args: { order: this.order, reason: "Voided from POS" },
					callback: () => {
						this.toast("Order voided", "info");
						this.order = null;
						this.table = null;
						document.getElementById("rpos-order-table").textContent = "No Table";
						this.clearOrderPanel();
						this.loadTables();
					},
				});
			}
		);
	}

	// ─── Toast ────────────────────────────────────────────────────────────────
	toast(msg, type = "info") {
		const t = document.createElement("div");
		t.className = `rpos-toast ${type}`;
		t.textContent = msg;
		document.body.appendChild(t);
		setTimeout(() => t.remove(), 3200);
	}
}
