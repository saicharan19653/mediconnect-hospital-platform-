/**
 * api.js - Shared API utilities, auth management, and UI helpers
 * MediConnect Hospital Platform
 */

// ============================================================
// Configuration
// ============================================================
const API_BASE = 'https://mediconnect-api.onrender.com/api';

// ============================================================
// Auth Management
// ============================================================
const Auth = {
  getToken() { return localStorage.getItem('hsp_token'); },
  getUser() {
    const u = localStorage.getItem('hsp_user');
    return u ? JSON.parse(u) : null;
  },
  setSession(token, user) {
    localStorage.setItem('hsp_token', token);
    localStorage.setItem('hsp_user', JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem('hsp_token');
    localStorage.removeItem('hsp_user');
  },
  isLoggedIn() { return !!this.getToken(); },
  isAdmin() { return this.getUser()?.role === 'admin'; },
  isPatient() { return this.getUser()?.role === 'patient'; },
  requireAuth(redirect = '/pages/login.html') {
    if (!this.isLoggedIn()) { window.location.href = redirect; return false; }
    return true;
  },
  requireAdmin(redirect = '/pages/login.html') {
    if (!this.isLoggedIn() || !this.isAdmin()) { window.location.href = redirect; return false; }
    return true;
  },
  logout() {
    this.clearSession();
    window.location.href = '/pages/login.html';
  }
};

// ============================================================
// API Client
// ============================================================
const Api = {
  async request(method, endpoint, body = null, auth = false) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth) {
      const token = Auth.getToken();
      if (token) headers['Authorization'] = `Bearer ${token}`;
    }
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    try {
      const res = await fetch(API_BASE + endpoint, opts);
      const data = await res.json();
      if (!res.ok) throw { status: res.status, message: data.message || 'Request failed', data };
      return data;
    } catch (err) {
      if (err.status === 401) { Auth.clearSession(); window.location.href = '/pages/login.html'; }
      throw err;
    }
  },
  get(endpoint, params = {}, auth = false) {
    const qs = new URLSearchParams(params).toString();
    return this.request('GET', endpoint + (qs ? '?' + qs : ''), null, auth);
  },
  post(endpoint, body, auth = false) { return this.request('POST', endpoint, body, auth); },
  put(endpoint, body, auth = true) { return this.request('PUT', endpoint, body, auth); },
  delete(endpoint, auth = true) { return this.request('DELETE', endpoint, null, auth); },

  // Auth endpoints
  register: (data) => Api.post('/register', data),
  login: (data) => Api.post('/login', data),
  me: () => Api.get('/me', {}, true),

  // Hospital endpoints
  getHospitals: (params) => Api.get('/hospitals', params),
  getHospital: (id) => Api.get(`/hospitals/${id}`),
  searchByLocation: (location) => Api.get('/hospitals/location', { location }),
  addHospital: (data) => Api.post('/hospitals', data, true),
  updateHospital: (id, data) => Api.put(`/hospitals/${id}`, data),
  deleteHospital: (id) => Api.delete(`/hospitals/${id}`),
  updateCrowd: (id, data) => Api.put(`/hospitals/${id}/crowd`, data),

  // Doctor endpoints
  getDoctors: (params) => Api.get('/doctors', params),
  getDoctor: (id) => Api.get(`/doctors/${id}`),
  addDoctor: (data) => Api.post('/doctors', data, true),
  updateDoctor: (id, data) => Api.put(`/doctors/${id}`, data),
  deleteDoctor: (id) => Api.delete(`/doctors/${id}`),

  // Appointment endpoints
  bookAppointment: (data) => Api.post('/appointments', data, true),
  getAppointments: (params) => Api.get('/appointments', params, true),
  updateAppointmentStatus: (id, status) => Api.put(`/appointments/${id}/status`, { status }),

  // Blood donor endpoints
  registerDonor: (data) => Api.post('/blood-donors', data, true),
  getDonors: (params) => Api.get('/blood-donors', params),
  updateDonor: (id, data) => Api.put(`/blood-donors/${id}`, data),
  deleteDonor: (id) => Api.delete(`/blood-donors/${id}`),
};

