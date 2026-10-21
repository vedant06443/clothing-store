/**
 * Suyog Textile - Main JavaScript
 * Handles: cart, wishlist, search, product gallery, filters, notifications
 */

// ─── Local Storage + UI state ───────────────────────────────
const Storage = {
  get(key, fallback = null) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch {
      return false;
    }
  },
  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  }
};

const UIEnhancements = {
  init() {
    this.initializeThemePreference();
    this.initializeAOS();
    this.initializeSwiper();
    this.initializeWebSocket();
  },

  initializeThemePreference() {
    const stored = Storage.get('theme', 'light');
    document.documentElement.setAttribute('data-bs-theme', stored);
  },

  initializeAOS() {
    if (window.AOS) {
      AOS.init({
        duration: 700,
        easing: 'ease-out-cubic',
        once: true,
        offset: 24
      });
    }
  },

  initializeSwiper() {
    if (!window.Swiper) return;

    document.querySelectorAll('.swiper').forEach((swiperEl) => {
      const autoPlay = swiperEl.dataset.autoplay === 'true';
      new Swiper(swiperEl, {
        loop: true,
        slidesPerView: 1,
        spaceBetween: 18,
        autoplay: autoPlay ? { delay: 2500, disableOnInteraction: false } : false,
        pagination: {
          el: swiperEl.querySelector('.swiper-pagination'),
          clickable: true
        },
        navigation: {
          nextEl: swiperEl.querySelector('.swiper-button-next'),
          prevEl: swiperEl.querySelector('.swiper-button-prev')
        },
        breakpoints: {
          640: { slidesPerView: 2 },
          992: { slidesPerView: 3 }
        }
      });
    });
  },

  initializeWebSocket() {
    const wsUrl = document.body.dataset.wsUrl;
    if (!wsUrl || !('WebSocket' in window)) return;

    try {
      const socket = new WebSocket(wsUrl);
      socket.addEventListener('message', (event) => {
        const payload = JSON.parse(event.data || '{}');
        if (payload.stock_update) {
          Toast.info(`Stock update: ${payload.stock_update}`);
        }
      });
    } catch {
      // silently ignore unsupported WebSocket setup
    }
  }
};

