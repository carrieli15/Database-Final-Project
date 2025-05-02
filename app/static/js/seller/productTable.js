// static/js/productTable.js

// Class to handle product management table operations
class ProductTable {
  constructor(allProducts) {
    this.allProducts = allProducts;
    this.currentPage = 1;
    this.itemsPerPage = 10;
    this.init();
  }

  // Initialize event listeners and table rendering
  init() {
    this.setupEventListeners();
    this.renderTable();
  }

  // Set up all necessary event listeners
  setupEventListeners() {
    // Search input listener
    document.getElementById('search-input').addEventListener('input', () => {
      this.currentPage = 1;
      this.renderTable();
    });

    // Click event listener on table for edit and delete actions
    document.getElementById('product-table-body').addEventListener('click', e => {
      const row = e.target.closest('tr');
      if (!row) return;

      const id = row.querySelector('td:nth-child(1)').textContent.trim();

      if (e.target.classList.contains('edit-btn')) {
        const product = this.allProducts.find(p => String(p.id) === String(id));
        if (product) window.app.openEditModal(product);
      }

      if (e.target.classList.contains('delete-btn')) {
        const name = row.querySelector('td:nth-child(2)').textContent.trim();
        // Show custom modal
        this.showDeleteModal(id, name);
      }
    });

    // Modal cancel button for delete confirmation
    document.getElementById('cancel-delete').addEventListener('click', () => {
      document.getElementById('delete-modal-overlay').style.display = 'none';
    });

    // Modal confirm delete button
    document.getElementById('confirm-delete').addEventListener('click', () => {
      if (this.pendingDeleteId) {
        this.handleDeleteProduct(this.pendingDeleteId);
        document.getElementById('delete-modal-overlay').style.display = 'none';
      }
    });
  }

  // Render the main product table
  renderTable() {
    const filtered = this.filterProducts();
    const paginated = this.paginate(filtered);
    this.buildTable(paginated);
    this.renderPagination(filtered.length);
  }

  // Filter products based on search input
  filterProducts() {
    const keyword = document.getElementById('search-input').value.toLowerCase();
    return this.allProducts.filter(p =>
      p.name.toLowerCase().includes(keyword) ||
      String(p.id).includes(keyword)
    );
  }

  // Paginate products based on current page and items per page
  paginate(data) {
    const start = (this.currentPage - 1) * this.itemsPerPage;
    return data.slice(start, start + this.itemsPerPage);
  }

  // Build the table rows for the current product list
  buildTable(products) {
    const tbody = document.getElementById('product-table-body');
    tbody.innerHTML = products.map(p => `
        <tr>
          <td>${p.id}</td>
          <td>${p.name}</td>
          <td>${p.category}</td>
          <td>
            ${p.stock}
            ${(p.low_stock_quantity && p.stock < p.low_stock_quantity) ? this.lowStockSVG() : ''}
          </td>
          <td>${p.price}</td>
          <td>
            <span class="status-label ${p.status.toLowerCase().replace(' ', '-')}">
              ${p.status}
            </span>
          </td>
          <td>${p.date_added}</td>
          <td>
            <span class="edit-btn">✏️</span>
            <span class="delete-btn">🗑️</span>
          </td>
        </tr>
      `).join('');
  }

  // Return an SVG badge for low stock
  lowStockSVG() {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="22" style="vertical-align: middle; margin-left: 6px;">
        <rect x="0" y="0" width="40" height="22" rx="11" ry="11" fill="#dc3545"/>
        <text x="20" y="15" text-anchor="middle" font-size="12" fill="white" font-weight="bold" font-family="Arial">Low</text>
      </svg>`;
  }

  // Render pagination buttons based on the number of filtered items
  renderPagination(totalItems) {
    const totalPages = Math.ceil(totalItems / this.itemsPerPage);
    const container = document.getElementById('pagination');
    container.innerHTML = Array.from({ length: totalPages }, (_, i) => i + 1)
      .map(page => `<button onclick="productTable.currentPage = ${page}; productTable.renderTable()">${page}</button>`)
      .join('');
  }

  // Send a request to the server to delete a product
  handleDeleteProduct(id) {
    fetch('/seller/delete_product', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id })
    })
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          // remove from local
          this.allProducts = this.allProducts.filter(p => String(p.id) !== String(id));
          window.productsData = this.allProducts; // global update

          this.renderTable();
        } else {
          alert("Failed to delete product.");
        }
      })
      .catch(err => {
        console.error("Delete failed:", err);
        alert("Error deleting product.");
      });
  }

  // Show the delete confirmation modal
  showDeleteModal(id, name) {
    this.pendingDeleteId = id;
    document.getElementById('delete-modal-message').textContent =
      `Are you sure you want to delete "${name}" (ID: ${id})?`;
    document.getElementById('delete-modal-overlay').style.display = 'flex';
  }

}