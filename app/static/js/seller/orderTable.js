// static/js/seller/orderTable.js

class OrderTable {
    constructor(allOrders) {
        this.allOrders = allOrders;
        this.currentPage = 1;
        this.itemsPerPage = 10;
        this.pendingFulfillId = null;
        this.init();
    }

    // Initialize table with event listeners and initial render
    init() {
        this.setupEventListeners();
        this.renderTable();
    }

    // Bind events for search, filter, fulfill, delete
    setupEventListeners() {
        document.getElementById('search-input').addEventListener('input', () => {
            this.currentPage = 1;
            this.renderTable();
        });

        document.getElementById('status-filter')?.addEventListener('change', () => {
            this.currentPage = 1;
            this.renderTable();
        });

        document.getElementById('order-table-body').addEventListener('click', e => {
            const row = e.target.closest('tr');

            if (e.target.classList.contains('edit-btn')) {
                const id = row.querySelector('td:nth-child(3)').textContent.trim(); // order_item_id
                this.showFulfillModal(id);
            }

            if (e.target.classList.contains('delete-btn')) {
                const id = row.querySelector('td:nth-child(3)').textContent.trim(); // order_item_id
                const name = row.querySelector('td:nth-child(5)').textContent.trim();
                this.showDeleteModal(id, name);
            }
        });

        document.getElementById('cancel-delete').addEventListener('click', () => {
            document.getElementById('delete-modal-overlay').style.display = 'none';
        });

        document.getElementById('cancel-fulfill').addEventListener('click', () => {
            document.getElementById('fulfill-modal-overlay').style.display = 'none';
        });

        document.getElementById('confirm-delete').addEventListener('click', () => {
            if (this.pendingDeleteId) {
                this.handleDelete(this.pendingDeleteId);
                document.getElementById('delete-modal-overlay').style.display = 'none';
            }
        });

        document.getElementById('confirm-fulfill').addEventListener('click', () => {
            if (this.pendingFulfillId) {
                this.handleFulfill(this.pendingFulfillId);
                document.getElementById('fulfill-modal-overlay').style.display = 'none';
            }
        });
    }

    // Filter orders by search keyword and status
    filterOrders() {
        const keyword = document.getElementById('search-input').value.toLowerCase();
        const status = document.getElementById('status-filter')?.value.toLowerCase();

        return this.allOrders.filter(o => {
            const matchesOrder = String(o.order_id).toLowerCase().includes(keyword);
            const matchesStatus = !status || (o.status && o.status.toLowerCase() === status);
            return matchesOrder && matchesStatus;
        });
    }

    // Paginate orders
    paginate(data) {
        const start = (this.currentPage - 1) * this.itemsPerPage;
        return data.slice(start, start + this.itemsPerPage);
    }