// ─── Toast Notification System ───────────────────────────────
const Toast = {
  container: null,

  init() {
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.className = 'toast-container';
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },

  show(message, type = 'default', duration = 4000) {
    this.init();
    const icons = { success: '✓', error: '✕', warning: '⚠', default: '🛍' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || icons.default}</span>
      <span>${message}</span>
    `;
    this.container.appendChild(toast);
    setTimeout(() => toast.remove(), duration + 300);
  },

  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error'); },
  warning(msg) { this.show(msg, 'warning'); },
  info(msg) { this.show(msg, 'default'); }
};

// ─── API Helper ───────────────────────────────────────────────
const API = {
  async request(method, url, data = null) {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    };
    if (data) opts.body = JSON.stringify(data);
    const res = await fetch(url, opts);
    let json;
    try {
      json = await res.json();
    } catch {
      json = {};
    }
    if (!res.ok) {
      let msg = 'Something went wrong';
      if (typeof json.detail === 'string') {
        msg = json.detail;
      } else if (Array.isArray(json.detail)) {
        msg = json.detail.map(d => {
          if (typeof d === 'string') return d;
          const loc = d.loc ? d.loc.filter(l => l !== 'body').join('.') : '';
          return (loc ? loc + ': ' : '') + (d.msg || JSON.stringify(d));
        }).join('; ');
      } else if (json.message) {
        msg = json.message;
      }
      throw new Error(msg);
    }
    return json;
  },
  get: (url) => API.request('GET', url),
  post: (url, data) => API.request('POST', url, data),
  put: (url, data) => API.request('PUT', url, data),
  delete: (url) => API.request('DELETE', url)
};

// ─── Cart ─────────────────────────────────────────────────────
const Cart = {
  async add(productId, quantity = 1, color = null, size = null, overrideQuantity = false) {
    try {
      const data = { product_id: productId, quantity, color, size, override_quantity: overrideQuantity };
      const res = await API.post('/api/cart/add', data);
      Cart.updateCount(res.cart_count);
      Toast.success('Added to cart!');
      return true;
    } catch (err) {
      Toast.error(err.message);
      return false;
    }
  },

  async remove(itemId) {
    try {
      const res = await API.delete(`/api/cart/item/${itemId}`);
      Cart.updateCount(res.item_count);
      return res;
    } catch (err) {
      Toast.error(err.message);
    }
  },

  async updateQty(itemId, quantity) {
    try {
      const res = await API.put(`/api/cart/item/${itemId}`, { quantity });
      Cart.updateCount(res.item_count);
      return res;
    } catch (err) {
      Toast.error(err.message);
    }
  },

  updateCount(count) {
    document.querySelectorAll('.cart-count').forEach(el => {
      el.textContent = count;
      el.style.display = count > 0 ? 'flex' : 'none';
    });
  }
};

// ─── Wishlist ─────────────────────────────────────────────────
const Wishlist = {
  async toggle(productId, btn) {
    try {
      const res = await API.post(`/api/wishlist/toggle/${productId}`);
      const inWishlist = res.in_wishlist;
      if (btn) {
        btn.classList.toggle('active', inWishlist);
        btn.innerHTML = inWishlist ? '♥' : '♡';
        btn.title = inWishlist ? 'Remove from wishlist' : 'Add to wishlist';
      }
      // Update wishlist count
      const countEls = document.querySelectorAll('.wishlist-count');
      const res2 = await API.get('/api/wishlist/');
      countEls.forEach(el => el.textContent = res2.count);

      Toast.success(inWishlist ? 'Added to wishlist!' : 'Removed from wishlist');
      return inWishlist;
    } catch (err) {
      if (err.message.includes('401') || err.message.includes('authenticate')) {
        window.location.href = '/login?next=' + window.location.pathname;
      } else {
        Toast.error(err.message);
      }
    }
  }
};

// ─── Search ───────────────────────────────────────────────────
const Search = {
  timeout: null,

  init() {
    const input = document.getElementById('search-input');
    const suggestions = document.getElementById('search-suggestions');
    if (!input) return;

    input.addEventListener('input', () => {
      clearTimeout(this.timeout);
      const q = input.value.trim();
      if (q.length < 2) {
        suggestions?.classList.remove('show');
        return;
      }
      this.timeout = setTimeout(() => Search.fetchSuggestions(q, suggestions), 300);
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        window.location.href = `/search?q=${encodeURIComponent(input.value)}`;
      }
    });

    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !suggestions?.contains(e.target)) {
        suggestions?.classList.remove('show');
      }
    });
  },

  async fetchSuggestions(q, container) {
    try {
      const res = await API.get(`/api/products/search/suggestions?q=${encodeURIComponent(q)}`);
      if (!container) return;
      container.innerHTML = res.suggestions.map(s =>
        `<div class="suggestion-item" onclick="window.location.href='/search?q=${encodeURIComponent(s)}'">${s}</div>`
      ).join('');
      container.classList.toggle('show', res.suggestions.length > 0);
    } catch {}
  }
};

// ─── Product Gallery ──────────────────────────────────────────
const Gallery = {
  init() {
    const thumbs = document.querySelectorAll('.gallery-thumb');
    const mainImg = document.getElementById('gallery-main-img');
    if (!thumbs.length || !mainImg) return;

    thumbs.forEach(thumb => {
      thumb.addEventListener('click', () => {
        thumbs.forEach(t => t.classList.remove('active'));
        thumb.classList.add('active');
        mainImg.src = thumb.dataset.img;
      });
    });
  }
};

// ─── Product Detail ───────────────────────────────────────────
const ProductDetail = {
  selectedColor: null,
  selectedSize: null,

  init() {
    // Color selection
    document.querySelectorAll('.color-option').forEach(opt => {
      opt.addEventListener('click', () => {
        document.querySelectorAll('.color-option').forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');
        this.selectedColor = opt.dataset.color;
      });
    });

    // Size selection
    document.querySelectorAll('.size-option').forEach(opt => {
      opt.addEventListener('click', () => {
        document.querySelectorAll('.size-option').forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');
        this.selectedSize = opt.dataset.size;
      });
    });

    // Add to cart with double-click guard
    document.getElementById('add-to-cart-detail')?.addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      if (btn.disabled) return;
      const productId = parseInt(document.getElementById('product-id')?.value);
      const qtyInput = document.getElementById('pdp-quantity-input') || document.getElementById('quantity-input');
      const qty = parseInt(qtyInput?.value || 1);
      if (!productId || qty < 1) return;

      btn.disabled = true;
      const originalText = btn.innerHTML;
      btn.innerHTML = '⏳ Adding...';

      try {
        await Cart.add(productId, qty, this.selectedColor, this.selectedSize, true);
      } finally {
        setTimeout(() => {
          btn.disabled = false;
          btn.innerHTML = originalText;
        }, 600);
      }
    });

    // Buy now
    document.getElementById('buy-now-btn')?.addEventListener('click', async (e) => {
      const btn = e.currentTarget;
      if (btn.disabled) return;
      const productId = parseInt(document.getElementById('product-id')?.value);
      const qtyInput = document.getElementById('pdp-quantity-input') || document.getElementById('quantity-input');
      const qty = parseInt(qtyInput?.value || 1);
      if (!productId || qty < 1) return;

      btn.disabled = true;
      try {
        const success = await Cart.add(productId, qty, this.selectedColor, this.selectedSize, true);
        if (success) window.location.href = '/checkout';
      } finally {
        setTimeout(() => { btn.disabled = false; }, 800);
      }
    });
  }
};

// ─── Cart Page ────────────────────────────────────────────────
const CartPage = {
  init() {
    // Remove buttons
    document.querySelectorAll('.remove-cart-item').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const itemId = btn.dataset.itemId;
        if (!itemId) return;
        if (window.CartOps && typeof window.CartOps.removeItem === 'function') {
          await window.CartOps.removeItem(itemId);
        } else {
          const res = await Cart.remove(itemId);
          if (res !== undefined) {
            Toast.success('Item removed from shopping bag');
            window.location.reload();
          }
        }
      });
    });

    // Quantity update
    document.querySelectorAll('.cart-qty-input').forEach(input => {
      input.addEventListener('change', async () => {
        const itemId = input.dataset.itemId;
        const qty = parseInt(input.value);
        if (qty < 1) { input.value = 1; return; }
        const res = await Cart.updateQty(itemId, qty);
        if (res) CartPage.updateTotals(res);
      });
    });

    // Coupon
    document.getElementById('apply-coupon-btn')?.addEventListener('click', CartPage.applyCoupon);
  },

  updateTotals(res) {
    if (res.total !== undefined) {
      document.getElementById('cart-total')?.textContent && (
        document.getElementById('cart-total').textContent = `₹${res.total.toLocaleString('en-IN')}`
      );
    }
  },

  async applyCoupon() {
    const code = document.getElementById('coupon-code')?.value?.trim();
    const total = parseFloat(document.getElementById('cart-subtotal')?.dataset?.amount || 0);
    if (!code) return Toast.warning('Enter a coupon code');

    try {
      const res = await API.post('/api/orders/coupon/apply', { code, order_amount: total });
      Toast.success(`Coupon applied! You save ₹${res.discount}`);
      const discountEl = document.getElementById('discount-amount');
      if (discountEl) discountEl.textContent = `-₹${res.discount.toLocaleString('en-IN')}`;
    } catch (err) {
      Toast.error(err.message);
    }
  }
};

// ─── Checkout & Razorpay ──────────────────────────────────────
const Checkout = {
  selectedAddressId: null,
  couponDiscount: 0,
  couponCode: null,

  init() {
    // Address selection
    document.querySelectorAll('.address-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.address-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this.selectedAddressId = parseInt(card.dataset.addressId);
      });
      // Auto-select default
      if (card.dataset.isDefault === 'true') {
        card.classList.add('selected');
        this.selectedAddressId = parseInt(card.dataset.addressId);
      }
    });

    // Coupon
    document.getElementById('checkout-apply-coupon')?.addEventListener('click', this.applyCoupon.bind(this));

    // Payment buttons
    document.getElementById('pay-online-btn')?.addEventListener('click', () => this.placeOrder('Online'));
    document.getElementById('pay-cod-btn')?.addEventListener('click', () => this.placeOrder('COD'));
  },

  async applyCoupon() {
    const code = document.getElementById('checkout-coupon-input')?.value?.trim();
    const subtotal = parseFloat(document.getElementById('checkout-subtotal')?.dataset?.amount || 0);
    if (!code) return Toast.warning('Enter a coupon code');
    try {
      const res = await API.post('/api/orders/coupon/apply', { code, order_amount: subtotal });
      this.couponDiscount = res.discount;
      this.couponCode = res.code;
      Toast.success(`${res.code}: You save ₹${res.discount}!`);
      const discEl = document.getElementById('checkout-discount');
      if (discEl) discEl.textContent = `-₹${res.discount.toLocaleString('en-IN')}`;
    } catch (err) {
      Toast.error(err.message);
    }
  },

  async placeOrder(paymentMethod) {
    if (!this.selectedAddressId) {
      Toast.warning('Please select a delivery address');
      return;
    }

    const masterBtn = document.getElementById('master-place-order-btn');
    const btn = document.getElementById(`pay-${paymentMethod === 'Online' ? 'online' : 'cod'}-btn`);
    const setButtonsProcessing = (processing) => {
      if (masterBtn) {
        masterBtn.disabled = processing;
        masterBtn.textContent = processing ? 'Processing Payment...' : 'PLACE ORDER';
      }
      if (btn) {
        btn.disabled = processing;
        btn.textContent = processing ? 'Processing...' : (paymentMethod === 'Online' ? 'Pay Online' : 'Place Order (COD)');
      }
    };

    setButtonsProcessing(true);

    try {
      const res = await API.post('/api/orders/', {
        address_id: this.selectedAddressId,
        payment_method: paymentMethod,
        coupon_code: this.couponCode
      });

      if (paymentMethod === 'COD') {
        Toast.success('Order placed successfully! Pay cash upon delivery.');
        setTimeout(() => window.location.href = `/order-confirmation/${res.order_id}`, 1000);
        return;
      }

      // Online payment with Razorpay
      if (res.demo_mode || !res.razorpay_key) {
        // Demo / Mock mode — simulate online payment verification
        Toast.info('Demo Mode: Simulating secure payment verification...');
        await API.post(`/api/orders/${res.order_id}/payment/verify`, {
          razorpay_order_id: res.razorpay_order_id || `order_demo_${res.order_id}`,
          razorpay_payment_id: `pay_demo_${Date.now()}`,
          razorpay_signature: 'demo_sig'
        });
        Toast.success('Payment verified! Redirecting to confirmation...');
        setTimeout(() => window.location.href = `/order-confirmation/${res.order_id}`, 1000);
        return;
      }

      const options = {
        key: res.razorpay_key,
        amount: Math.round(res.total * 100),
        currency: 'INR',
        name: 'Suyog Textile',
        description: `Order #${res.order_number}`,
        order_id: res.razorpay_order_id,
        handler: async (payment) => {
          try {
            Toast.info('Verifying payment signature with server...');
            await API.post(`/api/orders/${res.order_id}/payment/verify`, {
              razorpay_order_id: payment.razorpay_order_id,
              razorpay_payment_id: payment.razorpay_payment_id,
              razorpay_signature: payment.razorpay_signature
            });
            Toast.success('Payment confirmed! Redirecting...');
            window.location.href = `/order-confirmation/${res.order_id}`;
          } catch (err) {
            Toast.error(err.message || 'Payment verification failed. Please contact support.');
            setButtonsProcessing(false);
          }
        },
        prefill: {
          name: document.getElementById('user-name')?.value || '',
          email: document.getElementById('user-email')?.value || ''
        },
        theme: { color: '#8B1A4A' },
        modal: {
          ondismiss: () => {
            setButtonsProcessing(false);
            Toast.info('Payment was not completed. You can retry anytime.');
            API.post(`/api/payments/${res.order_id}/failed`, {
              razorpay_order_id: res.razorpay_order_id,
              error_description: 'User closed the Razorpay payment modal'
            }).catch(() => {});
          }
        }
      };

      const rzp = new Razorpay(options);

      rzp.on('payment.failed', function (response) {
        setButtonsProcessing(false);
        const errDesc = response.error?.description || response.error?.reason || 'Transaction declined';
        Toast.error(`Payment Failed: ${errDesc}`);
        API.post(`/api/payments/${res.order_id}/failed`, {
          razorpay_order_id: response.error?.metadata?.order_id || res.razorpay_order_id,
          razorpay_payment_id: response.error?.metadata?.payment_id,
          error_description: errDesc
        }).catch(() => {});
      });

      rzp.open();
    } catch (err) {
      Toast.error(err.message || 'Could not place order');
      setButtonsProcessing(false);
    }
  }
};

