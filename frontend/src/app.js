// ==============================================================================
// Sistema de Captacion, Prospeccion y CRM Local - Frontend Application
// Version: 4.0.0
// Estilo: Notion / Obsidian Slate Neutro (Cero Emojis, Iconos Lucide SVG)
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    leads: [],
    filteredLeads: [],
    events: [],
    settings: {
      whatsapp_template: 'Hola, buen dia.',
      lan_ip: '192.168.100.96',
      proxy_port: '32662',
      lan_url: 'http://192.168.100.96:32662',
      local_url: 'http://localhost:32662'
    },
    activeCategory: '',
    activeStage: '',
    searchQuery: '',
    currentView: 'leads',
    selectedLeadForAudit: null
  };

  // DOM Elements - Shell & Navigation
  const pageTitle = document.getElementById('page-title');
  const navBtnLeads = document.getElementById('nav-btn-leads');
  const navBtnCalendar = document.getElementById('nav-btn-calendar');
  const navBtnSettings = document.getElementById('nav-btn-settings');
  const mobNavLeads = document.getElementById('mob-nav-leads');
  const mobNavCalendar = document.getElementById('mob-nav-calendar');
  const mobNavSettings = document.getElementById('mob-nav-settings');
  const badgeLeadsCount = document.getElementById('badge-leads-count');
  const badgeEventsCount = document.getElementById('badge-events-count');
  const liveReloadDot = document.getElementById('live-reload-dot');
  const liveReloadText = document.getElementById('live-reload-text');
  const diagWsStatus = document.getElementById('diag-ws-status');
  const sidebarLanLabel = document.getElementById('sidebar-lan-label');

  // DOM Elements - Views
  const viewLeads = document.getElementById('view-leads');
  const viewCalendar = document.getElementById('view-calendar');
  const viewSettings = document.getElementById('view-settings');

  // DOM Elements - Controls & Filters
  const leadsSearchInput = document.getElementById('leads-search-input');
  const categoryFilters = document.getElementById('category-filters');
  const stageFilterSelect = document.getElementById('stage-filter-select');
  const leadsGridContainer = document.getElementById('leads-grid-container');
  const leadsEmptyState = document.getElementById('leads-empty-state');
  const statTotalLeads = document.getElementById('stat-total-leads');
  const statWhatsappLeads = document.getElementById('stat-whatsapp-leads');
  const statQualifiedLeads = document.getElementById('stat-qualified-leads');

  // DOM Elements - Calendar
  const calendarEventsList = document.getElementById('calendar-events-list');
  const calendarEmptyState = document.getElementById('calendar-empty-state');
  const imminentAlertsBanner = document.getElementById('imminent-alerts-banner');
  const btnRequestNotifications = document.getElementById('btn-request-notifications');
  const topBtnNewEvent = document.getElementById('top-btn-new-event');
  const btnCalendarAddEvent = document.getElementById('btn-calendar-add-event');
  const topBtnRefresh = document.getElementById('top-btn-refresh');

  // DOM Elements - Settings
  const settingsWhatsappTemplate = document.getElementById('settings-whatsapp-template');
  const btnSaveWhatsappTemplate = document.getElementById('btn-save-whatsapp-template');
  const linkLocalPc = document.getElementById('link-local-pc');
  const linkLanMobile = document.getElementById('link-lan-mobile');
  const btnCopyLanUrl = document.getElementById('btn-copy-lan-url');

  // DOM Elements - Modals
  const modalEvent = document.getElementById('modal-event');
  const modalEventClose = document.getElementById('modal-event-close');
  const modalEventCancel = document.getElementById('modal-event-cancel');
  const formNewEvent = document.getElementById('form-new-event');
  const eventLeadIdSelect = document.getElementById('event-lead-id');
  const eventStartTimeInput = document.getElementById('event-start-time');
  const eventEndTimeInput = document.getElementById('event-end-time');

  const modalAudit = document.getElementById('modal-audit');
  const modalAuditClose = document.getElementById('modal-audit-close');
  const modalAuditDone = document.getElementById('modal-audit-done');
  const modalAuditLeadName = document.getElementById('modal-audit-lead-name');
  const modalHealthScore = document.getElementById('modal-health-score');
  const modalProbScore = document.getElementById('modal-prob-score');
  const modalChannelsList = document.getElementById('modal-channels-list');
  const modalSalesArguments = document.getElementById('modal-sales-arguments');
  const modalActivityLog = document.getElementById('modal-activity-log');

  // ============================================================================
  // 1. Live Reload WebSocket Client
  // ============================================================================
  function initLiveReload() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/dev/live-reload`;
    let ws = null;
    let retryInterval = 3000;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (liveReloadDot) liveReloadDot.style.backgroundColor = 'var(--badge-green-text)';
          if (liveReloadText) liveReloadText.textContent = 'Conectado en vivo';
          if (diagWsStatus) diagWsStatus.textContent = 'Conectado';
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.action === 'reload') {
              console.log('[DevReload] Recibida senal de recarga automatica.');
              window.location.reload();
            }
          } catch (e) {
            // Mensaje de texto plano
            if (event.data === 'reload') {
              window.location.reload();
            }
          }
        };

        ws.onclose = () => {
          if (liveReloadDot) liveReloadDot.style.backgroundColor = 'var(--badge-amber-text)';
          if (liveReloadText) liveReloadText.textContent = 'Reconectando...';
          if (diagWsStatus) diagWsStatus.textContent = 'Reconectando';
          setTimeout(connect, retryInterval);
        };

        ws.onerror = () => {
          ws.close();
        };
      } catch (err) {
        setTimeout(connect, retryInterval);
      }
    }

    connect();
  }

  // ============================================================================
  // 2. Navigation & View Switcher
  // ============================================================================
  function switchView(viewName) {
    state.currentView = viewName;

    // Toggle panels
    if (viewLeads) viewLeads.style.display = viewName === 'leads' ? 'block' : 'none';
    if (viewCalendar) viewCalendar.style.display = viewName === 'calendar' ? 'flex' : 'none';
    if (viewSettings) viewSettings.style.display = viewName === 'settings' ? 'block' : 'none';

    // Update Desktop Nav Active Classes
    [navBtnLeads, navBtnCalendar, navBtnSettings].forEach(btn => {
      if (btn) {
        if (btn.dataset.view === viewName) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      }
    });

    // Update Mobile Nav Active Classes
    [mobNavLeads, mobNavCalendar, mobNavSettings].forEach(btn => {
      if (btn) {
        if (btn.dataset.view === viewName) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      }
    });

    // Update Top Title
    if (pageTitle) {
      if (viewName === 'leads') pageTitle.textContent = 'Directorio de Prospectos Calificados';
      else if (viewName === 'calendar') pageTitle.textContent = 'Agenda de Citas y Seguimientos';
      else if (viewName === 'settings') pageTitle.textContent = 'Configuracion de Canales y Red';
    }

    if (viewName === 'calendar') {
      loadCalendarEvents();
      loadAlerts();
    }
  }

  // Bind Navigation Listeners
  [navBtnLeads, mobNavLeads].forEach(el => el && el.addEventListener('click', () => switchView('leads')));
  [navBtnCalendar, mobNavCalendar].forEach(el => el && el.addEventListener('click', () => switchView('calendar')));
  [navBtnSettings, mobNavSettings].forEach(el => el && el.addEventListener('click', () => switchView('settings')));

  // ============================================================================
  // 3. Data Fetching
  // ============================================================================
  async function loadSettings() {
    try {
      const res = await fetch('/api/v1/settings');
      if (res.ok) {
        const data = await res.json();
        state.settings = data;

        if (settingsWhatsappTemplate) {
          settingsWhatsappTemplate.value = data.whatsapp_template || 'Hola, buen dia.';
        }
        if (linkLocalPc) {
          linkLocalPc.href = data.local_url;
          linkLocalPc.textContent = data.local_url;
        }
        if (linkLanMobile) {
          linkLanMobile.href = data.lan_url;
          linkLanMobile.textContent = data.lan_url;
        }
        if (sidebarLanLabel) {
          sidebarLanLabel.textContent = `${data.lan_ip}:${data.proxy_port}`;
        }
      }
    } catch (err) {
      console.error('[Settings] Error al cargar configuracion:', err);
    }
  }

  async function loadLeads() {
    try {
      const res = await fetch('/api/v1/leads?limit=200');
      if (res.ok) {
        const data = await res.json();
        state.leads = data;
        populateLeadSelect(data);
        applyFilters();
      }
    } catch (err) {
      console.error('[Leads] Error al cargar prospectos:', err);
    }
  }

  async function loadCalendarEvents() {
    try {
      const res = await fetch('/api/v1/calendar/events');
      if (res.ok) {
        const events = await res.json();
        state.events = events;
        renderCalendarEvents(events);
        if (badgeEventsCount) {
          const pending = events.filter(e => e.status === 'PENDIENTE').length;
          if (pending > 0) {
            badgeEventsCount.textContent = pending;
            badgeEventsCount.style.display = 'inline-block';
          } else {
            badgeEventsCount.style.display = 'none';
          }
        }
      }
    } catch (err) {
      console.error('[Calendar] Error al cargar eventos:', err);
    }
  }

  async function loadAlerts() {
    try {
      const res = await fetch('/api/v1/calendar/alerts');
      if (res.ok) {
        const alerts = await res.json();
        if (imminentAlertsBanner) {
          if (alerts.imminent_alerts && alerts.imminent_alerts.length > 0) {
            const first = alerts.imminent_alerts[0];
            imminentAlertsBanner.innerHTML = `
              <strong>Alerta de Cita Inminente:</strong> "${escapeHtml(first.title)}" inicia a las ${formatTime(first.start_time)}.
            `;
            imminentAlertsBanner.style.display = 'block';

            // Disparar notificacion de escritorio si esta permitido
            if (Notification.permission === 'granted') {
              new Notification('Cita Inminente - CRM', {
                body: `${first.title} con ${first.lead_name || 'prospecto'} a las ${formatTime(first.start_time)}`,
                icon: '/favicon.ico'
              });
            }
          } else {
            imminentAlertsBanner.style.display = 'none';
          }
        }
      }
    } catch (err) {
      console.error('[Alerts] Error al cargar alertas:', err);
    }
  }

  // ============================================================================
  // 4. Filtering & Rendering Leads
  // ============================================================================
  function applyFilters() {
    let filtered = [...state.leads];

    // Filter by Category
    if (state.activeCategory) {
      filtered = filtered.filter(l => l.category_slug === state.activeCategory);
    }

    // Filter by Stage
    if (state.activeStage) {
      filtered = filtered.filter(l => l.lifecycle_stage === state.activeStage);
    }

    // Filter by Search Query
    if (state.searchQuery.trim() !== '') {
      const q = state.searchQuery.toLowerCase().trim();
      filtered = filtered.filter(l => {
        const name = (l.name || '').toLowerCase();
        const address = (l.address_raw || '').toLowerCase();
        const phone = (l.phone_raw || '').toLowerCase();
        return name.includes(q) || address.includes(q) || phone.includes(q);
      });
    }

    state.filteredLeads = filtered;
    updateStats(filtered);
    renderLeads(filtered);
  }

  function updateStats(filtered) {
    if (badgeLeadsCount) badgeLeadsCount.textContent = state.leads.length;
    if (statTotalLeads) statTotalLeads.textContent = filtered.length;
    if (statWhatsappLeads) {
      const withWa = filtered.filter(l => l.has_whatsapp !== false && (l.phone_e164 || l.phone_raw)).length;
      statWhatsappLeads.textContent = withWa;
    }
    if (statQualifiedLeads) {
      const qualified = filtered.filter(l => l.acceptance_probability_pct && l.acceptance_probability_pct > 0).length;
      statQualifiedLeads.textContent = qualified;
    }
  }

  function renderLeads(leads) {
    if (!leadsGridContainer) return;
    leadsGridContainer.innerHTML = '';

    if (leads.length === 0) {
      if (leadsEmptyState) leadsEmptyState.style.display = 'block';
      return;
    }

    if (leadsEmptyState) leadsEmptyState.style.display = 'none';

    leads.forEach(lead => {
      const card = createLeadCardElement(lead);
      leadsGridContainer.appendChild(card);
    });
  }

  function createLeadCardElement(lead) {
    const card = document.createElement('div');
    card.className = 'lead-card';
    card.id = `lead-card-${lead.id}`;

    // Score classification
    const prob = lead.acceptance_probability_pct != null ? Math.round(lead.acceptance_probability_pct) : 0;
    let scoreBadgeClass = 'low';
    if (prob >= 70) scoreBadgeClass = 'high';
    else if (prob >= 40) scoreBadgeClass = 'med';

    // Arguments or findings
    const args = Array.isArray(lead.sales_arguments) ? lead.sales_arguments.slice(0, 2) : [];
    let findingsHtml = '';
    if (args.length > 0) {
      findingsHtml = `
        <div class="findings-box">
          <ul>
            ${args.map(a => `<li>${escapeHtml(a)}</li>`).join('')}
          </ul>
        </div>
      `;
    }

    // Phone / WhatsApp resolution
    const phoneDisplay = lead.phone_e164 || lead.phone_raw || 'Sin telefono registrado';
    const cleanPhone = (lead.phone_e164 || lead.phone_raw || '').replace(/[^0-9]/g, '');
    const hasPhone = cleanPhone.length >= 10;
    const isWaAvailable = lead.has_whatsapp !== false && hasPhone;

    // Contact action buttons
    const template = state.settings.whatsapp_template || 'Hola, buen dia.';
    const customMessage = template.replace(/{nombre}/g, lead.name || '');
    const waUrl = isWaAvailable ? `https://wa.me/${cleanPhone}?text=${encodeURIComponent(customMessage)}` : '#';

    // Social Links
    const socials = lead.social_links || {};
    let socialButtonsHtml = '';
    for (const [platform, link] of Object.entries(socials)) {
      if (link && typeof link === 'string' && link.startsWith('http')) {
        socialButtonsHtml += `
          <a href="${escapeHtml(link)}" target="_blank" rel="noopener noreferrer" class="btn-icon-only" title="${platform}">
            <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-share-2"/></svg>
          </a>
        `;
      }
    }

    // Website button
    let websiteButtonHtml = '';
    if (lead.website) {
      websiteButtonHtml = `
        <a href="${escapeHtml(lead.website)}" target="_blank" rel="noopener noreferrer" class="btn-icon-only" title="Sitio Web">
          <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-globe"/></svg>
        </a>
      `;
    }

    card.innerHTML = `
      <div>
        <div class="card-top">
          <div>
            <div class="lead-name">${escapeHtml(lead.name)}</div>
            <div class="lead-cat">${escapeHtml(lead.primary_category || lead.category_slug)} &bull; ${escapeHtml(lead.lifecycle_stage)}</div>
          </div>
          <div class="score-badge ${scoreBadgeClass}" title="Probabilidad de aceptacion de propuesta">
            ${prob}% Exito
          </div>
        </div>

        <div class="meta-stats" style="margin-top: 8px;">
          <span style="display: flex; align-items: center; gap: 4px;">
            <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
            ${escapeHtml(phoneDisplay)}
          </span>
          ${lead.rating ? `<span>&bull;</span> <span>${lead.rating.toFixed(1)} (${lead.review_count || 0})</span>` : ''}
        </div>

        ${lead.address_raw ? `
          <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px; line-height: 1.3;">
            ${escapeHtml(lead.address_raw)}
          </div>
        ` : ''}

        ${findingsHtml}
      </div>

      <div class="action-bar">
        ${isWaAvailable ? `
          <button class="btn-action btn-whatsapp" data-action="whatsapp" data-id="${lead.id}" data-url="${waUrl}">
            <svg style="width:14px;height:14px;" stroke="currentColor" fill="none"><use href="#icon-message-circle"/></svg>
            WhatsApp
          </button>
          <button class="btn-secondary-action" data-action="mark-no-wa" data-id="${lead.id}" title="Desactivar WhatsApp si es solo linea fija">
            Sin WhatsApp
          </button>
        ` : `
          <button class="btn-action disabled" title="Canal de WhatsApp no disponible">
            Solo linea fija
          </button>
        `}

        ${hasPhone ? `
          <button class="btn-action" data-action="call" data-id="${lead.id}" data-phone="${cleanPhone}">
            <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-phone"/></svg>
            Llamar
          </button>
        ` : ''}

        ${lead.email ? `
          <a href="mailto:${escapeHtml(lead.email)}" class="btn-icon-only" title="${escapeHtml(lead.email)}">
            <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-mail"/></svg>
          </a>
        ` : ''}

        ${websiteButtonHtml}
        ${socialButtonsHtml}

        <button class="btn-action" data-action="schedule" data-id="${lead.id}" style="margin-left: auto;">
          <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-calendar"/></svg>
          Agendar
        </button>

        <button class="btn-icon-only" data-action="audit" data-id="${lead.id}" title="Ver auditoria y argumentos completos">
          <svg style="width:13px;height:13px;" stroke="currentColor" fill="none"><use href="#icon-activity"/></svg>
        </button>
      </div>
    `;

    // Bind card action buttons
    bindCardActions(card, lead);

    return card;
  }

  function bindCardActions(card, lead) {
    // WhatsApp Click
    const waBtn = card.querySelector('[data-action="whatsapp"]');
    if (waBtn) {
      waBtn.addEventListener('click', async () => {
        const url = waBtn.dataset.url;
        // 1. Log interaction in background
        try {
          await fetch(`/api/v1/leads/${lead.id}/interact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              channel: 'WHATSAPP',
              interaction_type: 'OUTBOUND_MESSAGE',
              notes: 'Apertura de conversacion via redireccion wa.me'
            })
          });
          // Update local lifecycle stage to FIRST_CONTACT if qualified
          if (lead.lifecycle_stage === 'QUALIFIED' || lead.lifecycle_stage === 'EXTRACTED' || lead.lifecycle_stage === 'AUDITED') {
            lead.lifecycle_stage = 'FIRST_CONTACT';
            const catElem = card.querySelector('.lead-cat');
            if (catElem) {
              catElem.textContent = `${lead.primary_category || lead.category_slug} • FIRST_CONTACT`;
            }
          }
        } catch (e) {
          console.error('[Interact] Error registrando interaccion de WhatsApp:', e);
        }
        // 2. Open universal WhatsApp link without auto-send
        window.open(url, '_blank');
      });
    }

    // Call Click
    const callBtn = card.querySelector('[data-action="call"]');
    if (callBtn) {
      callBtn.addEventListener('click', async () => {
        const phone = callBtn.dataset.phone;
        try {
          await fetch(`/api/v1/leads/${lead.id}/interact`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              channel: 'LLAMADA',
              interaction_type: 'OUTBOUND_CALL',
              notes: 'Marcado telefonico tradicional iniciado'
            })
          });
        } catch (e) {
          console.error('[Interact] Error registrando llamada:', e);
        }
        window.location.href = `tel:+${phone}`;
      });
    }

    // 1-Click "Sin WhatsApp" (Mark no whatsapp)
    const noWaBtn = card.querySelector('[data-action="mark-no-wa"]');
    if (noWaBtn) {
      noWaBtn.addEventListener('click', async () => {
        try {
          const res = await fetch(`/api/v1/leads/${lead.id}/mark-no-whatsapp`, { method: 'POST' });
          if (res.ok) {
            lead.has_whatsapp = false;
            // Re-render card
            const newCard = createLeadCardElement(lead);
            card.replaceWith(newCard);
          }
        } catch (e) {
          console.error('[MarkNoWa] Error al actualizar estado de WhatsApp:', e);
        }
      });
    }

    // Agendar Cita
    const schedBtn = card.querySelector('[data-action="schedule"]');
    if (schedBtn) {
      schedBtn.addEventListener('click', () => {
        openNewEventModal(lead.id);
      });
    }

    // Auditoria Tecnica Modal
    const auditBtn = card.querySelector('[data-action="audit"]');
    if (auditBtn) {
      auditBtn.addEventListener('click', () => {
        openAuditModal(lead);
      });
    }
  }

  // ============================================================================
  // 5. Calendar Management & Rendering
  // ============================================================================
  function renderCalendarEvents(events) {
    if (!calendarEventsList) return;
    calendarEventsList.innerHTML = '';

    if (events.length === 0) {
      if (calendarEmptyState) calendarEmptyState.style.display = 'block';
      return;
    }

    if (calendarEmptyState) calendarEmptyState.style.display = 'none';

    events.forEach(evt => {
      const item = document.createElement('div');
      item.className = 'event-card';

      const startDate = new Date(evt.start_time);
      const dateStr = startDate.toLocaleDateString('es-MX', { weekday: 'short', month: 'short', day: 'numeric' });
      const timeStr = startDate.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });

      item.innerHTML = `
        <div class="event-info">
          <div class="event-title">${escapeHtml(evt.title)}</div>
          <div class="event-meta">
            <span class="score-badge med">${escapeHtml(evt.event_type)}</span>
            <span>&bull;</span>
            <span style="font-family: var(--font-mono);">${dateStr} a las ${timeStr}</span>
            ${evt.lead_name ? `<span>&bull;</span> <strong>${escapeHtml(evt.lead_name)}</strong>` : ''}
          </div>
          ${evt.notes ? `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">${escapeHtml(evt.notes)}</div>` : ''}
        </div>

        <div class="event-actions">
          ${evt.status === 'PENDIENTE' ? `
            <button class="btn-action" data-evt-action="complete" data-id="${evt.id}" style="font-size: 11px;">
              <svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-check"/></svg>
              Completar
            </button>
            <button class="btn-secondary-action" data-evt-action="cancel" data-id="${evt.id}">
              Cancelar
            </button>
          ` : `
            <span class="score-badge ${evt.status === 'COMPLETADO' ? 'high' : 'low'}">${escapeHtml(evt.status)}</span>
          `}
        </div>
      `;

      // Event Card Action Handlers
      const completeBtn = item.querySelector('[data-evt-action="complete"]');
      if (completeBtn) {
        completeBtn.addEventListener('click', async () => {
          await updateEventStatus(evt.id, 'COMPLETADO');
        });
      }

      const cancelBtn = item.querySelector('[data-evt-action="cancel"]');
      if (cancelBtn) {
        cancelBtn.addEventListener('click', async () => {
          await updateEventStatus(evt.id, 'CANCELADO');
        });
      }

      calendarEventsList.appendChild(item);
    });
  }

  async function updateEventStatus(eventId, status) {
    try {
      const res = await fetch(`/api/v1/calendar/events/${eventId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (res.ok) {
        loadCalendarEvents();
      }
    } catch (e) {
      console.error('[Calendar] Error actualizando estado de evento:', e);
    }
  }

  function populateLeadSelect(leads) {
    if (!eventLeadIdSelect) return;
    eventLeadIdSelect.innerHTML = '<option value="">Selecciona un prospecto...</option>';
    leads.forEach(l => {
      const opt = document.createElement('option');
      opt.value = l.id;
      opt.textContent = `${l.name} (${l.phone_e164 || l.phone_raw || 'Sin tel'})`;
      eventLeadIdSelect.appendChild(opt);
    });
  }

  function openNewEventModal(preselectedLeadId = null) {
    if (!modalEvent) return;
    if (preselectedLeadId && eventLeadIdSelect) {
      eventLeadIdSelect.value = preselectedLeadId;
    }

    // Set default times (Tomorrow 10:00 AM)
    const now = new Date();
    now.setHours(now.getHours() + 2);
    now.setMinutes(0, 0, 0);

    const end = new Date(now);
    end.setHours(end.getHours() + 1);

    if (eventStartTimeInput) eventStartTimeInput.value = formatDateTimeLocal(now);
    if (eventEndTimeInput) eventEndTimeInput.value = formatDateTimeLocal(end);

    modalEvent.style.display = 'flex';
  }

  // Handle Event Form Submit
  if (formNewEvent) {
    formNewEvent.addEventListener('submit', async (e) => {
      e.preventDefault();
      const leadId = eventLeadIdSelect.value;
      const title = document.getElementById('event-title').value;
      const eventType = document.getElementById('event-type').value;
      const startTime = eventStartTimeInput.value;
      const endTime = eventEndTimeInput.value;
      const notes = document.getElementById('event-notes').value;

      try {
        const res = await fetch('/api/v1/calendar/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            lead_id: leadId,
            title: title,
            event_type: eventType,
            start_time: new Date(startTime).toISOString(),
            end_time: new Date(endTime).toISOString(),
            notes: notes
          })
        });

        if (res.ok) {
          modalEvent.style.display = 'none';
          formNewEvent.reset();
          loadCalendarEvents();
          loadAlerts();
        }
      } catch (err) {
        console.error('[Calendar] Error al crear evento:', err);
      }
    });
  }

  if (modalEventClose) modalEventClose.addEventListener('click', () => modalEvent.style.display = 'none');
  if (modalEventCancel) modalEventCancel.addEventListener('click', () => modalEvent.style.display = 'none');
  if (topBtnNewEvent) topBtnNewEvent.addEventListener('click', () => openNewEventModal());
  if (btnCalendarAddEvent) btnCalendarAddEvent.addEventListener('click', () => openNewEventModal());

  // ============================================================================
  // 6. Technical Audit Modal
  // ============================================================================
  async function openAuditModal(lead) {
    if (!modalAudit) return;
    state.selectedLeadForAudit = lead;

    if (modalAuditLeadName) modalAuditLeadName.textContent = lead.name;
    if (modalHealthScore) modalHealthScore.textContent = `${lead.technical_health_score != null ? Math.round(lead.technical_health_score) : 0}/100`;
    if (modalProbScore) modalProbScore.textContent = `${lead.acceptance_probability_pct != null ? Math.round(lead.acceptance_probability_pct) : 0}%`;

    // Channels
    if (modalChannelsList) {
      modalChannelsList.innerHTML = '';
      const st = lead.channels_status || {};
      for (const [ch, status] of Object.entries(st)) {
        const badge = document.createElement('span');
        badge.className = `score-badge ${status === 'DISPONIBLE' ? 'high' : 'low'}`;
        badge.textContent = `${ch.toUpperCase()}: ${status}`;
        modalChannelsList.appendChild(badge);
      }
    }

    // Arguments
    if (modalSalesArguments) {
      const args = Array.isArray(lead.sales_arguments) ? lead.sales_arguments : [];
      if (args.length > 0) {
        modalSalesArguments.innerHTML = `
          <ul>
            ${args.map(a => `<li>${escapeHtml(a)}</li>`).join('')}
          </ul>
        `;
      } else {
        modalSalesArguments.innerHTML = '<span style="color:var(--text-muted);">Sin argumentos calculados.</span>';
      }
    }

    // Activity log
    if (modalActivityLog) {
      modalActivityLog.textContent = 'Consultando interacciones...';
      try {
        const res = await fetch(`/api/v1/leads/${lead.id}/activity`);
        if (res.ok) {
          const acts = await res.json();
          if (acts.length > 0) {
            modalActivityLog.innerHTML = acts.map(a => {
              const dt = new Date(a.created_at).toLocaleString('es-MX');
              return `<div style="margin-bottom: 4px;"><strong>${dt}:</strong> [${escapeHtml(a.channel)}] ${escapeHtml(a.notes || a.interaction_type)}</div>`;
            }).join('');
          } else {
            modalActivityLog.textContent = 'Sin historial de interacciones registrado para este contacto.';
          }
        }
      } catch (e) {
        modalActivityLog.textContent = 'No se pudo consultar el registro de actividad.';
      }
    }

    modalAudit.style.display = 'flex';
  }

  if (modalAuditClose) modalAuditClose.addEventListener('click', () => modalAudit.style.display = 'none');
  if (modalAuditDone) modalAuditDone.addEventListener('click', () => modalAudit.style.display = 'none');

  // ============================================================================
  // 7. Settings Handlers
  // ============================================================================
  if (btnSaveWhatsappTemplate) {
    btnSaveWhatsappTemplate.addEventListener('click', async () => {
      const text = settingsWhatsappTemplate.value;
      try {
        btnSaveWhatsappTemplate.textContent = 'Guardando...';
        const res = await fetch('/api/v1/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ whatsapp_template: text })
        });
        if (res.ok) {
          state.settings.whatsapp_template = text;
          btnSaveWhatsappTemplate.textContent = 'Guardado';
          setTimeout(() => {
            btnSaveWhatsappTemplate.textContent = 'Guardar Plantilla';
          }, 1500);
          // Refresh leads cards so new template applies to URLs
          renderLeads(state.filteredLeads);
        }
      } catch (err) {
        btnSaveWhatsappTemplate.textContent = 'Error al guardar';
      }
    });
  }

  if (btnCopyLanUrl) {
    btnCopyLanUrl.addEventListener('click', () => {
      if (state.settings.lan_url) {
        navigator.clipboard.writeText(state.settings.lan_url).then(() => {
          btnCopyLanUrl.innerHTML = '<svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-check"/></svg>';
          setTimeout(() => {
            btnCopyLanUrl.innerHTML = '<svg style="width:12px;height:12px;" stroke="currentColor" fill="none"><use href="#icon-copy"/></svg>';
          }, 1500);
        });
      }
    });
  }

  if (btnRequestNotifications) {
    btnRequestNotifications.addEventListener('click', async () => {
      if ('Notification' in window) {
        const perm = await Notification.requestPermission();
        if (perm === 'granted') {
          btnRequestNotifications.textContent = 'Alertas Habilitadas';
          btnRequestNotifications.classList.add('disabled');
        }
      }
    });
  }

  // ============================================================================
  // 8. Filters & Search Handlers
  // ============================================================================
  if (leadsSearchInput) {
    leadsSearchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value;
      applyFilters();
    });
  }

  if (categoryFilters) {
    categoryFilters.querySelectorAll('.filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        categoryFilters.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.activeCategory = btn.dataset.category;
        applyFilters();
      });
    });
  }

  if (stageFilterSelect) {
    stageFilterSelect.addEventListener('change', (e) => {
      state.activeStage = e.target.value;
      applyFilters();
    });
  }

  if (topBtnRefresh) {
    topBtnRefresh.addEventListener('click', () => {
      loadLeads();
      loadCalendarEvents();
      loadAlerts();
    });
  }

  // ============================================================================
  // 9. Utilities
  // ============================================================================
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatTime(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
  }

  function formatDateTimeLocal(date) {
    const pad = (n) => String(n).padStart(2, '0');
    const y = date.getFullYear();
    const m = pad(date.getMonth() + 1);
    const d = pad(date.getDate());
    const h = pad(date.getHours());
    const min = pad(date.getMinutes());
    return `${y}-${m}-${d}T${h}:${min}`;
  }

  // ============================================================================
  // 10. Initialization
  // ============================================================================
  initLiveReload();
  loadSettings();
  loadLeads();
  loadCalendarEvents();
  loadAlerts();
});