// ============================================================
// Toast Notifications
// ============================================================
const Toast = {
  container: null,
  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      document.body.appendChild(this.container);
    }
  },
  show(message, type = 'info', duration = 4000) {
    this.init();
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span style="font-size:16px">${icons[type] || icons.info}</span><span>${message}</span>`;
    this.container.appendChild(toast);
    setTimeout(() => {
      toast.style.animation = 'fadeOut 0.3s ease forwards';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  },
  success: (msg) => Toast.show(msg, 'success'),
  error: (msg) => Toast.show(msg, 'error'),
  warning: (msg) => Toast.show(msg, 'warning'),
  info: (msg) => Toast.show(msg, 'info'),
};

// ============================================================
// UI Helpers
// ============================================================
const UI = {
  setLoading(btn, loading, text = '') {
    if (!btn) return;
    if (loading) {
      btn._origText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<div class="spinner"></div>${text}`;
    } else {
      btn.disabled = false;
      btn.innerHTML = btn._origText || text;
    }
  },
  showError(containerId, message) {
    const el = document.getElementById(containerId);
    if (el) { el.innerHTML = `<div class="alert alert-danger">⚠ ${message}</div>`; el.classList.remove('hidden'); }
  },
  hideError(containerId) {
    const el = document.getElementById(containerId);
    if (el) { el.innerHTML = ''; el.classList.add('hidden'); }
  },
  formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  },
  formatDateTime(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  },
  getStatusBadge(status) {
    const map = {
      pending: 'status-pending', confirmed: 'status-confirmed',
      completed: 'status-completed', cancelled: 'status-cancelled'
    };
    return `<span class="status-badge ${map[status] || ''}">${status}</span>`;
  },
  getRatingStars(rating) {
    const full = Math.floor(rating);
    const half = rating % 1 >= 0.5;
    let stars = '★'.repeat(full);
    if (half) stars += '½';
    return `<span class="rating-stars">${stars}</span> <span style="font-size:12px;color:var(--gray-500)">${rating.toFixed(1)}</span>`;
  },
  truncate(str, len = 80) { return str && str.length > len ? str.substring(0, len) + '…' : (str || ''); },
  debounce(fn, delay = 300) {
    let timeout;
    return (...args) => { clearTimeout(timeout); timeout = setTimeout(() => fn(...args), delay); };
  },
  renderNavbar(activePage = '') {
    const user = Auth.getUser();
    const isAdmin = user?.role === 'admin';
    const navLinks = isAdmin ? [
      { href: '/pages/admin-dashboard.html', label: '📊 Dashboard' },
      { href: '/pages/add-hospital.html', label: '🏥 Add Hospital' },
      { href: '/pages/add-doctor.html', label: '👨‍⚕️ Add Doctor' },
      { href: '/pages/manage-appointments.html', label: '📅 Appointments' },
    ] : [
      { href: '/pages/patient-dashboard.html', label: '🏠 Dashboard' },
      { href: '/pages/hospitals.html', label: '🏥 Hospitals' },
      { href: '/pages/doctors.html', label: '👨‍⚕️ Doctors' },
      { href: '/pages/appointment-booking.html', label: '📅 Book Appointment' },
      { href: '/pages/blood-donation.html', label: '🩸 Blood Donation' },
    ];
    return `
      <nav class="navbar">
        <div class="navbar-inner">
          <a href="${isAdmin ? '/pages/admin-dashboard.html' : '/pages/patient-dashboard.html'}" class="navbar-brand">
            <div class="brand-icon">✚</div> MediConnect
          </a>
          <ul class="navbar-nav md-hidden">
            ${navLinks.map(l => `<li><a href="${l.href}" class="${activePage === l.label ? 'active' : ''}">${l.label}</a></li>`).join('')}
          </ul>
          <div class="navbar-actions">
            ${user ? `
              <div class="user-badge">
                <div class="avatar">${user.name.charAt(0).toUpperCase()}</div>
                ${user.name.split(' ')[0]}
              </div>
              <button class="btn btn-sm btn-secondary" onclick="Auth.logout()">Logout</button>
            ` : `<a href="/pages/login.html" class="btn btn-sm btn-primary">Login</a>`}
          </div>
        </div>
      </nav>`;
  },
  renderSidebar(activePage, role = 'patient') {
    const adminLinks = [
      { href: '/pages/admin-dashboard.html', icon: '📊', label: 'Dashboard' },
      { href: '/pages/add-hospital.html', icon: '🏥', label: 'Add Hospital' },
      { href: '/pages/add-doctor.html', icon: '👨‍⚕️', label: 'Add Doctor' },
      { href: '/pages/manage-appointments.html', icon: '📅', label: 'Appointments' },
      { href: '/pages/blood-donation.html', icon: '🩸', label: 'Blood Donors' },
      { href: '/pages/hospitals.html', icon: '🗂️', label: 'All Hospitals' },
    ];
    const patientLinks = [
      { href: '/pages/patient-dashboard.html', icon: '🏠', label: 'Dashboard' },
      { href: '/pages/hospitals.html', icon: '🏥', label: 'Find Hospitals' },
      { href: '/pages/doctors.html', icon: '👨‍⚕️', label: 'Doctors' },
      { href: '/pages/appointment-booking.html', icon: '📅', label: 'Book Appointment' },
      { href: '/pages/blood-donation.html', icon: '🩸', label: 'Blood Donation' },
    ];
    const links = role === 'admin' ? adminLinks : patientLinks;
    return `
      <aside class="sidebar">
        <div class="sidebar-section-title">Navigation</div>
        <ul class="sidebar-menu">
          ${links.map(l => `<li><a href="${l.href}" class="${activePage === l.label ? 'active' : ''}"><span class="icon">${l.icon}</span>${l.label}</a></li>`).join('')}
        </ul>
        <div class="sidebar-section-title" style="margin-top:24px">Account</div>
        <ul class="sidebar-menu">
          <li><a href="#" onclick="Auth.logout()"><span class="icon">🚪</span>Logout</a></li>
        </ul>
      </aside>`;
  }
};