// ─── Filters ──────────────────────────────────────────────────
const Filters = {
  params: new URLSearchParams(window.location.search),

  init() {
    // Sort select
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
      sortSelect.value = this.params.get('sort') || 'featured';
      sortSelect.addEventListener('change', () => {
        this.params.set('sort', sortSelect.value);
        this.params.set('page', '1');
        this.apply();
      });
    }

    // Price filter
    const applyPrice = document.getElementById('apply-price-filter');
    if (applyPrice) {
      applyPrice.addEventListener('click', () => {
        const min = document.getElementById('min-price')?.value;
        const max = document.getElementById('max-price')?.value;
        if (min) this.params.set('min_price', min); else this.params.delete('min_price');
        if (max) this.params.set('max_price', max); else this.params.delete('max_price');
        this.params.set('page', '1');
        this.apply();
      });
    }

    // Color checkboxes
    document.querySelectorAll('input[name="color"]').forEach(cb => {
      cb.addEventListener('change', () => {
        const colors = [...document.querySelectorAll('input[name="color"]:checked')].map(c => c.value);
        if (colors.length) this.params.set('colors', colors.join(','));
        else this.params.delete('colors');
        this.params.set('page', '1');
        this.apply();
      });
    });

    // Fabric checkboxes
    document.querySelectorAll('input[name="fabric"]').forEach(cb => {
      cb.addEventListener('change', () => {
        const fabrics = [...document.querySelectorAll('input[name="fabric"]:checked')].map(f => f.value);
        if (fabrics.length) this.params.set('fabrics', fabrics.join(','));
        else this.params.delete('fabrics');
        this.params.set('page', '1');
        this.apply();
      });
    });

    // Occasion checkboxes
    document.querySelectorAll('input[name="occasion"]').forEach(cb => {
      cb.addEventListener('change', () => {
        const occ = [...document.querySelectorAll('input[name="occasion"]:checked')].map(o => o.value);
        if (occ.length) this.params.set('occasions', occ.join(','));
        else this.params.delete('occasions');
        this.params.set('page', '1');
        this.apply();
      });
    });

    // Clear filters
    document.getElementById('clear-filters')?.addEventListener('click', () => {
      window.location.href = window.location.pathname;
    });

    // Filter toggle on mobile
    const filterToggle = document.getElementById('filter-toggle');
    const filterSidebar = document.getElementById('filter-sidebar');
    filterToggle?.addEventListener('click', () => {
      filterSidebar?.classList.toggle('mobile-visible');
    });
  },

  apply() {
    window.location.href = `${window.location.pathname}?${this.params.toString()}`;
  }
};

