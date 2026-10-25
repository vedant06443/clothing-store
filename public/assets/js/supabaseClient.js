/**
 * Suyog Textile — Supabase Client Integration
 * Loads Supabase client using pinned UMD build from CDN.
 * Gracefully handles offline / unconfigured state with a WhatsApp assistance prompt.
 */

(function () {
  'use strict';

  var client = null;
  var isConfigured = false;

  var cfg = window.SITE_CONFIG || {};
  var url = cfg.supabaseUrl;
  var key = cfg.supabaseAnonKey;

  if (url && url !== 'TODO_CONFIRM' && key && key !== 'TODO_CONFIRM' && window.supabase) {
    try {
      client = window.supabase.createClient(url, key, {
        auth: {
          persistSession: true,
          autoRefreshToken: true,
          detectSessionInUrl: true
        }
      });
      isConfigured = true;
    } catch (err) {
      console.warn('[Suyog Textile] Supabase initialization error:', err);
      client = null;
      isConfigured = false;
    }
  } else {
    // Supabase credentials pending configuration in assets/js/config.js
    isConfigured = false;
  }

  window.supabaseClient = client;
  window.isSupabaseConfigured = function () {
    return isConfigured && client !== null;
  };

  /**
   * Helper to display an elegant error/offline state with direct WhatsApp support
   */
  window.showFriendlyErrorState = function (container, customMessage) {
    if (!container) return;
    var target = typeof container === 'string' ? document.getElementById(container) : container;
    if (!target) return;

    var waNum = (window.SITE_CONFIG && window.SITE_CONFIG.whatsappNumber) || '918669396037';
    var waUrl = 'https://wa.me/' + waNum + '?text=' + encodeURIComponent('Namaste Suyog Textile, I need help browsing your collection.');

    var msg = customMessage || 'Our real-time collection is temporarily syncing. You can browse directly with our showroom stylist on WhatsApp!';

    target.innerHTML =
      '<div class="text-center py-5 px-3" style="grid-column: 1 / -1; max-width: 600px; margin: 0 auto;">' +
      '  <div style="font-size: 2.5rem; margin-bottom: 12px;">✨</div>' +
      '  <h3 style="font-family: var(--font-brand); font-size: 1.35rem; margin-bottom: 8px; color: var(--dark, #1C1917);">Showroom Stylist Available</h3>' +
      '  <p style="color: var(--text-muted, #78716C); font-size: 0.92rem; line-height: 1.6; margin-bottom: 20px;">' + msg + '</p>' +
      '  <a href="' + waUrl + '" class="btn btn-whatsapp" target="_blank" rel="noopener noreferrer" style="display: inline-flex; align-items: center; gap: 8px; padding: 10px 22px; border-radius: 8px; text-decoration: none; font-weight: 600;">' +
      '    <i class="fa-brands fa-whatsapp" style="font-size: 1.2rem;"></i> Inquire on WhatsApp' +
      '  </a>' +
      '</div>';
  };
})();
