// static/js/dashboard.js

// Global app object for managing dashboard functionalities
window.app = {
    init() {
        this.bindSectionSwitcher();
        this.initModal();
    },

    // Bind navigation links to switch dashboard sections
    bindSectionSwitcher() {
        const links = document.querySelectorAll('.nav-link');

        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.target.dataset.section;
                console.log('Switching to section:', section); // log
                this.showSection(section);
            });
        });
    },

    // Show selected section and hide others
    showSection(section) {
        document.getElementById('dashboard-section').style.display = section === 'dashboard' ? 'block' : 'none';
        document.getElementById('product-section').style.display = section === 'product' ? 'block' : 'none';
    },

    // Initialize add/edit product modal
    initModal() {
        const form = document.getElementById('product-form');
        if (form) {
            form.addEventListener('submit', async e => {
                e.preventDefault();

                // Get form values
                const name = document.getElementById('product-name').value.trim();
                const category = document.getElementById('product-category').value.trim();
                const stockRaw = document.getElementById('product-stock').value;
                const priceRaw = document.getElementById('product-price').value.trim();

                // Basic validation
                if (!name || !category || stockRaw === '' || isNaN(parseInt(stockRaw)) || !priceRaw || isNaN(parseFloat(priceRaw))) {
                    alert("Please fill in all required fields correctly.");
                    return;
                }

                const updated = {
                    id: document.getElementById('product-id').value,
                    name,
                    category,
                    stock: parseInt(stockRaw),
                    price: `$${parseFloat(priceRaw).toFixed(2)}`,
                    status: document.getElementById('product-status').value,
                    low_stock_quantity: parseInt(document.getElementById('product-lowStock').value) || 50
                };

                const isAdd = !updated.id;  // if id is none，treat as adding a new product

                try {
                    const res = await fetch(isAdd ? '/seller/add_product' : '/seller/update_product', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(isAdd ? {
                            name: updated.name,
                            category: updated.category,
                            stock: updated.stock,
                            price: updated.price,
                            status: updated.status,
                            low_stock_quantity: updated.low_stock_quantity
                        } : updated)  // update need id, add new product do not need id
                    });

                    const result = await res.json();
                    if (result.success) {
                        location.reload();
                    } else {
                        alert("Failed to " + (isAdd ? "add" : "update") + " product");
                    }
                } catch (error) {
                    console.error((isAdd ? "Add" : "Update") + " failed:", error);
                    alert("Error " + (isAdd ? "adding" : "updating") + " product");
                }
            });
        }
    },

    // Open modal with pre-filled data for editing an existing product
    openEditModal(product) {
        const requiredFields = ['id', 'name', 'category', 'stock', 'price', 'status'];
        if (!requiredFields.every(field => field in product)) {
            console.error('Invalid product data:', product);
            return;
        }

        document.getElementById('modal-title').textContent = 'Edit Product';
        document.getElementById('product-id').value = product.id;
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-category').value = product.category;
        document.getElementById('product-stock').value = product.stock;
        document.getElementById('product-lowStock').value = product.low_stock_quantity || 50;
        document.getElementById('product-price').value = product.price.replace('$', '');
        document.getElementById('product-status').value = product.status === "Draft" ? "Draft" : "Published";

        // display a modal with an overlay
        const overlay = document.getElementById('product-modal-overlay');
        overlay.style.display = 'flex';
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
        });
    },

    // Close the add/edit modal
    closeModal() {
        document.getElementById('product-modal-overlay').style.display = 'none';
    },

    // Open modal for adding a new product
    showAddProductForm() {
        document.getElementById('modal-title').textContent = 'Add Product';
        document.getElementById('product-id').value = '';
        document.getElementById('product-name').value = '';
        document.getElementById('product-category').value = '';
        document.getElementById('product-stock').value = '';
        document.getElementById('product-lowStock').value = '';
        document.getElementById('product-price').value = '';
        document.getElementById('product-status').value = 'Published';

        const overlay = document.getElementById('product-modal-overlay');
        overlay.style.display = 'flex';
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
        });
    }

};

// Allow modal to be closed externally
window.closeModal = window.app.closeModal.bind(window.app);