// ─── Wishlist buttons on product cards ────────────────────────
function initWishlistButtons() {
  document.querySelectorAll('.wishlist-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      const productId = parseInt(btn.dataset.productId);
      Wishlist.toggle(productId, btn);
    });
  });
}

// ─── Add to cart buttons on product cards ────────────────────
function initAddToCartButtons() {
  document.querySelectorAll('.product-card .add-to-cart-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      const productId = parseInt(btn.dataset.productId);
      if (productId) {
        Cart.add(productId);
      }
    });
  });
}

// ─── Mobile Hamburger Menu ────────────────────────────────────
function initMobileMenu() {
  const hamburger = document.getElementById('hamburger-btn');
  const mobileMenu = document.getElementById('mobile-menu');

  function closeMenu() {
    hamburger?.classList.remove('open');
    mobileMenu?.classList.remove('open');
    document.body.style.overflow = '';
  }

  function toggleMenu() {
    const isOpen = mobileMenu?.classList.contains('open');
    hamburger?.classList.toggle('open', !isOpen);
    mobileMenu?.classList.toggle('open', !isOpen);
    document.body.style.overflow = !isOpen ? 'hidden' : '';
  }

  hamburger?.addEventListener('click', (event) => {
    event.stopPropagation();
    toggleMenu();
  });

  mobileMenu?.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  document.addEventListener('click', (event) => {
    if (!mobileMenu?.contains(event.target) && !hamburger?.contains(event.target)) {
      closeMenu();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 992) closeMenu();
  });
}

