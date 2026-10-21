/**
 * Suyog Textile - Cart Module
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
    try {
      if (window.Cart && typeof window.Cart.remove === 'function') {
        const res = await window.Cart.remove(itemId);
        if (res !== undefined) {
          if (window.Toast) window.Toast.success('Item removed from shopping bag');
          window.location.reload();
          return;
        }
      }
      const res = await fetch(`/api/cart/item/${itemId}`, { method: 'DELETE' });
      if (res.ok) {
        if (window.Toast) window.Toast.success('Item removed from shopping bag');
        window.location.reload();
      } else {
        const err = await res.json().catch(() => ({}));
        if (window.Toast) window.Toast.error(err.detail || 'Could not remove item');
      }
    } catch (err) {
      console.error('Failed to remove cart item', err);
      if (window.Toast) window.Toast.error('Could not remove item');
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

// Bind inline helpers for cart templates
window.updateItemQty = function(itemId, change) {
  window.CartOps.updateQty(itemId, change);
};

window.removeCartItem = function(itemId) {
  window.CartOps.removeItem(itemId);
};