    // Build table HTML based on grouped orders
    buildTable(orders) {
        const tbody = document.getElementById('order-table-body');
        tbody.innerHTML = '';

        const grouped = {};
        for (const o of orders) {
            if (!grouped[o.order_id]) {
                grouped[o.order_id] = [];
            }
            grouped[o.order_id].push(o);
        }

        for (const orderId in grouped) {
            const items = grouped[orderId];
            const firstItem = items[0];

            // Create expandable summary row
            const summaryRow = document.createElement('tr');
            summaryRow.classList.add('order-summary-row', `order-summary-${orderId}`);
            summaryRow.style.display = 'none';
            summaryRow.innerHTML = `
                <td colspan="11" style="padding: 12px 15px; font-style: italic;">
                    <strong>Buyer:</strong> ${firstItem.buyer_name || 'N/A'} &nbsp;|&nbsp;
                    <strong>Address:</strong> ${firstItem.buyer_address || 'N/A'} &nbsp;|&nbsp;
                    <strong>Ordered:</strong> ${firstItem.updated_at}
                </td>
            `;
            tbody.appendChild(summaryRow);

            // Create order item rows
            items.forEach((o, index) => {
                const row = document.createElement('tr');
                row.classList.add(`order-row-${orderId}`);
                row.innerHTML = `
                    <td style="text-align: center;">${index === 0 ?
                        `<span class="order-toggle" data-order="${orderId}" style="cursor:pointer;">▶️</span>` :
                        ''}</td>
                    <td>${o.order_id}</td>
                    <td>${o.order_item_id}</td>
                    <td>${o.product_id}</td>
                    <td>${o.product_name}</td>
                    <td style="text-align: center;">${o.quantity}</td>
                    <td style="text-align: right;">${o.unit_price}</td>
                    <td style="text-align: right;">${o.total_price}</td>
                    <td>
                      <span class="status-label ${o.status ? o.status.toLowerCase().trim() : 'pending'}">
                        ${o.status || 'Pending'}
                      </span>
                    </td>
                    <td>${o.updated_at}</td>
                    <td style="text-align: center;">
                        <span class="edit-btn">✏️</span>
                        <span class="delete-btn">🗑️</span>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }

        // Bind collapse/expand toggle
        document.querySelectorAll('.order-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                const orderId = btn.dataset.order;
                const summaryRow = document.querySelector(`.order-summary-${orderId}`);
                const isHidden = summaryRow.style.display === 'none';
                summaryRow.style.display = isHidden ? 'table-row' : 'none';
                btn.textContent = isHidden ? '🔽' : '▶️';

                const itemRows = document.querySelectorAll(`.order-row-${orderId}`);
                itemRows.forEach(row => {
                    if (isHidden) {
                        row.classList.add('expanded-row');
                    } else {
                        row.classList.remove('expanded-row');
                    }
                });

                if (isHidden) {
                    summaryRow.classList.add('show');
                } else {
                    summaryRow.classList.remove('show');
                }

            });
        });
    }

    // Render pagination buttons
    renderPagination(totalItems) {
        const totalPages = Math.ceil(totalItems / this.itemsPerPage);
        const container = document.getElementById('pagination');
        container.innerHTML = Array.from({ length: totalPages }, (_, i) => i + 1)
            .map(page => `
          <button onclick="orderTable.currentPage = ${page}; orderTable.renderTable()">
            ${page}
          </button>`).join('');
    }

    // Render the entire order table
    renderTable() {
        const filtered = this.filterOrders();
        const paginated = this.paginate(filtered);
        this.buildTable(paginated);
        this.renderPagination(filtered.length);
    }

    // Show delete confirmation modal
    showDeleteModal(id, name) {
        this.pendingDeleteId = id;
        document.getElementById('delete-modal-message').textContent =
            `Are you sure you want to delete Order Item ${id}?`;
        document.getElementById('delete-modal-overlay').style.display = 'flex';
    }

    // Show fulfill confirmation modal
    showFulfillModal(id) {
        this.pendingFulfillId = id;
        document.getElementById('fulfill-modal-message').textContent =
            `Are you sure you want to mark this Order Item ${id} as fulfilled?`;
        document.getElementById('fulfill-modal-overlay').style.display = 'flex';
    }

    // Handle delete action
    handleDelete(id) {
        fetch('/seller/delete_order_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        })
            .then(res => res.json())
            .then(result => {
                if (result.success) {
                    this.allOrders = this.allOrders.filter(o => String(o.order_item_id) !== String(id));
                    this.renderTable();
                } else {
                    alert('Failed to delete item');
                }
            });
    }

    // Handle fulfill action
    handleFulfill(id) {
        fetch('/seller/fulfill_order_item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id })
        })
            .then(res => res.json())
            .then(result => {
                if (result.success) {
                    this.allOrders = this.allOrders.map(o =>
                        String(o.order_item_id) === String(id) ? { ...o, status: 'Fulfilled' } : o
                    );

                    this.renderTable(); // render
                } else {
                    alert('Error marking as fulfilled.');
                }
            })
            .catch(() => alert('Error marking as fulfilled.'));
    }

}