// ============================================================
// Hospital Card Renderer
// ============================================================
function renderHospitalCard(h) {
  const occupancy = h.crowd_data?.occupancy_percent || 0;
  const barClass = occupancy < 50 ? 'low' : occupancy < 80 ? 'medium' : 'high';
  return `
    <div class="card hospital-card" onclick="window.location.href='/pages/hospitals.html?id=${h.id}'">
      <div class="card-img-top">
        🏥
        ${h.emergency_available ? '<span class="emergency-badge">🚨 Emergency</span>' : ''}
      </div>
      <div class="card-body">
        <h4 style="margin-bottom:4px">${h.hospital_name}</h4>
        <p class="text-sm text-muted" style="margin-bottom:10px">📍 ${h.address}</p>
        <div class="hospital-meta">
          <span class="meta-tag">🛏 ${h.total_beds} Beds</span>
          <span class="meta-tag">📍 ${h.location_display || h.location}</span>
          ${h.rating ? `<span class="meta-tag">⭐ ${h.rating.toFixed(1)}</span>` : ''}
        </div>
        <div class="crowd-monitor" style="margin-top:12px;padding:14px">
          <h4 style="font-size:10px">Live Crowd Status</h4>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div class="crowd-stat">
              <div class="value" style="font-size:1.6rem">${h.crowd_data?.current_waiting || 0}</div>
              <div class="label">Waiting</div>
            </div>
            <div class="crowd-stat">
              <div class="value" style="font-size:1.6rem">${h.crowd_data?.estimated_wait_minutes || 0}m</div>
              <div class="label">Est. Wait</div>
            </div>
            <div class="crowd-stat">
              <div class="value" style="font-size:1.6rem">${occupancy}%</div>
              <div class="label">Capacity</div>
            </div>
          </div>
          <div class="crowd-bar" style="margin-top:10px">
            <div class="crowd-bar-fill ${barClass}" style="width:${occupancy}%"></div>
          </div>
        </div>
      </div>
    </div>`;
}

function renderDoctorCard(d, showBook = true) {
  return `
    <div class="card doctor-card" style="padding:20px">
      <div style="display:flex;gap:16px;align-items:flex-start">
        <div class="doctor-avatar">👨‍⚕️</div>
        <div class="doctor-info">
          <h4 style="margin-bottom:4px">Dr. ${d.doctor_name}</h4>
          <p class="text-sm" style="color:var(--primary);font-weight:600;margin-bottom:6px">${d.specialization}</p>
          <p class="text-sm text-muted">${d.hospital_name}</p>
          <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px">
            <span class="meta-tag">🏅 ${d.experience} yrs exp</span>
            <span class="meta-tag">📅 ${d.schedule || 'Mon-Sat'}</span>
            ${d.consultation_fee ? `<span class="meta-tag">💰 ₹${d.consultation_fee}</span>` : ''}
          </div>
          <div style="margin-top:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px">
            <span class="availability-pill ${d.availability ? 'available' : 'unavailable'}">
              ${d.availability ? 'Available' : 'Unavailable'}
            </span>
            ${showBook && d.availability ? `<a href="/pages/appointment-booking.html?doctor_id=${d.id}&hospital_id=${d.hospital_id}" class="btn btn-sm btn-primary">Book Now</a>` : ''}
          </div>
        </div>
      </div>
    </div>`;
}
