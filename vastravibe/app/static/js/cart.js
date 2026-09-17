/**
 * Suyog Collection - Cart Module
 * Dedicated handler for cart operations, quantity adjustments, coupon validation
 */

window.CartOps = {
  async updateQty(itemId, change) {
    const input = document.querySelector(`.cart-qty-input[data-item-id="${itemId}"]`);
    if (!input) return;
    const currentVal = parseInt(input.value) || 1;
    const newVal = currentVal + change;
    if (newVal < 1) return;

    input.value = newVal;

    if (window.Cart && typeof window.Cart.updateQty === 'function') {
      const res = await window.Cart.updateQty(itemId, newVal);
      if (res) {
        window.location.reload();
      }
    } else {
      try {
        const res = await fetch(`/api/cart/item/${itemId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quantity: newVal })
        });
        if (res.ok) {
          window.location.reload();
        }
      } catch (err) {
        console.error('Failed to update cart qty', err);
      }
    }
  },

  async removeItem(itemId) {
    if (window.Cart && typeof window.Cart.remove === 'function') {
      await window.Cart.remove(itemId);
    } else {
      try {
        const res = await fetch(`/api/cart/item/${itemId}`, { method: 'DELETE' });
        if (res.ok) {
          window.location.reload();
        }
      } catch (err) {
        console.error('Failed to remove cart item', err);
      }
    }
  },

  async applyCoupon(code) {
    if (!code) return;
    try {
      const res = await fetch('/api/cart/coupon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code.trim().toUpperCase() })
      });
      const data = await res.json();
      if (res.ok) {
        if (window.Toast) window.Toast.success(`Coupon ${code} applied!`);
        setTimeout(() => window.location.reload(), 600);
      } else {
        if (window.Toast) window.Toast.error(data.detail || 'Invalid coupon code');
      }
    } catch (err) {
      if (window.Toast) window.Toast.error('Could not apply coupon');
    }
  }
};

// Bind inline helper for cart templates
window.updateItemQty = function(itemId, change) {
  window.CartOps.updateQty(itemId, change);
};