// ─── Address Management ───────────────────────────────────────
const AddressManager = {
  async delete(addressId, card) {
    if (!confirm('Delete this address?')) return;
    try {
      await API.delete(`/api/addresses/${addressId}`);
      card?.remove();
      Toast.success('Address deleted');
    } catch (err) {
      Toast.error(err.message);
    }
  },

  async setDefault(addressId) {
    try {
      await API.put(`/api/addresses/${addressId}/set-default`);
      location.reload();
    } catch (err) {
      Toast.error(err.message);
    }
  }
};

// ─── Admin Functions ──────────────────────────────────────────
const Admin = {
  async loadStats() {
    try {
      const stats = await API.get('/api/admin/dashboard/stats');
      document.getElementById('stat-products')?.textContent && (
        document.getElementById('stat-products').textContent = stats.total_products
      );
      document.getElementById('stat-orders')?.textContent !== undefined && (
        document.getElementById('stat-orders') && (document.getElementById('stat-orders').textContent = stats.total_orders)
      );
      ['products', 'orders', 'customers', 'revenue', 'pending', 'low_stock'].forEach(key => {
        const el = document.getElementById(`stat-${key}`);
        if (el) el.textContent = key === 'revenue'
          ? `₹${(stats.total_revenue || 0).toLocaleString('en-IN')}`
          : stats[`total_${key}`] ?? stats[`${key}_orders`] ?? stats[key] ?? 0;
      });
    } catch {}
  },

  async updateOrderStatus(orderId, newStatus) {
    try {
      await API.put(`/api/admin/orders/${orderId}/status`, { status: newStatus });
      Toast.success('Order status updated');
      return true;
    } catch (err) {
      Toast.error(err.message);
      return false;
    }
  }
};

