/**
 * Suyog Collection - Responsive UI & Mobile Interactions
 * Handles: mobile drawer, mobile search, category scroller, filter drawer, footer accordion
 */

(function () {
  'use strict';

  // ─── Mobile Offcanvas Drawer ─────────────────────────────────
  const MobileDrawer = {
    drawer: null,
    overlay: null,
    openBtns: [],
    closeBtns: [],

    init() {
      this.drawer = document.getElementById('mobile-nav-drawer') || document.getElementById('mobile-menu');
      this.overlay = document.getElementById('mobile-drawer-overlay');
      this.openBtns = document.querySelectorAll('.mobile-hamburger-btn, #hamburger-btn');
      this.closeBtns = document.querySelectorAll('.mobile-drawer-close, #mobile-drawer-close');

      if (!this.drawer) return;

      this.openBtns.forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.open();
        });
      });

      this.closeBtns.forEach((btn) => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          this.close();
        });
      });

      if (this.overlay) {
        this.overlay.addEventListener('click', () => this.close());
      }

      // Close when clicking nav links
      this.drawer.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => this.close());
      });

      // Escape key to close
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isOpen()) {
          this.close();
        }
      });

      // Auto close on desktop resize
      window.addEventListener('resize', () => {
        if (window.innerWidth >= 992 && this.isOpen()) {
          this.close();
        }
      });
    },

    isOpen() {
      return this.drawer && (this.drawer.classList.contains('active') || this.drawer.classList.contains('open'));
    },

    open() {
      if (!this.drawer) return;
      this.drawer.classList.add('active');
      this.drawer.classList.add('open');
      if (this.overlay) {
        this.overlay.classList.add('active');
      }
      document.body.style.overflow = 'hidden';
      this.openBtns.forEach((btn) => btn.classList.add('open'));
    },

    close() {
      if (!this.drawer) return;
      this.drawer.classList.remove('active');
      this.drawer.classList.remove('open');
      if (this.overlay) {
        this.overlay.classList.remove('active');
      }
      document.body.style.overflow = '';
      this.openBtns.forEach((btn) => btn.classList.remove('open'));
    }
  };

  // ─── Mobile Dedicated Search ─────────────────────────────────
  const MobileSearch = {
    input: null,
    clearBtn: null,
    suggestionsBox: null,
    debounceTimer: null,

    init() {
      this.input = document.getElementById('mobile-search-input');
      this.clearBtn = document.getElementById('mobile-search-clear');
      this.suggestionsBox = document.getElementById('mobile-search-suggestions');

      if (!this.input) return;

      this.input.addEventListener('input', () => {
        const query = this.input.value.trim();
        if (this.clearBtn) {
          this.clearBtn.style.display = query.length > 0 ? 'block' : 'none';
        }

        clearTimeout(this.debounceTimer);
        if (query.length < 2) {
          if (this.suggestionsBox) this.suggestionsBox.classList.remove('show');
          return;
        }

        this.debounceTimer = setTimeout(() => this.fetchSuggestions(query), 250);
      });

      this.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const q = this.input.value.trim();
          if (q) {
            window.location.href = `/search?q=${encodeURIComponent(q)}`;
          }
        }
      });

      if (this.clearBtn) {
        this.clearBtn.addEventListener('click', () => {
          this.input.value = '';
          this.clearBtn.style.display = 'none';
          if (this.suggestionsBox) this.suggestionsBox.classList.remove('show');
          this.input.focus();
        });
      }

      document.addEventListener('click', (e) => {
        if (this.suggestionsBox && !this.input.contains(e.target) && !this.suggestionsBox.contains(e.target)) {
          this.suggestionsBox.classList.remove('show');
        }
      });
    },

    async fetchSuggestions(q) {
      if (!this.suggestionsBox) return;
      try {
        const res = await fetch(`/api/products/search/suggestions?q=${encodeURIComponent(q)}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.suggestions && data.suggestions.length > 0) {
          this.suggestionsBox.innerHTML = data.suggestions
            .map((s) => `<div class="suggestion-item" onclick="window.location.href='/search?q=${encodeURIComponent(s)}'">${s}</div>`)
            .join('');
          this.suggestionsBox.classList.add('show');
        } else {
          this.suggestionsBox.classList.remove('show');
        }
      } catch (err) {
        // silent fail
      }
    }
  };

  // ─── Collection Filter Drawer on Mobile ──────────────────────
  const FilterDrawer = {
    sidebar: null,
    backdrop: null,
    openBtn: null,
    closeBtn: null,

    init() {
      this.sidebar = document.getElementById('filter-sidebar');
      this.openBtn = document.getElementById('mobile-filter-open');
      this.closeBtn = document.getElementById('mobile-filter-close');

      if (!this.sidebar) return;

      // Create backdrop if not present
      this.backdrop = document.getElementById('filter-drawer-backdrop');
      if (!this.backdrop) {
        this.backdrop = document.createElement('div');
        this.backdrop.id = 'filter-drawer-backdrop';
        this.backdrop.className = 'filter-drawer-backdrop';
        document.body.appendChild(this.backdrop);
      }

      if (this.openBtn) {
        this.openBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.open();
        });
      }

      if (this.closeBtn) {
        this.closeBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.close();
        });
      }

      this.backdrop.addEventListener('click', () => this.close());
    },

    open() {
      if (!this.sidebar) return;
      this.sidebar.classList.add('drawer-open');
      if (this.backdrop) this.backdrop.classList.add('active');
      document.body.style.overflow = 'hidden';
    },

    close() {
      if (!this.sidebar) return;
      this.sidebar.classList.remove('drawer-open');
      if (this.backdrop) this.backdrop.classList.remove('active');
      document.body.style.overflow = '';
    }
  };

  // ─── Footer Accordions on Mobile ─────────────────────────────
  const FooterAccordion = {
    init() {
      const headers = document.querySelectorAll('.footer-accordion-header');
      headers.forEach((header) => {
        header.addEventListener('click', () => {
          if (window.innerWidth >= 768) return;
          const item = header.closest('.footer-accordion-item');
          if (item) {
            item.classList.toggle('active');
          }
        });
      });
    }
  };

  // ─── Category Horizontal Scroller Helpers ────────────────────
  const CategoryScroller = {
    init() {
      const container = document.querySelector('.categories-grid');
      if (!container) return;

      // Ensure smooth horizontal dragging on mobile touch
      let isDown = false;
      let startX;
      let scrollLeft;

      container.addEventListener('mousedown', (e) => {
        isDown = true;
        startX = e.pageX - container.offsetLeft;
        scrollLeft = container.scrollLeft;
      });

      container.addEventListener('mouseleave', () => { isDown = false; });
      container.addEventListener('mouseup', () => { isDown = false; });

      container.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const walk = (x - startX) * 1.5;
        container.scrollLeft = scrollLeft - walk;
      });
    }
  };

  // ─── Initialize on DOM Ready ────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    MobileDrawer.init();
    MobileSearch.init();
    FilterDrawer.init();
    FooterAccordion.init();
    CategoryScroller.init();
  });

  window.SuyogResponsive = {
    MobileDrawer,
    MobileSearch,
    FilterDrawer
  };
})();
