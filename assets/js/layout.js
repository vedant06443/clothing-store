/**
 * Suyog Textile — Shared Layout Component
 * Renders consistent Announcement Bar, Header, Mobile Navigation, and Footer across all pages.
 */
(function() {
  function renderLayout() {
    const config = window.SITE_CONFIG || {};
    const brandName = config.brandName || "Suyog Textile";
    const tagline = config.tagline || "Traditional Indian Wear";
    const threshold = config.freeShippingThreshold || 1499;
    const address = config.address || "Lahoti Mala, 484, Jadhav Sankul road, Ashoknagar, Satpur Colony, Nashik, Maharashtra 422007";
    const mapsUrl = config.mapsUrl || "https://maps.google.com/?q=Lahoti+Mala,+484,+Jadhav+Sankul+road,+Ashoknagar,+Satpur+Colony,+Nashik,+Maharashtra+422007";
    const storeHours = config.storeHours || "10:00 AM – 8:30 PM, all days";
    const email = config.email || "contact@suyogtextile.in";
    const phones = config.phones || [
      { display: "0253 4515460", tel: "02534515460" },
      { display: "+91 86693 96037", tel: "+918669396037" }
    ];
    const waUrl = config.whatsappUrl || "https://wa.me/918669396037";
    const trackOrderWa = `${waUrl}?text=${encodeURIComponent("Hi Suyog Textile, I would like to track my order.")}`;

    // ─── 1. Announcement Bar ───
    const announcementEl = document.getElementById('site-announcement') || document.querySelector('.announcement-bar');
    if (announcementEl) {
      announcementEl.className = 'announcement-bar';
      announcementEl.setAttribute('role', 'banner');
      announcementEl.innerHTML = `
        <div class="container text-center">
          ✨ <strong>Authentic Indian Fashion</strong> &nbsp;|&nbsp; 
          🚚 Free Pan-India Shipping on Orders Over ₹${threshold} &nbsp;|&nbsp; 
          Use code <a href="offers.html" style="color:var(--gold-light, #FDE68A);text-decoration:underline;font-weight:700;">WELCOME10</a> for 10% OFF!
        </div>
      `;
    }

    // ─── 2. Header & Navigation ───
    const headerEl = document.getElementById('site-header') || document.querySelector('.desktop-header');
    if (headerEl) {
      headerEl.className = 'desktop-header';
      headerEl.setAttribute('id', 'desktop-header');
      headerEl.innerHTML = `
        <div class="container">
          <div class="desktop-nav-inner">
            <div class="desktop-logo-wrap">
              <a href="index.html" class="navbar-logo" aria-label="${brandName} Home">
                <img src="assets/images/logo.png" alt="${brandName} Logo" class="brand-logo-img" height="46" width="46" style="height:46px;width:auto;object-fit:contain">
                <span class="brand-text-wrap">
                  <span class="brand-name">Suyog <span class="brand-highlight">Textile</span></span>
                  <small class="navbar-tagline">${tagline}</small>
                </span>
              </a>
            </div>

            <nav aria-label="Primary Navigation">
              <ul class="desktop-nav-links">
                <li><a href="index.html">Home</a></li>
                <li><a href="shop.html?cat=sarees">Sarees</a></li>
                <li><a href="shop.html?cat=salwar-suits">Salwar Suits</a></li>
                <li><a href="shop.html?cat=lehengas">Lehengas</a></li>
                <li><a href="shop.html?cat=kurtis">Kurtis</a></li>
                <li><a href="shop.html?cat=dresses">Gowns</a></li>
                <li><a href="shop.html?cat=mens-wear">Menswear</a></li>
                <li><a href="studio.html" style="color:var(--gold, #D97706);font-weight:600;">✨ Style Studio</a></li>
                <li><a href="size-guide.html">Size Guide</a></li>
                <li><a href="offers.html" style="color:#DC2626;font-weight:600;">Offers %</a></li>
              </ul>
            </nav>

            <div class="desktop-nav-right">
              <div class="desktop-search-box">
                <label for="desktop-search-input" class="visually-hidden">Search products</label>
                <input type="text" class="desktop-search-input" id="desktop-search-input" placeholder="Search ethnic wear..." onkeydown="if(event.key==='Enter') window.location.href='shop.html?q='+encodeURIComponent(this.value)">
                <button class="desktop-search-btn" aria-label="Search" onclick="window.location.href='shop.html?q='+encodeURIComponent(document.getElementById('desktop-search-input').value)">
                  <i class="bi bi-search"></i>
                </button>
              </div>

              <a href="wishlist.html" class="nav-icon-btn" title="Saved Wishlist" aria-label="Saved Wishlist">
                <i class="bi bi-heart"></i>
                <span class="nav-badge wishlist-count-badge" style="display:none">0</span>
              </a>

              <a href="login.html" id="headerAuthBtn" class="nav-icon-btn" title="Sign In" aria-label="Account" style="text-decoration:none;">
                <i class="bi bi-person"></i>
                <span class="auth-label d-none d-xl-inline ms-1" style="font-size:0.82rem;font-weight:600;">Sign In</span>
              </a>

              <button class="nav-icon-btn" onclick="if(window.Store) Store.openCartDrawer()" title="Shopping Bag" aria-label="Shopping Bag" style="background:transparent;border:none;">
                <i class="bi bi-bag"></i>
                <span class="nav-badge cart-count-badge" style="display:none">0</span>
              </button>

              <button class="hamburger d-lg-none" aria-label="Open Mobile Menu" onclick="toggleMobileNav()">
                <span></span><span></span><span></span>
              </button>
            </div>
          </div>
        </div>
      `;
    }

    // ─── 3. Mobile Navigation Drawer ───
    let mobileDrawer = document.getElementById('site-mobile-drawer');
    if (!mobileDrawer) {
      mobileDrawer = document.createElement('div');
      mobileDrawer.id = 'site-mobile-drawer';
      document.body.appendChild(mobileDrawer);
    }
    mobileDrawer.innerHTML = `
      <div class="mobile-drawer-overlay" id="mobile-drawer-overlay" onclick="toggleMobileNav()"></div>
      <aside class="mobile-drawer" id="mobile-nav-drawer" aria-label="Mobile Navigation">
        <div class="mobile-drawer-header">
          <a href="index.html" class="navbar-logo" style="font-size:1.15rem">
            <img src="assets/images/logo.png" alt="${brandName} Logo" class="brand-logo-img" height="36" width="36" style="height:36px;width:auto;object-fit:contain">
            <span class="brand-name">Suyog <span class="brand-highlight">Textile</span></span>
          </a>
          <button class="mobile-drawer-close" onclick="toggleMobileNav()" aria-label="Close Menu">✕</button>
        </div>
        <div class="mobile-drawer-body">
          <div>
            <div class="drawer-section-title">Navigation</div>
            <div class="drawer-links-group">
              <a href="index.html" class="drawer-link"><span>🏠 Home</span></a>
              <a href="shop.html?filter=new" class="drawer-link"><span>✨ New Arrivals</span></a>
              <a href="offers.html" class="drawer-link"><span>🔥 Special Offers</span></a>
              <a href="studio.html" class="drawer-link"><span>🎨 Style Studio</span></a>
            </div>
          </div>
          <div>
            <div class="drawer-section-title">Categories</div>
            <div class="drawer-links-group">
              <a href="shop.html?cat=sarees" class="drawer-link"><span>🥻 Sarees</span></a>
              <a href="shop.html?cat=kurtis" class="drawer-link"><span>👗 Kurtis</span></a>
              <a href="shop.html?cat=lehengas" class="drawer-link"><span>💃 Lehenga Choli</span></a>
              <a href="shop.html?cat=salwar-suits" class="drawer-link"><span>👘 Salwar Suits</span></a>
              <a href="shop.html?cat=dresses" class="drawer-link"><span>🌸 Gowns</span></a>
              <a href="shop.html?cat=mens-wear" class="drawer-link"><span>👳 Menswear</span></a>
              <a href="shop.html" class="drawer-link"><span>🛍️ All Collections</span></a>
            </div>
          </div>
          <div>
            <div class="drawer-section-title">Customer Care</div>
            <div class="drawer-links-group">
              <a href="login.html" id="mobileDrawerAccountLink" class="drawer-link"><span>👤 Sign In / My Account</span></a>
              <a href="wishlist.html" class="drawer-link"><span>♡ My Wishlist</span></a>
              <a href="size-guide.html" class="drawer-link"><span>📏 Size Guide & Fit Finder</span></a>
              <a href="${trackOrderWa}" target="_blank" rel="noopener noreferrer" class="drawer-link"><span>🚚 Track my order on WhatsApp</span></a>
              <a href="about.html" class="drawer-link"><span>📖 Our Showroom</span></a>
              <a href="contact.html" class="drawer-link"><span>📍 Contact & Location</span></a>
            </div>
          </div>
        </div>
        <div class="drawer-footer">
          <a href="https://wa.me/${config.whatsappNumber}" target="_blank" rel="noopener noreferrer" class="btn btn-primary w-100">
            <i class="fa-brands fa-whatsapp me-2"></i> Chat with Us
          </a>
        </div>
      </aside>
    `;

    // ─── 4. Shared Footer ───
    const footerEl = document.getElementById('site-footer') || document.querySelector('.site-footer') || document.querySelector('.footer');
    if (footerEl) {
      footerEl.className = 'site-footer';
      footerEl.setAttribute('id', 'site-footer');
      footerEl.style.background = '#1C1917';
      footerEl.style.color = '#FFFFFF';
      footerEl.style.padding = '60px 0 30px';

      const phoneLinks = phones.map(p => `<li><a href="tel:${p.tel}" style="color:rgba(255,255,255,0.85);text-decoration:none">📞 ${p.display}</a></li>`).join('');

      footerEl.innerHTML = `
        <div class="container">
          <div class="row g-4 pb-4 border-bottom border-secondary">
            <!-- Brand & Showroom Info -->
            <div class="col-lg-4 col-md-6">
              <div class="footer-logo mb-3">
                <a href="index.html" style="text-decoration:none;">
                  <span style="font-family:var(--font-brand);font-size:1.4rem;font-weight:700;color:var(--gold, #D97706);">${brandName}</span>
                </a>
                <div style="font-size:0.8rem;color:rgba(255,255,255,0.6);text-transform:uppercase;letter-spacing:1px;">${tagline}</div>
              </div>
              <p style="color:rgba(255,255,255,0.75);font-size:0.88rem;line-height:1.6;margin-bottom:14px;">
                Versatile clothing store offering a wide variety of readymade garments and fabrics for all ages.
              </p>
              <div style="font-size:0.85rem;color:rgba(255,255,255,0.8);margin-bottom:8px;">
                <strong>Showroom Address:</strong><br>
                ${address}<br>
                <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" style="color:var(--gold-light, #FDE68A);text-decoration:underline;">📍 View on Google Maps</a>
              </div>
              <div style="font-size:0.85rem;color:rgba(255,255,255,0.8);margin-top:8px;">
                <strong>Timings:</strong> ${storeHours}
              </div>
            </div>

            <!-- Quick Links -->
            <div class="col-lg-2 col-md-6">
              <h5 style="color:var(--gold, #D97706);font-family:var(--font-brand);margin-bottom:16px;font-size:1rem;">Collections</h5>
              <ul class="list-unstyled" style="line-height:2.2;font-size:0.88rem;">
                <li><a href="shop.html?cat=sarees" style="color:rgba(255,255,255,0.8);text-decoration:none">Sarees</a></li>
                <li><a href="shop.html?cat=kurtis" style="color:rgba(255,255,255,0.8);text-decoration:none">Kurtis</a></li>
                <li><a href="shop.html?cat=lehengas" style="color:rgba(255,255,255,0.8);text-decoration:none">Lehengas</a></li>
                <li><a href="shop.html?cat=salwar-suits" style="color:rgba(255,255,255,0.8);text-decoration:none">Salwar Suits</a></li>
                <li><a href="shop.html?cat=dresses" style="color:rgba(255,255,255,0.8);text-decoration:none">Gowns</a></li>
                <li><a href="shop.html?cat=mens-wear" style="color:rgba(255,255,255,0.8);text-decoration:none">Menswear</a></li>
                <li><a href="studio.html" style="color:rgba(255,255,255,0.8);text-decoration:none">Style Studio</a></li>
              </ul>
            </div>

            <!-- Customer Care -->
            <div class="col-lg-3 col-md-6">
              <h5 style="color:var(--gold, #D97706);font-family:var(--font-brand);margin-bottom:16px;font-size:1rem;">Customer Care</h5>
              <ul class="list-unstyled" style="line-height:2.2;font-size:0.88rem;">
                <li><a href="account.html" style="color:rgba(255,255,255,0.8);text-decoration:none">👤 My Account & Orders</a></li>
                <li><a href="size-guide.html" style="color:rgba(255,255,255,0.8);text-decoration:none">📏 Size Guide & Fit Finder</a></li>
                <li><a href="${trackOrderWa}" target="_blank" rel="noopener noreferrer" style="color:rgba(255,255,255,0.8);text-decoration:none">🚚 Track my order on WhatsApp</a></li>
                <li><a href="cart.html" style="color:rgba(255,255,255,0.8);text-decoration:none">🛍️ Shopping Bag</a></li>
                <li><a href="wishlist.html" style="color:rgba(255,255,255,0.8);text-decoration:none">♡ Saved Wishlist</a></li>
                <li><a href="offers.html" style="color:rgba(255,255,255,0.8);text-decoration:none">🎟️ Active Promotions</a></li>
                <li><a href="about.html" style="color:rgba(255,255,255,0.8);text-decoration:none">Showroom Story</a></li>
                <li><a href="contact.html" style="color:rgba(255,255,255,0.8);text-decoration:none">Contact Showroom</a></li>
              </ul>
            </div>

            <!-- Policies & Direct Contact -->
            <div class="col-lg-3 col-md-6">
              <h5 style="color:var(--gold, #D97706);font-family:var(--font-brand);margin-bottom:16px;font-size:1rem;">Contact & Policies</h5>
              <ul class="list-unstyled" style="line-height:2;font-size:0.88rem;margin-bottom:16px;">
                ${phoneLinks}
                <li><a href="mailto:${email}" style="color:rgba(255,255,255,0.85);text-decoration:none">✉️ ${email}</a></li>
                <li><a href="https://wa.me/${config.whatsappNumber}" target="_blank" rel="noopener noreferrer" style="color:#25D366;text-decoration:none;font-weight:600;"><i class="fa-brands fa-whatsapp"></i> Chat on WhatsApp</a></li>
              </ul>

              <h6 style="color:rgba(255,255,255,0.9);font-size:0.85rem;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px;">Legal & Store Policies</h6>
              <ul class="list-unstyled" style="line-height:2;font-size:0.82rem;">
                <li><a href="privacy.html" style="color:rgba(255,255,255,0.7);text-decoration:none">Privacy Policy</a></li>
                <li><a href="terms.html" style="color:rgba(255,255,255,0.7);text-decoration:none">Terms of Service</a></li>
                <li><a href="shipping-returns.html" style="color:rgba(255,255,255,0.7);text-decoration:none">Shipping & 7-Day Exchange</a></li>
              </ul>
            </div>
          </div>

          <div class="d-flex flex-wrap justify-content-between align-items-center pt-3 small" style="color:rgba(255,255,255,0.6)">
            <div>&copy; 2026 ${brandName}. All rights reserved. Nashik, Maharashtra.</div>
            <div>Free Pan-India Delivery on orders over ₹${threshold}</div>
          </div>
        </div>
      `;
    }
    // Dynamic Auth Header Update
    syncAuthUi();
  }

  function syncAuthUi() {
    function update(user) {
      const headerAuthBtn = document.getElementById('headerAuthBtn');
      const mobileDrawerAccountLink = document.getElementById('mobileDrawerAccountLink');

      if (user) {
        if (headerAuthBtn) {
          headerAuthBtn.href = 'account.html';
          headerAuthBtn.title = 'My Account';
          headerAuthBtn.setAttribute('aria-label', 'My Account');
          headerAuthBtn.innerHTML = '<i class="bi bi-person-circle"></i><span class="auth-label d-none d-xl-inline ms-1" style="font-size:0.82rem;font-weight:600;">Account</span>';
        }
        if (mobileDrawerAccountLink) {
          mobileDrawerAccountLink.href = 'account.html';
          mobileDrawerAccountLink.innerHTML = '<span>👤 My Account & Orders</span>';
        }
      } else {
        if (headerAuthBtn) {
          headerAuthBtn.href = 'login.html';
          headerAuthBtn.title = 'Sign In';
          headerAuthBtn.setAttribute('aria-label', 'Sign In');
          headerAuthBtn.innerHTML = '<i class="bi bi-person"></i><span class="auth-label d-none d-xl-inline ms-1" style="font-size:0.82rem;font-weight:600;">Sign In</span>';
        }
        if (mobileDrawerAccountLink) {
          mobileDrawerAccountLink.href = 'login.html';
          mobileDrawerAccountLink.innerHTML = '<span>👤 Sign In / Register</span>';
        }
      }
    }

    // Check if client is already initialized or wait brief moment
    function check() {
      if (window.supabaseClient && window.isSupabaseConfigured && window.isSupabaseConfigured()) {
        window.supabaseClient.auth.getSession().then(function(res) {
          var session = res.data ? res.data.session : null;
          update(session ? session.user : null);
        }).catch(function() {});

        if (window.supabaseClient.auth.onAuthStateChange) {
          window.supabaseClient.auth.onAuthStateChange(function(event, session) {
            update(session ? session.user : null);
          });
        }
      }
    }

    check();
    setTimeout(check, 400);
  }

  window.toggleMobileNav = function() {
    const drawer = document.getElementById('mobile-nav-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');
    if (drawer && overlay) {
      drawer.classList.toggle('active');
      overlay.classList.toggle('active');
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderLayout);
  } else {
    renderLayout();
  }
})();