// ─── Init on DOM Ready ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  UIEnhancements.init();
  Search.init();
  Gallery.init();
  initWishlistButtons();
  initAddToCartButtons();
  initMobileMenu();

  // Page-specific init
  if (document.getElementById('add-to-cart-detail')) ProductDetail.init();
  if (document.querySelector('.cart-item, .cart-item-row, .cart-page')) CartPage.init();
  if (document.getElementById('pay-online-btn') || document.getElementById('pay-cod-btn')) Checkout.init();
  if (document.querySelector('.filter-sidebar')) Filters.init();
  if (document.getElementById('admin-dashboard')) Admin.loadStats();

  // Auto-hide flash messages
  document.querySelectorAll('.alert-auto-hide').forEach(el => {
    setTimeout(() => el.remove(), 4000);
  });

  const cartCount = Storage.get('cart_count', 0);
  if (cartCount > 0) {
    Cart.updateCount(cartCount);
  }
  const wishlistIds = Storage.get('wishlist', []);
  document.querySelectorAll('.wishlist-btn').forEach((btn) => {
    const productId = Number(btn.dataset.productId);
    btn.classList.toggle('active', wishlistIds.includes(productId));
    btn.innerHTML = wishlistIds.includes(productId) ? '♥' : '♡';
  });
});

// ─── Utility: Format Indian price ────────────────────────────
function formatINR(amount) {
  return '₹' + parseFloat(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

// ─── Rating Stars ─────────────────────────────────────────────
function renderStars(rating) {
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5;
  let html = '';
  for (let i = 0; i < 5; i++) {
    if (i < full) html += '★';
    else if (i === full && half) html += '½';
    else html += '☆';
  }
  return html;
}
