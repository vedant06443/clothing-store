/**
 * Admin Real-Time Order Notifications System
 * Handles WebSocket connection, live unread count, audio chime, toast alerts, and dropdown.
 */

let adminSocket = null;
let reconnectTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 15000;

// ── Synthetic Web Audio Chime (No external audio file needed, respects browser policies) ──
function playNotificationChime() {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    if (ctx.state === 'suspended') {
      ctx.resume().catch(() => {});
    }

    // Play a friendly dual-tone luxury chime (E5 -> B5)
    const now = ctx.currentTime;
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(659.25, now); // E5
    gain1.gain.setValueAtTime(0.12, now);
    gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.start(now);
    osc1.stop(now + 0.35);

    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.frequency.setValueAtTime(987.77, now + 0.12); // B5
    gain2.gain.setValueAtTime(0.15, now + 0.12);
    gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.55);
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.start(now + 0.12);
    osc2.stop(now + 0.55);
  } catch (e) {
    // Autoplay policy or unsupported audio - graceful degradation
  }
}

// ── Time Ago Formatter ──
function formatTimeAgo(isoString) {
  if (!isoString) return 'Just now';
  const date = new Date(isoString);
  const seconds = Math.floor((new Date() - date) / 1000);
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ── Badge & UI Updaters ──
function updateBellBadge(count) {
  const badge = document.getElementById('admin-bell-badge');
  const navPills = document.querySelectorAll('.unread-badge-count');

  if (badge) {
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = 'inline-flex';
    } else {
      badge.textContent = '0';
      badge.style.display = 'none';
    }
  }

  navPills.forEach(pill => {
    if (count > 0) {
      pill.textContent = `${count} New`;
      pill.style.display = 'inline-block';
    } else {
      pill.style.display = 'none';
    }
  });
}

// ── Fetch Initial State & Populate Dropdown ──
async function fetchRecentNotifications() {
  try {
    const res = await fetch('/api/admin/notifications?limit=8');
    if (!res.ok) return;
    const data = await res.json();
    updateBellBadge(data.unread_count);
    renderDropdownItems(data.notifications);
  } catch (err) {
    console.warn('[Notifications] Could not fetch notifications:', err);
  }
}

function renderDropdownItems(notifications) {
  const list = document.getElementById('admin-notif-dropdown-list');
  if (!list) return;

  if (!notifications || notifications.length === 0) {
    list.innerHTML = `
      <div style="padding:28px 16px;text-align:center;color:var(--text-muted);font-size:0.85rem">
        <div style="font-size:1.6rem;margin-bottom:6px">🔕</div>
        No notifications yet
      </div>
    `;
    return;
  }

  list.innerHTML = notifications.map(n => `
    <div class="notif-dropdown-item ${n.is_read ? 'read' : 'unread'}" 
         id="dd-notif-${n.id}"
         onclick="handleDropdownItemClick(${n.id}, ${n.order_id})">
      <div class="notif-dd-left">
        ${n.is_read ? '<span class="dd-dot read"></span>' : '<span class="dd-dot unread">🔴</span>'}
      </div>
      <div class="notif-dd-body">
        <div class="notif-dd-title-row">
          <strong class="notif-dd-title">${escapeHtml(n.title)}</strong>
          <span class="notif-dd-time">${formatTimeAgo(n.created_at)}</span>
        </div>
        <div class="notif-dd-order-num">Order #${escapeHtml(n.order_number)}</div>
        <div class="notif-dd-product">${escapeHtml(n.product_name)} • Qty: ${n.quantity}</div>
        <div class="notif-dd-bottom">
          <strong class="notif-dd-amount">${escapeHtml(n.formatted_amount)}</strong>
          <span class="notif-dd-btn">View Order →</span>
        </div>
      </div>
    </div>
  `).join('');
}

function prependDropdownNotification(n) {
  const list = document.getElementById('admin-notif-dropdown-list');
  if (!list) return;

  // Remove empty state if present
  if (list.querySelector('div[style*="text-align:center"]')) {
    list.innerHTML = '';
  }

  const itemHtml = `
    <div class="notif-dropdown-item unread new-pulse" 
         id="dd-notif-${n.id}"
         onclick="handleDropdownItemClick(${n.id}, ${n.order_id})">
      <div class="notif-dd-left">
        <span class="dd-dot unread">🔴</span>
      </div>
      <div class="notif-dd-body">
        <div class="notif-dd-title-row">
          <strong class="notif-dd-title">${escapeHtml(n.title)}</strong>
          <span class="notif-dd-time">Just now</span>
        </div>
        <div class="notif-dd-order-num">Order #${escapeHtml(n.order_number)}</div>
        <div class="notif-dd-product">${escapeHtml(n.product_name)} • Qty: ${n.quantity}</div>
        <div class="notif-dd-bottom">
          <strong class="notif-dd-amount">${escapeHtml(n.formatted_amount)}</strong>
          <span class="notif-dd-btn">View Order →</span>
        </div>
      </div>
    </div>
  `;
  list.insertAdjacentHTML('afterbegin', itemHtml);
}

