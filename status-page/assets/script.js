/* ============================================================
   Arminda · Painel de acompanhamento
   ============================================================
   Lê status.json e popula a página. Editar o JSON é a única
   ação necessária para atualizar o painel.
   ============================================================ */

(function () {
  'use strict';

  // ----------------------------------------------------------
  // Utilidades
  // ----------------------------------------------------------
  const MESES = [
    'jan', 'fev', 'mar', 'abr', 'mai', 'jun',
    'jul', 'ago', 'set', 'out', 'nov', 'dez'
  ];

  const MESES_LONGO = [
    'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
  ];

  const STATUS_LABEL = {
    concluido: 'Concluído',
    em_andamento: 'Em andamento',
    previsto: 'Previsto'
  };

  /** Converte "2026-04-27" em Date local (sem timezone shift). */
  function parseDate(iso) {
    if (!iso) return null;
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  /** Formata como "27/abr/2026". */
  function fmtData(iso) {
    const d = parseDate(iso);
    if (!d) return '—';
    const dia = String(d.getDate()).padStart(2, '0');
    return `${dia}/${MESES[d.getMonth()]}/${d.getFullYear()}`;
  }

  /** Formata como "27 de abril de 2026". */
  function fmtDataLongo(iso) {
    const d = parseDate(iso);
    if (!d) return '—';
    return `${d.getDate()} de ${MESES_LONGO[d.getMonth()]} de ${d.getFullYear()}`;
  }

  /** Formata como "abr/2026". */
  function fmtMesAno(iso) {
    const d = parseDate(iso);
    if (!d) return '—';
    return `${MESES[d.getMonth()]}/${d.getFullYear()}`;
  }

  /** Diferença em meses entre duas datas. */
  function mesesEntre(a, b) {
    return (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth());
  }

  /** Aplica valores no DOM via [data-bind]. */
  function bindSimples(dados) {
    document.querySelectorAll('[data-bind]').forEach((el) => {
      const path = el.getAttribute('data-bind');
      const valor = path.split('.').reduce(
        (obj, key) => (obj == null ? undefined : obj[key]),
        dados
      );
      if (valor !== undefined && valor !== null) {
        el.textContent = String(valor);
      }
    });
  }

  // ----------------------------------------------------------
  // Renderização: cronograma (Gantt simplificado)
  // ----------------------------------------------------------
  function renderTimeline(blocos) {
    const container = document.getElementById('timeline');
    if (!container) return;

    // Determina a janela total do cronograma
    const datasInicio = blocos.map((b) => parseDate(b.data_inicio)).filter(Boolean);
    const datasFim = blocos
      .map((b) => parseDate(b.data_fim_real || b.data_fim_prevista))
      .filter(Boolean);

    if (datasInicio.length === 0 || datasFim.length === 0) return;

    const inicioGeral = new Date(Math.min(...datasInicio.map((d) => d.getTime())));
    const fimGeral = new Date(Math.max(...datasFim.map((d) => d.getTime())));
    const totalMeses = Math.max(1, mesesEntre(inicioGeral, fimGeral) + 1);

    // Header com escala (4 ticks: início, 1/3, 2/3, fim)
    const header = document.createElement('div');
    header.className = 'timeline-header';
    header.innerHTML = `
      <div class="timeline-header-spacer"></div>
      <div class="timeline-header-spacer"></div>
      <div class="timeline-header-scale">
        ${[0, 0.33, 0.66, 1]
          .map((frac) => {
            const d = new Date(inicioGeral);
            d.setMonth(d.getMonth() + Math.round(totalMeses * frac));
            return `<span class="timeline-header-tick" style="left: ${frac * 100}%">${MESES[d.getMonth()]}/${String(d.getFullYear()).slice(2)}</span>`;
          })
          .join('')}
      </div>
      <div class="timeline-header-spacer"></div>
    `;
    container.appendChild(header);

    // Linhas
    blocos.forEach((bloco) => {
      const inicio = parseDate(bloco.data_inicio);
      const fim = parseDate(bloco.data_fim_real || bloco.data_fim_prevista);
      if (!inicio || !fim) return;

      const offsetPct = (mesesEntre(inicioGeral, inicio) / totalMeses) * 100;
      const widthPct = Math.max(2, ((mesesEntre(inicio, fim) + 1) / totalMeses) * 100);

      const row = document.createElement('div');
      row.className = 'timeline-row';
      row.innerHTML = `
        <span class="timeline-num">${String(bloco.numero).padStart(2, '0')}</span>
        <div class="timeline-info">
          <span class="timeline-info-title">${escapeHtml(bloco.titulo)}</span>
          <span class="timeline-info-period">${escapeHtml(bloco.periodo)}</span>
        </div>
        <div class="timeline-bar-wrapper">
          <div class="timeline-bar-track"></div>
          <div class="timeline-bar status-${bloco.status}"
               style="left: ${offsetPct}%; width: ${widthPct}%"
               title="${escapeHtml(bloco.titulo)} — ${escapeHtml(STATUS_LABEL[bloco.status] || '')}"></div>
        </div>
        <span class="timeline-status status-${bloco.status}">${escapeHtml(STATUS_LABEL[bloco.status] || '')}</span>
      `;
      container.appendChild(row);
    });
  }

  // ----------------------------------------------------------
  // Renderização: detalhe dos blocos
  // ----------------------------------------------------------
  function renderBlocos(blocos) {
    const container = document.getElementById('blocos');
    if (!container) return;

    blocos.forEach((bloco) => {
      const article = document.createElement('article');
      article.className = 'bloco';
      article.id = `bloco-${bloco.numero}`;

      const entregasHtml = (bloco.entregas || [])
        .map((e) => `<li class="bloco-entrega">${escapeHtml(e)}</li>`)
        .join('');

      article.innerHTML = `
        <aside class="bloco-aside">
          <div>
            <span class="bloco-numero-prefix">Etapa</span>
            <span class="bloco-numero">${String(bloco.numero).padStart(2, '0')}</span>
          </div>
          <span class="bloco-status status-${bloco.status}">
            ${escapeHtml(STATUS_LABEL[bloco.status] || '')}
          </span>
          <span class="bloco-periodo">${escapeHtml(bloco.periodo)}</span>
        </aside>
        <div class="bloco-main">
          <h3 class="bloco-titulo">${escapeHtml(bloco.titulo)}</h3>
          <p class="bloco-descricao">${escapeHtml(bloco.descricao)}</p>
          <div class="bloco-progress">
            <div class="bloco-progress-meta">
              <span>Progresso</span>
              <span class="bloco-progress-pct">${bloco.progresso_pct}%</span>
            </div>
            <div class="bloco-progress-bar">
              <div class="bloco-progress-fill" data-progress-bloco="${bloco.numero}"></div>
            </div>
          </div>
          ${
            entregasHtml
              ? `
            <div>
              <p class="bloco-entregas-label">Entregas previstas</p>
              <ul class="bloco-entregas">${entregasHtml}</ul>
            </div>
          `
              : ''
          }
        </div>
      `;
      container.appendChild(article);
    });
  }

  // ----------------------------------------------------------
  // Renderização: changelog
  // ----------------------------------------------------------
  function renderChangelog(itens) {
    const container = document.getElementById('changelog');
    if (!container) return;

    if (!itens || itens.length === 0) {
      container.innerHTML = '<li class="changelog-empty">Atualizações aparecerão aqui conforme forem registradas.</li>';
      return;
    }

    // Mais recente primeiro
    const ordenado = [...itens].sort((a, b) => (a.data < b.data ? 1 : -1));

    ordenado.forEach((item) => {
      const li = document.createElement('li');
      li.className = 'changelog-item';
      li.innerHTML = `
        <div class="changelog-meta">
          <span class="changelog-data">${escapeHtml(fmtData(item.data))}</span>
          ${item.tipo ? `<span class="changelog-tipo tipo-${item.tipo}">${escapeHtml(item.tipo)}</span>` : ''}
        </div>
        <div class="changelog-content">
          <h3 class="changelog-titulo">${escapeHtml(item.titulo)}</h3>
          <p class="changelog-descricao">${escapeHtml(item.descricao)}</p>
        </div>
      `;
      container.appendChild(li);
    });
  }

  // ----------------------------------------------------------
  // Renderização: relatórios
  // ----------------------------------------------------------
  function renderRelatorios(itens) {
    const container = document.getElementById('relatorios');
    if (!container) return;

    if (!itens || itens.length === 0) {
      container.innerHTML = `
        <div class="relatorios-empty">
          O primeiro relatório quinzenal será publicado ao final do Bloco 1.
        </div>
      `;
      return;
    }

    const ordenado = [...itens].sort((a, b) => (a.data < b.data ? 1 : -1));

    ordenado.forEach((rel) => {
      const a = document.createElement('a');
      a.className = 'relatorio';
      a.href = rel.url || '#';
      a.target = '_blank';
      a.rel = 'noopener';
      a.innerHTML = `
        <span class="relatorio-data">${escapeHtml(fmtData(rel.data))}</span>
        <h3 class="relatorio-titulo">${escapeHtml(rel.titulo)}</h3>
        <span class="relatorio-meta">Abrir documento</span>
      `;
      container.appendChild(a);
    });
  }

  // ----------------------------------------------------------
  // Anima as barras de progresso
  // ----------------------------------------------------------
  function animarProgressos(dados) {
    // Barra geral
    const geral = document.querySelector('[data-progress-bar="geral"]');
    if (geral) {
      requestAnimationFrame(() => {
        geral.style.width = `${dados.progresso_geral_pct || 0}%`;
      });
    }
    // Barras por bloco
    dados.blocos.forEach((bloco) => {
      const el = document.querySelector(`[data-progress-bloco="${bloco.numero}"]`);
      if (el) {
        requestAnimationFrame(() => {
          el.style.width = `${bloco.progresso_pct || 0}%`;
        });
      }
    });
  }

  // ----------------------------------------------------------
  // Sanitização básica para evitar HTML no conteúdo
  // ----------------------------------------------------------
  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // ----------------------------------------------------------
  // Bootstrap
  // ----------------------------------------------------------
  async function init() {
    try {
      const resp = await fetch('status.json', { cache: 'no-cache' });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const dados = await resp.json();

      // Campos formatados derivados
      const blocoAtual = dados.blocos.find((b) => b.numero === dados.bloco_atual);
      dados.bloco_atual_titulo = blocoAtual ? blocoAtual.titulo : '—';
      dados.ultima_atualizacao_fmt = fmtData(dados.ultima_atualizacao);
      dados.ultima_atualizacao_fmt_long = fmtDataLongo(dados.ultima_atualizacao);
      if (dados.projeto) {
        dados.projeto.inicio_fmt = fmtData(dados.projeto.inicio);
        dados.projeto.previsao_fmt = fmtMesAno(dados.projeto.previsao_lancamento);
      }

      bindSimples(dados);
      renderTimeline(dados.blocos);
      renderBlocos(dados.blocos);
      renderChangelog(dados.changelog);
      renderRelatorios(dados.relatorios);

      // Pequeno delay pra animação
      setTimeout(() => {
        document.body.classList.add('loaded');
        animarProgressos(dados);
      }, 50);
    } catch (err) {
      console.error('[Arminda Status] Falha ao carregar dados:', err);
      document.body.innerHTML = `
        <div style="padding: 4rem 1.5rem; text-align: center; font-family: 'IBM Plex Sans', sans-serif; color: #5b6678;">
          <h1 style="font-family: 'Fraunces', serif; color: #0a2540; margin-bottom: 1rem;">Painel temporariamente indisponível</h1>
          <p>Não foi possível carregar as informações neste momento. Tente novamente em alguns minutos.</p>
        </div>
      `;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
