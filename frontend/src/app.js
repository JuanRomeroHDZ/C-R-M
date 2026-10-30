document.addEventListener('DOMContentLoaded', () => {
  const dotBackend = document.getElementById('dot-backend');
  const valBackend = document.getElementById('val-backend');
  const dotDb = document.getElementById('dot-db');
  const valDb = document.getElementById('val-db');
  const dotRedis = document.getElementById('dot-redis');
  const valRedis = document.getElementById('val-redis');
  const btnRefresh = document.getElementById('btn-refresh');

  async function fetchHealth() {
    try {
      valBackend.textContent = 'Verificando...';
      const response = await fetch('/health');
      if (!response.ok && response.status !== 503) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // Backend
      if (data.services && data.services.backend === 'online') {
        dotBackend.className = 'status-dot online';
        valBackend.textContent = 'En linea';
      } else {
        dotBackend.className = 'status-dot error';
        valBackend.textContent = 'Error';
      }

      // Database
      if (data.services && data.services.postgres && data.services.postgres.status === 'connected') {
        dotDb.className = 'status-dot online';
        valDb.textContent = 'Conectado';
      } else {
        dotDb.className = 'status-dot error';
        valDb.textContent = 'Desconectado';
      }

      // Redis
      if (data.services && data.services.redis && data.services.redis.status === 'connected') {
        dotRedis.className = 'status-dot online';
        valRedis.textContent = 'Conectado';
      } else {
        dotRedis.className = 'status-dot error';
        valRedis.textContent = 'Desconectado';
      }
    } catch (error) {
      dotBackend.className = 'status-dot error';
      valBackend.textContent = 'Inaccesible';
      dotDb.className = 'status-dot error';
      valDb.textContent = 'Inaccesible';
      dotRedis.className = 'status-dot error';
      valRedis.textContent = 'Inaccesible';
    }
  }

  if (btnRefresh) {
    btnRefresh.addEventListener('click', fetchHealth);
  }

  fetchHealth();
  setInterval(fetchHealth, 10000);
});