// ── Dropdown Item Click ──
async function handleDropdownItemClick(notifId, orderId) {
  try {
    await fetch(`/api/admin/notifications/${notifId}/read`, { method: 'PATCH' });
    const item = document.getElementById(`dd-notif-${notifId}`);
    if (item) {
      item.classList.remove('unread');
      item.classList.add('read');
      const dot = item.querySelector('.dd-dot');
      if (dot) dot.innerHTML = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#D1D5DB"></span>';
    }
  } catch (e) {
    // Ignore error
  }
  // Open existing order page
  window.open(`/orders/${orderId}`, '_blank');
}

// ── Mark All Read ──
async function handleMarkAllRead(e) {
  if (e) e.stopPropagation();
  try {
    const res = await fetch('/api/admin/notifications/read-all', { method: 'PATCH' });
    if (res.ok) {
      updateBellBadge(0);
      document.querySelectorAll('.notif-dropdown-item').forEach(item => {
        item.classList.remove('unread');
        item.classList.add('read');
        const dot = item.querySelector('.dd-dot');
        if (dot) dot.innerHTML = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#D1D5DB"></span>';
      });
      if (typeof Toast !== 'undefined') Toast.success('All marked as read');
    }
  } catch (err) {
    console.error('Failed to mark all read:', err);
  }
}

// ── Real-Time Order Toast Alert ──
function showOrderToast(n) {
  let toastContainer = document.getElementById('admin-order-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'admin-order-toast-container';
    toastContainer.className = 'admin-order-toast-container';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = 'admin-live-order-toast';
  toast.innerHTML = `
    <div class="toast-header-row">
      <span class="toast-bell-icon">🔔</span>
      <strong>New Order Received!</strong>
      <button type="button" class="toast-close-btn" onclick="this.closest('.admin-live-order-toast').remove()">✕</button>
    </div>
    <div class="toast-body-content">
      <div class="toast-order-num">Order #${escapeHtml(n.order_number)}</div>
      <div class="toast-customer">Customer: <strong>${escapeHtml(n.customer_name)}</strong></div>
      <div class="toast-product">${escapeHtml(n.product_name)} (Qty: ${n.quantity})</div>
      <div class="toast-amount">${escapeHtml(n.formatted_amount)}</div>
    </div>
    <div class="toast-action-row">
      <a href="/orders/${n.order_id}" target="_blank" class="toast-view-btn" onclick="handleDropdownItemClick(${n.id}, ${n.order_id}); this.closest('.admin-live-order-toast').remove();">
        View Order ↗
      </a>
    </div>
  `;

  toastContainer.appendChild(toast);

  // Play synthetic chime
  playNotificationChime();

  // Auto-dismiss after 6.5 seconds
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = 'toastSlideOut 0.3s forwards ease';
      setTimeout(() => toast.remove(), 300);
    }
  }, 6500);
}

// ── Dropdown Toggle ──
function toggleNotificationDropdown(e) {
  if (e) {
    e.preventDefault();
    e.stopPropagation();
  }
  const dropdown = document.getElementById('admin-notif-dropdown');
  if (!dropdown) return;

  const isOpen = dropdown.classList.contains('show');
  if (isOpen) {
    dropdown.classList.remove('show');
  } else {
    dropdown.classList.add('show');
    fetchRecentNotifications();
  }
}

// Close dropdown on click outside
document.addEventListener('click', function(e) {
  const dropdown = document.getElementById('admin-notif-dropdown');
  const bellBtn = document.getElementById('admin-bell-btn');
  if (dropdown && dropdown.classList.contains('show')) {
    if (!dropdown.contains(e.target) && (!bellBtn || !bellBtn.contains(e.target))) {
      dropdown.classList.remove('show');
    }
  }
});

// ── WebSocket Connection & Reconnect ──
function initAdminWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/admin/notifications`;

  try {
    adminSocket = new WebSocket(wsUrl);

    adminSocket.onopen = function() {
      reconnectAttempts = 0;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      // Keep alive ping every 30s
      setInterval(() => {
        if (adminSocket && adminSocket.readyState === WebSocket.OPEN) {
          adminSocket.send('ping');
        }
      }, 30000);
    };

    adminSocket.onmessage = function(event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'init') {
          updateBellBadge(data.unread_count);
        } else if (data.type === 'new_order') {
          updateBellBadge(data.unread_count);
          prependDropdownNotification(data.notification);
          showOrderToast(data.notification);

          // If on /admin/notifications page, reload or prepend row
          const notifTableBody = document.getElementById('notifications-table-body');
          if (notifTableBody && typeof reloadNotificationsPage === 'function') {
            reloadNotificationsPage();
          }
        }
      } catch (err) {
        // Ignore non-json (e.g. pong)
      }
    };

    adminSocket.onclose = function(e) {
      if (e.code !== 1008) {
        scheduleReconnect();
      }
    };

    adminSocket.onerror = function() {
      scheduleReconnect();
    };
  } catch (err) {
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectAttempts++;
  const delay = Math.min(2000 * Math.pow(1.5, reconnectAttempts), MAX_RECONNECT_DELAY);
  reconnectTimer = setTimeout(initAdminWebSocket, delay);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ── Initialize on page ready ──
document.addEventListener('DOMContentLoaded', () => {
  fetchRecentNotifications();
  initAdminWebSocket();
});
