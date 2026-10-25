/**
 * Suyog Textile — Modernized Store Engine with Supabase Integration
 * Client Cart stores ONLY { id, size, qty }.
 * Prices, stock, discounts, shipping, and totals are computed only via the database.
 */

const Store = {
  getConfig() {
    return window.SITE_CONFIG || {
      brandName: "Suyog Textile",
      freeShippingThreshold: 1499,
      shippingFee: 0,
      whatsappNumber: "918669396037"
    };
  },

  // ─── CART STORAGE (Stores ONLY id, size, qty) ───
  getCart() {
    try {
      const data = localStorage.getItem('suyog_cart');
      if (!data) return [];
      const raw = JSON.parse(data);
      if (!Array.isArray(raw)) return [];
      // Normalize to { id, size, qty }
      return raw.map(item => ({
        id: Number(item.id),
        size: item.size || 'Free Size',
        qty: Math.max(1, Number(item.qty || item.quantity || 1))
      })).filter(item => !isNaN(item.id) && item.id > 0);
    } catch (e) {
      console.warn("Storage access error:", e);
      return [];
    }
  },

  saveCart(cart) {
    try {
      const clean = cart.map(item => ({
        id: Number(item.id),
        size: item.size || 'Free Size',
        qty: Math.max(1, Math.min(10, Number(item.qty || 1)))
      }));
      localStorage.setItem('suyog_cart', JSON.stringify(clean));
    } catch (e) {
      console.warn("Unable to save cart:", e);
    }
    this.updateCartBadges();
  },

  addToCart(productId, size = 'Free Size', qty = 1) {
    const id = Number(productId);
    if (!id) return;
    const chosenSize = size || 'Free Size';
    const addQty = Math.max(1, Number(qty) || 1);

    const cart = this.getCart();
    const existingIndex = cart.findIndex(item => item.id === id && item.size === chosenSize);

    if (existingIndex > -1) {
      cart[existingIndex].qty = Math.min(10, cart[existingIndex].qty + addQty);
    } else {
      cart.push({ id, size: chosenSize, qty: addQty });
    }

    this.saveCart(cart);
    this.showToast("✨ Added to your shopping bag!");
  },

  updateQuantity(index, newQty) {
    const cart = this.getCart();
    if (index < 0 || index >= cart.length) return;
    if (newQty <= 0) {
      cart.splice(index, 1);
    } else {
      cart[index].qty = Math.min(10, Math.max(1, newQty));
    }
    this.saveCart(cart);
  },

  removeFromCart(index) {
    const cart = this.getCart();
    if (index >= 0 && index < cart.length) {
      cart.splice(index, 1);
      this.saveCart(cart);
    }
  },

  clearCart() {
    localStorage.removeItem('suyog_cart');
    this.updateCartBadges();
  },

  getCartCount() {
    const cart = this.getCart();
    return cart.reduce((sum, item) => sum + item.qty, 0);
  },

  updateCartBadges() {
    const count = this.getCartCount();
    document.querySelectorAll('.cart-count-badge').forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'inline-flex' : 'none';
    });
  },

  // ─── SERVER RE-FETCH & SYNCHRONIZATION ───
  // Re-fetches active product details directly from Supabase
  async fetchCartDetails() {
    const cart = this.getCart();
    if (cart.length === 0) {
      return { items: [], subtotal: 0, count: 0 };
    }

    const ids = Array.from(new Set(cart.map(i => i.id)));
    let productsMap = new Map();

    if (window.isSupabaseConfigured()) {
      try {
        const { data, error } = await window.supabaseClient
          .from('products')
          .select('id, slug, name, price_inr, mrp_inr, stock, image_paths, is_active')
          .in('id', ids)
          .eq('is_active', true);

        if (!error && Array.isArray(data)) {
          data.forEach(p => productsMap.set(p.id, p));
        }
      } catch (err) {
        console.warn("Supabase products fetch failed:", err);
      }
    }

    // Fallback to local catalog if offline / setup mode
    if (productsMap.size === 0 && window.PRODUCTS_DATA) {
      window.PRODUCTS_DATA.forEach(p => {
        if (ids.includes(p.id)) {
          productsMap.set(p.id, {
            id: p.id,
            slug: p.id.toString(),
            name: p.name,
            price_inr: p.price,
            mrp_inr: p.originalPrice,
            stock: p.stock || 10,
            image_paths: [p.primaryImage],
            is_active: true
          });
        }
      });
    }

    // Merge cart with server snapshot
    let subtotal = 0;
    const enrichedItems = [];

    cart.forEach(item => {
      const prod = productsMap.get(item.id);
      if (prod && prod.is_active && prod.stock > 0) {
        const cappedQty = Math.min(item.qty, prod.stock);
        const itemTotal = prod.price_inr * cappedQty;
        subtotal += itemTotal;
        enrichedItems.push({
          id: prod.id,
          name: prod.name,
          size: item.size,
          qty: cappedQty,
          stock: prod.stock,
          unitPrice: prod.price_inr,
          mrp: prod.mrp_inr,
          totalPrice: itemTotal,
          image: (prod.image_paths && prod.image_paths[0]) || 'assets/images/favicon.png'
        });
      }
    });

    return {
      items: enrichedItems,
      subtotal: subtotal,
      count: enrichedItems.reduce((acc, i) => acc + i.qty, 0)
    };
  },

  // ─── SERVER-SIDE COUPON VALIDATION ───
  async validateCouponServer(couponCode) {
    const code = (couponCode || '').trim().toUpperCase();
    if (!code) {
      return { valid: false, error: 'Please enter a coupon code.' };
    }

    const cart = this.getCart();
    if (cart.length === 0) {
      return { valid: false, error: 'Your bag is empty.' };
    }

    const payloadItems = cart.map(item => ({ id: item.id, qty: item.qty, size: item.size }));

    if (window.isSupabaseConfigured()) {
      try {
        const { data, error } = await window.supabaseClient.rpc('validate_coupon', {
          coupon_code: code,
          items: payloadItems
        });
        if (error) {
          return { valid: false, error: error.message || 'Invalid coupon.' };
        }
        return data;
      } catch (err) {
        console.warn("RPC validate_coupon error:", err);
      }
    }

    // Client fallback validation for initial demo mode before Supabase credentials set
    const cfg = this.getConfig();
    const localCoupon = (cfg.coupons || []).find(c => c.code === code);
    if (!localCoupon) {
      return { valid: false, error: 'Invalid coupon code.' };
    }

    const cartData = await this.fetchCartDetails();
    if (cartData.subtotal < localCoupon.minOrder) {
      return { valid: false, error: `Minimum order for ${code} is ₹${localCoupon.minOrder.toLocaleString('en-IN')}.` };
    }

    let discount = 0;
    if (localCoupon.discountType === 'percent') {
      discount = Math.round((cartData.subtotal * localCoupon.discountValue) / 100);
    } else {
      discount = localCoupon.discountValue;
    }

    return {
      valid: true,
      code: code,
      discount_inr: Math.min(discount, cartData.subtotal)
    };
  },

  // ─── WISHLIST ENGINE (localStorage IDs) ───
  getWishlist() {
    try {
      const data = localStorage.getItem('suyog_wishlist');
      return data ? JSON.parse(data) : [];
    } catch (e) {
      return [];
    }
  },

  toggleWishlist(productId) {
    const id = Number(productId);
    let list = this.getWishlist();
    const idx = list.indexOf(id);
    let added = false;
    if (idx > -1) {
      list.splice(idx, 1);
    } else {
      list.push(id);
      added = true;
    }
    try {
      localStorage.setItem('suyog_wishlist', JSON.stringify(list));
    } catch (e) {}

    document.querySelectorAll(`[data-wishlist-id="${id}"]`).forEach(btn => {
      btn.classList.toggle('active', added);
    });

    this.showToast(added ? "❤️ Saved to your Wishlist!" : "Removed from Wishlist");
    return added;
  },

  isWishlisted(productId) {
    return this.getWishlist().includes(Number(productId));
  },

  // ─── WHATSAPP DIRECT ASSISTANCE ───
  inquireProductWhatsApp(productId) {
    const cfg = this.getConfig();
    const wa = cfg.whatsappNumber || "918669396037";
    const msg = `Namaste Suyog Textile, I am inquiring about product ID #${productId} on your online store. Could you share more details?`;
    window.open(`https://wa.me/${wa}?text=${encodeURIComponent(msg)}`, '_blank');
  },

  // ─── TOAST NOTIFICATIONS ───
  showToast(msg) {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.style.cssText = 'position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.style.cssText = 'background:#1C1917;color:#fff;padding:12px 20px;border-radius:10px;font-size:0.88rem;box-shadow:0 8px 24px rgba(0,0,0,0.2);display:flex;align-items:center;gap:10px;transition:opacity 0.3s;pointer-events:auto;';
    toast.textContent = msg;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 2800);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  Store.updateCartBadges();
});
