// Suyog Textile - Client Store Engine (Cart, Wishlist, WhatsApp Ordering, Search)

const Store = {
  // ─── CART ENGINE ───
  getCart() {
    try {
      return JSON.parse(localStorage.getItem('suyog_cart')) || [];
    } catch (e) {
      return [];
    }
  },

  saveCart(cart) {
    localStorage.setItem('suyog_cart', JSON.stringify(cart));
    this.updateCartBadges();
    this.renderDrawerCart();
  },

  addToCart(productId, size = null, color = null, quantity = 1) {
    const product = PRODUCTS_DATA.find(p => p.id === Number(productId));
    if (!product) return;

    const chosenSize = size || (product.sizes && product.sizes[0]) || "Standard";
    const chosenColor = color || (product.colors && product.colors[0]) || "Default";

    const cart = this.getCart();
    const existingIndex = cart.findIndex(item => 
      item.id === product.id && item.size === chosenSize && item.color === chosenColor
    );

    if (existingIndex > -1) {
      cart[existingIndex].quantity += quantity;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        price: product.price,
        originalPrice: product.originalPrice,
        image: product.primaryImage,
        size: chosenSize,
        color: chosenColor,
        quantity: quantity,
        category: product.category
      });
    }

    this.saveCart(cart);
    this.showToast(`✨ Added "${product.name}" to your bag!`);
    this.openCartDrawer();
  },

  updateQuantity(index, newQty) {
    const cart = this.getCart();
    if (newQty <= 0) {
      cart.splice(index, 1);
    } else {
      cart[index].quantity = newQty;
    }
    this.saveCart(cart);
    if (typeof renderCartPage === 'function') renderCartPage();
    if (typeof renderCheckoutSummary === 'function') renderCheckoutSummary();
  },

  removeFromCart(index) {
    const cart = this.getCart();
    const removed = cart.splice(index, 1)[0];
    this.saveCart(cart);
    if (removed) {
      this.showToast(`Removed "${removed.name}" from bag`);
    }
    if (typeof renderCartPage === 'function') renderCartPage();
    if (typeof renderCheckoutSummary === 'function') renderCheckoutSummary();
  },

  clearCart() {
    localStorage.removeItem('suyog_cart');
    this.updateCartBadges();
    this.renderDrawerCart();
  },

  getCartTotals() {
    const cart = this.getCart();
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const originalSubtotal = cart.reduce((sum, item) => sum + (item.originalPrice * item.quantity), 0);
    const savings = Math.max(0, originalSubtotal - subtotal);
    const shipping = subtotal >= STORE_CONFIG.freeShippingThreshold || subtotal === 0 ? 0 : STORE_CONFIG.standardShippingFee;
    
    // Apply coupon if any
    const couponCode = localStorage.getItem('suyog_coupon');
    let discount = 0;
    let appliedCoupon = null;

    if (couponCode && STORE_CONFIG.coupons[couponCode]) {
      const c = STORE_CONFIG.coupons[couponCode];
      if (subtotal >= c.minOrder) {
        if (c.type === 'percent') {
          discount = Math.round((subtotal * c.value) / 100);
        } else if (c.type === 'flat') {
          discount = c.value;
        }
        appliedCoupon = { code: couponCode, discount };
      }
    }

    const total = Math.max(0, subtotal - discount + shipping);

    return {
      subtotal,
      savings,
      shipping,
      discount,
      appliedCoupon,
      total,
      itemCount: cart.reduce((cnt, item) => cnt + item.quantity, 0)
    };
  },

  applyCoupon(code) {
    const cleanCode = code.trim().toUpperCase();
    const coupon = STORE_CONFIG.coupons[cleanCode];
    if (!coupon) {
      this.showToast("❌ Invalid coupon code. Try WELCOME10 or FESTIVE20", "error");
      return false;
    }
    const totals = this.getCartTotals();
    if (totals.subtotal < coupon.minOrder) {
      this.showToast(`⚠️ Minimum cart value ₹${coupon.minOrder} required for ${cleanCode}`, "error");
      return false;
    }

    localStorage.setItem('suyog_coupon', cleanCode);
    this.showToast(`🎉 Coupon ${cleanCode} applied successfully!`);
    if (typeof renderCartPage === 'function') renderCartPage();
    if (typeof renderCheckoutSummary === 'function') renderCheckoutSummary();
    this.renderDrawerCart();
    return true;
  },

  removeCoupon() {
    localStorage.removeItem('suyog_coupon');
    this.showToast("Coupon removed");
    if (typeof renderCartPage === 'function') renderCartPage();
    if (typeof renderCheckoutSummary === 'function') renderCheckoutSummary();
    this.renderDrawerCart();
  },

  // ─── WISHLIST ENGINE ───
  getWishlist() {
    try {
      return JSON.parse(localStorage.getItem('suyog_wishlist')) || [];
    } catch (e) {
      return [];
    }
  },

  toggleWishlist(productId) {
    let list = this.getWishlist();
    const id = Number(productId);
    const index = list.indexOf(id);
    let added = false;
    if (index > -1) {
      list.splice(index, 1);
      this.showToast("Removed from wishlist");
    } else {
      list.push(id);
      added = true;
      this.showToast("❤️ Saved to your wishlist!");
    }
    localStorage.setItem('suyog_wishlist', JSON.stringify(list));
    this.updateWishlistBadges();
    
    // Update button icons on page
    document.querySelectorAll(`[data-wishlist-id="${id}"]`).forEach(btn => {
      btn.classList.toggle('active', added);
    });
    return added;
  },

  isWishlisted(productId) {
    return this.getWishlist().includes(Number(productId));
  },

  // ─── BADGES & UI HELPERS ───
  updateCartBadges() {
    const count = this.getCart().reduce((sum, item) => sum + item.quantity, 0);
    document.querySelectorAll('.cart-count-badge').forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-flex' : 'none';
    });
  },

  updateWishlistBadges() {
    const count = this.getWishlist().length;
    document.querySelectorAll('.wishlist-count-badge').forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-flex' : 'none';
    });
  },

  // ─── DRAWER CART ───
  initDrawer() {
    if (document.getElementById('cartDrawerOverlay')) return;

    const drawerHTML = `
      <div id="cartDrawerOverlay" class="cart-drawer-overlay" onclick="Store.closeCartDrawer()"></div>
      <div id="cartDrawer" class="cart-drawer">
        <div class="cart-drawer-header">
          <div class="drawer-title">
            <span class="bag-icon">🛍️</span>
            <h3>Shopping Bag (<span class="drawer-items-count">0</span>)</h3>
          </div>
          <button class="drawer-close-btn" onclick="Store.closeCartDrawer()" aria-label="Close bag">&times;</button>
        </div>

        <div id="cartDrawerItems" class="cart-drawer-items">
          <!-- Items injected here -->
        </div>

        <div class="cart-drawer-footer" id="cartDrawerFooter">
          <div class="free-shipping-bar" id="freeShippingBar"></div>
          <div class="drawer-totals">
            <div class="drawer-total-row">
              <span>Subtotal</span>
              <strong id="drawerSubtotal">₹0</strong>
            </div>
            <p class="drawer-tax-note">Taxes included. Free shipping on orders over ₹${STORE_CONFIG.freeShippingThreshold}.</p>
          </div>
          <div class="drawer-actions">
            <a href="checkout.html" class="btn btn-primary btn-block">Proceed to Checkout &rarr;</a>
            <a href="cart.html" class="btn btn-outline btn-block">View Full Bag</a>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML('beforeend', drawerHTML);
    this.renderDrawerCart();
  },

  openCartDrawer() {
    this.initDrawer();
    const overlay = document.getElementById('cartDrawerOverlay');
    const drawer = document.getElementById('cartDrawer');
    if (overlay && drawer) {
      overlay.classList.add('active');
      drawer.classList.add('active');
      document.body.style.overflow = 'hidden';
      this.renderDrawerCart();
    }
  },

  closeCartDrawer() {
    const overlay = document.getElementById('cartDrawerOverlay');
    const drawer = document.getElementById('cartDrawer');
    if (overlay && drawer) {
      overlay.classList.remove('active');
      drawer.classList.remove('active');
      document.body.style.overflow = '';
    }
  },

  renderDrawerCart() {
    const container = document.getElementById('cartDrawerItems');
    const footer = document.getElementById('cartDrawerFooter');
    if (!container) return;

    const cart = this.getCart();
    const totals = this.getCartTotals();

    document.querySelectorAll('.drawer-items-count').forEach(el => el.textContent = totals.itemCount);

    if (cart.length === 0) {
      container.innerHTML = `
        <div class="drawer-empty-state">
          <span class="empty-icon">🪷</span>
          <h4>Your bag is empty</h4>
          <p>Discover our heirloom sarees, lehengas, and designer ethnic wear.</p>
          <a href="shop.html" class="btn btn-primary btn-sm" onclick="Store.closeCartDrawer()">Explore Catalog</a>
        </div>
      `;
      if (footer) footer.style.display = 'none';
      return;
    }

    if (footer) footer.style.display = 'block';

    // Free shipping bar calculation
    const progressEl = document.getElementById('freeShippingBar');
    if (progressEl) {
      if (totals.subtotal >= STORE_CONFIG.freeShippingThreshold) {
        progressEl.innerHTML = `
          <div class="shipping-success">🎉 Congratulations! You have qualified for <strong>FREE Delivery</strong></div>
        `;
      } else {
        const remaining = STORE_CONFIG.freeShippingThreshold - totals.subtotal;
        const pct = Math.min(100, Math.round((totals.subtotal / STORE_CONFIG.freeShippingThreshold) * 100));
        progressEl.innerHTML = `
          <div class="shipping-progress-text">Add <strong>₹${remaining}</strong> more for FREE Delivery!</div>
          <div class="shipping-progress-track">
            <div class="shipping-progress-fill" style="width: ${pct}%"></div>
          </div>
        `;
      }
    }

    const drawerSubtotal = document.getElementById('drawerSubtotal');
    if (drawerSubtotal) {
      drawerSubtotal.textContent = `₹${totals.subtotal.toLocaleString('en-IN')}`;
    }

    container.innerHTML = cart.map((item, idx) => `
      <div class="drawer-item">
        <img src="${item.image}" alt="${item.name}" class="drawer-item-img">
        <div class="drawer-item-info">
          <h4 class="drawer-item-name">${item.name}</h4>
          <div class="drawer-item-meta">
            <span>Size: ${item.size}</span> | <span>Color: ${item.color}</span>
          </div>
          <div class="drawer-item-price">
            <strong>₹${item.price.toLocaleString('en-IN')}</strong>
            <span class="original-strike">₹${item.originalPrice.toLocaleString('en-IN')}</span>
          </div>
          <div class="drawer-item-controls">
            <div class="qty-stepper">
              <button onclick="Store.updateQuantity(${idx}, ${item.quantity - 1})">-</button>
              <span>${item.quantity}</span>
              <button onclick="Store.updateQuantity(${idx}, ${item.quantity + 1})">+</button>
            </div>
            <button class="drawer-remove-btn" onclick="Store.removeFromCart(${idx})" title="Remove item">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path></svg>
              Remove
            </button>
          </div>
        </div>
      </div>
    `).join('');
  },

  // ─── WHATSAPP INTEGRATION ───
  orderViaWhatsApp(customOrder = null) {
    const cart = customOrder ? [customOrder] : this.getCart();
    if (cart.length === 0) {
      this.showToast("Your cart is empty!", "error");
      return;
    }

    const totals = this.getCartTotals();
    let message = `*Namaste Suyog Textile!* 🙏\n`;
    message += `I would like to place an order from your online store *${STORE_CONFIG.domain}*:\n\n`;

    cart.forEach((item, i) => {
      message += `*${i + 1}. ${item.name}*\n`;
      message += `   • Size: ${item.size}\n`;
      message += `   • Color: ${item.color}\n`;
      message += `   • Qty: ${item.quantity} × ₹${item.price.toLocaleString('en-IN')}\n\n`;
    });

    message += `───────────────────\n`;
    message += `*Subtotal:* ₹${totals.subtotal.toLocaleString('en-IN')}\n`;
    if (totals.discount > 0) {
      message += `*Discount (${totals.appliedCoupon.code}):* -₹${totals.discount.toLocaleString('en-IN')}\n`;
    }
    message += `*Shipping:* ${totals.shipping === 0 ? 'FREE' : '₹' + totals.shipping}\n`;
    message += `*Grand Total:* *₹${totals.total.toLocaleString('en-IN')}*\n`;
    message += `───────────────────\n\n`;
    message += `Please confirm product availability and delivery timeline. Thank you!`;

    const encoded = encodeURIComponent(message);
    const url = `https://wa.me/${STORE_CONFIG.whatsappNumber.replace(/[^0-9]/g, '')}?text=${encoded}`;
    window.open(url, '_blank');
  },

  inquireProductWhatsApp(productId) {
    const product = PRODUCTS_DATA.find(p => p.id === Number(productId));
    if (!product) return;

    let message = `*Namaste Suyog Textile!* 🙏\n`;
    message += `I am interested in this piece from your collection:\n\n`;
    message += `*${product.name}*\n`;
    message += `• Price: ₹${product.price.toLocaleString('en-IN')} (MRP ₹${product.originalPrice.toLocaleString('en-IN')})\n`;
    message += `• Fabric: ${product.fabric}\n`;
    message += `• Occasion: ${product.occasion}\n`;
    message += `• Link: https://${STORE_CONFIG.domain}/product.html?id=${product.id}\n\n`;
    message += `Could you please share more pictures, video call view, or delivery details?`;

    const encoded = encodeURIComponent(message);
    const url = `https://wa.me/${STORE_CONFIG.whatsappNumber.replace(/[^0-9]/g, '')}?text=${encoded}`;
    window.open(url, '_blank');
  },

  // ─── TOAST NOTIFICATION ───
  showToast(message, type = "success") {
    let container = document.getElementById('suyogToastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'suyogToastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">${message}</div>
      <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;

    container.appendChild(toast);
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => toast.remove(), 400);
    }, 3500);
  },

  // ─── SEARCH AUTOCOMPLETE ───
  initSearchAutocomplete() {
    ['search-input', 'mobile-search-input'].forEach(id => {
      const input = document.getElementById(id);
      if (!input) return;

      let box = document.getElementById(id + '-results');
      if (!box) {
        box = document.createElement('div');
        box.id = id + '-results';
        box.className = 'search-suggestions-dropdown';
        box.style.cssText = 'position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid #E5E7EB;border-radius:8px;box-shadow:0 10px 25px rgba(0,0,0,0.15);z-index:999;max-height:360px;overflow-y:auto;display:none;';
        if (input.parentElement) {
          input.parentElement.style.position = 'relative';
          input.parentElement.appendChild(box);
        }
      }

      input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (query.length < 2) {
          box.style.display = 'none';
          return;
        }

        const matches = PRODUCTS_DATA.filter(p => 
          p.name.toLowerCase().includes(query) || 
          p.fabric.toLowerCase().includes(query) || 
          p.categoryName.toLowerCase().includes(query)
        ).slice(0, 5);

        if (matches.length === 0) {
          box.innerHTML = '<div style="padding:14px;text-align:center;color:#888;font-size:0.85rem;">No matching ethnic wear found</div>';
          box.style.display = 'block';
          return;
        }

        box.innerHTML = matches.map(p => `
          <a href="product.html?id=${p.id}" style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid #f3f3f3;text-decoration:none;color:#1C1917;">
            <img src="${p.primaryImage}" style="width:40px;height:50px;object-fit:cover;border-radius:4px;">
            <div style="flex-grow:1;font-size:0.85rem;">
              <div style="font-weight:600;line-height:1.2;">${p.name}</div>
              <div style="font-size:0.75rem;color:#666;">${p.categoryName} • ${p.fabric}</div>
            </div>
            <strong style="color:var(--primary);font-size:0.85rem;">₹${p.price.toLocaleString('en-IN')}</strong>
          </a>
        `).join('') + `
          <a href="shop.html?q=${encodeURIComponent(query)}" style="display:block;padding:10px;text-align:center;background:#FAF8F5;color:var(--primary);font-weight:700;font-size:0.8rem;text-decoration:none;">
            View all results for "${query}" &rarr;
          </a>
        `;
        box.style.display = 'block';
      });

      document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !box.contains(e.target)) {
          box.style.display = 'none';
        }
      });
    });
  },

  // ─── INIT ───
  init() {
    this.updateCartBadges();
    this.updateWishlistBadges();
    this.initDrawer();
    this.initSearchAutocomplete();
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Store.init();
});

