/**
 * Suyog Collection - Product Module
 * Handles: gallery thumbnail switching, size/color variant selection, pincode checking
 */

window.ProductPage = {
  selectedSize: null,
  selectedColor: null,

  init() {
    this.initGallery();
    this.initVariants();
    this.initQuantity();
  },

  initGallery() {
    const thumbs = document.querySelectorAll('.gallery-thumb, .detail-thumb-item');
    const mainImg = document.getElementById('gallery-main-img');
    if (!thumbs.length || !mainImg) return;

    thumbs.forEach((thumb) => {
      thumb.addEventListener('click', () => {
        thumbs.forEach((t) => t.classList.remove('active'));
        thumb.classList.add('active');
        const src = thumb.dataset.img || thumb.querySelector('img')?.src;
        if (src) {
          mainImg.src = src;
        }
      });
    });
  },

  initVariants() {
    // Size Chips
    const sizeOpts = document.querySelectorAll('.size-option');
    const sizeLabel = document.getElementById('selected-size-label');
    sizeOpts.forEach((opt) => {
      opt.addEventListener('click', () => {
        sizeOpts.forEach((o) => o.classList.remove('selected'));
        opt.classList.add('selected');
        this.selectedSize = opt.dataset.size || opt.textContent.trim();
        if (sizeLabel) {
          sizeLabel.textContent = this.selectedSize;
        }
      });
    });

    // Color Swatches
    const colorOpts = document.querySelectorAll('.color-option');
    const colorLabel = document.getElementById('selected-color-label');
    colorOpts.forEach((opt) => {
      opt.addEventListener('click', () => {
        colorOpts.forEach((o) => o.classList.remove('selected'));
        opt.classList.add('selected');
        this.selectedColor = opt.dataset.color || opt.getAttribute('title');
        if (colorLabel) {
          colorLabel.textContent = this.selectedColor;
        }
      });
    });
  },

  initQuantity() {
    const qtyInput = document.getElementById('quantity-input');
    const minusBtn = document.getElementById('qty-minus');
    const plusBtn = document.getElementById('qty-plus');

    if (!qtyInput) return;

    minusBtn?.addEventListener('click', () => {
      const cur = parseInt(qtyInput.value) || 1;
      if (cur > 1) qtyInput.value = cur - 1;
    });

    plusBtn?.addEventListener('click', () => {
      const cur = parseInt(qtyInput.value) || 1;
      const max = parseInt(qtyInput.getAttribute('max')) || 99;
      if (cur < max) qtyInput.value = cur + 1;
    });
  },

  async checkPincode() {
    const input = document.getElementById('pincode-input');
    const resultBox = document.getElementById('pincode-result');
    if (!input || !resultBox) return;

    const pin = input.value.trim();
    if (!/^\d{6}$/.test(pin)) {
      resultBox.style.display = 'block';
      resultBox.style.color = '#C62828';
      resultBox.innerHTML = '⚠️ Please enter a valid 6-digit Indian PIN code.';
      return;
    }

    resultBox.style.display = 'block';
    resultBox.style.color = '#2E7D32';
    resultBox.innerHTML = `✓ Delivery available to <strong>${pin}</strong> by <strong>${new Date(Date.now() + 4 * 86400000).toLocaleDateString('en-IN', { weekday: 'short', month: 'short', day: 'numeric' })}</strong>.<br>💵 Cash on Delivery is available.`;
  }
};

// Global helper bindings
window.setMainImage = function(el) {
  const mainImg = document.getElementById('gallery-main-img');
  const src = el.getAttribute('data-img') || el.querySelector('img')?.src;
  if (mainImg && src) {
    mainImg.src = src;
    document.querySelectorAll('.gallery-thumb, .detail-thumb-item').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
  }
};

window.selectSize = function(size, el) {
  window.ProductPage.selectedSize = size;
  document.querySelectorAll('.size-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  const label = document.getElementById('selected-size-label');
  if (label) label.textContent = size;
};

window.selectColor = function(color, el) {
  window.ProductPage.selectedColor = color;
  document.querySelectorAll('.color-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  const label = document.getElementById('selected-color-label');
  if (label) label.textContent = color;
};

window.checkPincode = function() {
  window.ProductPage.checkPincode();
};

document.addEventListener('DOMContentLoaded', () => {
  window.ProductPage.init();
});
