/* ============================================================
   Arminda · Status Page
   Le status.json e popula a pagina.
   ============================================================ */

(function () {
  'use strict';

  const MESES = ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'];
  const MESES_LONGO = ['janeiro','fevereiro','marco','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'];

  const STATUS_LABEL = {
    concluido: 'Concluido',
    em_andamento: 'Em andamento',
    previsto: 'Previsto'
  };

  function parseDate(iso) {
    if (!iso) return null;
    const [y, m, d] = iso.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  function fmtData(iso) {
    const d = parseDate(iso);
    if (!d) return '\u2014';
    return `${String(d.getDate()).padStart(2,'0')}/${MESES[d.getMonth()]}/${d.getFullYear()}`;
  }

  function fmtDataLongo(iso) {
    const d = parseDate(iso);
    if (!d) return '\u2014';
    return `${d.getDate()} de ${MESES_LONGO[d.getMonth()]} de ${d.getFullYear()}`;
  }

  function fmtMesAno(iso) {
    const d = parseDate(iso);
    if (!d) return '\u2014';
    return `${MESES[d.getMonth()]}/${d.getFullYear()}`;
  }

  function mesesEntre(a, b) {
    return (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth());
  }

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function bindSimples(dados) {
    document.querySelectorAll('[data-bind]').forEach(function (el) {
      var path = el.getAttribute('data-bind');
      var valor = path.split('.').reduce(function (obj, key) {
        return obj == null ? undefined : obj[key];
      }, dados);
      if (valor !== undefined && valor !== null) {
        el.textContent = String(valor);
      }
    });
  }

  // ----------------------------------------------------------
  // Timeline
  // ----------------------------------------------------------
  function renderTimeline(blocos) {
    var container = document.getElementById('timeline');
    if (!container) return;

    var datasInicio = blocos.map(function (b) { return parseDate(b.data_inicio); }).filter(Boolean);
    var datasFim = blocos.map(function (b) { return parseDate(b.data_fim_real || b.data_fim_prevista); }).filter(Boolean);
    if (datasInicio.length === 0 || datasFim.length === 0) return;

    var inicioGeral = new Date(Math.min.apply(null, datasInicio.map(function (d) { return d.getTime(); })));
    var fimGeral = new Date(Math.max.apply(null, datasFim.map(function (d) { return d.getTime(); })));
    var totalMeses = Math.max(1, mesesEntre(inicioGeral, fimGeral) + 1);

    // Header
    var header = document.createElement('div');
    header.className = 'timeline-header';
    header.innerHTML =
      '<div class="timeline-header-spacer"></div>' +
      '<div class="timeline-header-spacer"></div>' +
      '<div class="timeline-header-scale">' +
        [0, 0.25, 0.5, 0.75, 1].map(function (frac) {
          var d = new Date(inicioGeral);
          d.setMonth(d.getMonth() + Math.round(totalMeses * frac));
          return '<span class="timeline-header-tick" style="left:' + (frac * 100) + '%">' +
            MESES[d.getMonth()] + '/' + String(d.getFullYear()).slice(2) + '</span>';
        }).join('') +
      '</div>' +
      '<div class="timeline-header-spacer"></div>';
    container.appendChild(header);

    blocos.forEach(function (bloco) {
      var inicio = parseDate(bloco.data_inicio);
      var fim = parseDate(bloco.data_fim_real || bloco.data_fim_prevista);
      if (!inicio || !fim) return;

      var offsetPct = (mesesEntre(inicioGeral, inicio) / totalMeses) * 100;
      var widthPct = Math.max(3, ((mesesEntre(inicio, fim) + 1) / totalMeses) * 100);

      var row = document.createElement('div');
      row.className = 'timeline-row row-' + bloco.status;
      row.innerHTML =
        '<span class="timeline-num">' + String(bloco.numero).padStart(2, '0') + '</span>' +
        '<div class="timeline-info">' +
          '<span class="timeline-info-title">' + escapeHtml(bloco.titulo) + '</span>' +
          '<span class="timeline-info-period">' + escapeHtml(bloco.periodo) + '</span>' +
        '</div>' +
        '<div class="timeline-bar-wrapper">' +
          '<div class="timeline-bar-track"></div>' +
          '<div class="timeline-bar status-' + bloco.status + '"' +
            ' style="left:' + offsetPct + '%;width:' + widthPct + '%"' +
            ' title="' + escapeHtml(bloco.titulo) + '"></div>' +
        '</div>' +
        '<span class="timeline-badge badge-' + bloco.status + '">' +
          escapeHtml(STATUS_LABEL[bloco.status] || '') +
        '</span>';
      container.appendChild(row);
    });
  }

  // ----------------------------------------------------------
  // Blocos
  // ----------------------------------------------------------
  function renderBlocos(blocos) {
    var container = document.getElementById('blocos');
    if (!container) return;

    blocos.forEach(function (bloco) {
      var card = document.createElement('article');
      card.className = 'bloco-card card-' + bloco.status;
      card.id = 'bloco-' + bloco.numero;

      var entregasHtml = (bloco.entregas || []).map(function (e) {
        return '<li class="bloco-entrega">' + escapeHtml(e) + '</li>';
      }).join('');

      card.innerHTML =
        '<div class="bloco-top">' +
          '<span class="bloco-num">' + String(bloco.numero).padStart(2, '0') + '</span>' +
          '<span class="timeline-badge badge-' + bloco.status + '">' +
            escapeHtml(STATUS_LABEL[bloco.status] || '') +
          '</span>' +
        '</div>' +
        '<h3 class="bloco-titulo">' + escapeHtml(bloco.titulo) + '</h3>' +
        '<p class="bloco-desc">' + escapeHtml(bloco.descricao) + '</p>' +
        '<div class="bloco-progress">' +
          '<div class="bloco-progress-header">' +
            '<span>Progresso</span>' +
            '<span class="bloco-progress-pct">' + bloco.progresso_pct + '%</span>' +
          '</div>' +
          '<div class="bloco-progress-bar">' +
            '<div class="bloco-progress-fill" data-progress-bloco="' + bloco.numero + '"></div>' +
          '</div>' +
        '</div>' +
        (entregasHtml ?
          '<div>' +
            '<p class="bloco-entregas-label">Entregas previstas</p>' +
            '<ul class="bloco-entregas">' + entregasHtml + '</ul>' +
          '</div>'
          : '') +
        '<span class="bloco-periodo-text">' + escapeHtml(bloco.periodo) + '</span>';

      container.appendChild(card);
    });
  }

  // ----------------------------------------------------------
  // Changelog
  // ----------------------------------------------------------
  function renderChangelog(itens) {
    var container = document.getElementById('changelog');
    if (!container) return;

    if (!itens || itens.length === 0) {
      container.innerHTML = '<li class="changelog-empty">Atualizacoes aparecerao aqui conforme forem registradas.</li>';
      return;
    }

    var ordenado = itens.slice().sort(function (a, b) { return a.data < b.data ? 1 : -1; });

    ordenado.forEach(function (item) {
      var li = document.createElement('li');
      li.className = 'changelog-item';
      li.innerHTML =
        '<div class="changelog-meta">' +
          '<span class="changelog-data">' + escapeHtml(fmtData(item.data)) + '</span>' +
          (item.tipo ? '<span class="changelog-tipo tipo-' + item.tipo + '">' + escapeHtml(item.tipo) + '</span>' : '') +
        '</div>' +
        '<div class="changelog-content">' +
          '<h3 class="changelog-titulo">' + escapeHtml(item.titulo) + '</h3>' +
          '<p class="changelog-descricao">' + escapeHtml(item.descricao) + '</p>' +
        '</div>';
      container.appendChild(li);
    });
  }

  // ----------------------------------------------------------
  // Relatorios
  // ----------------------------------------------------------
  function renderRelatorios(itens) {
    var container = document.getElementById('relatorios-list');
    if (!container) return;

    if (!itens || itens.length === 0) {
      container.innerHTML =
        '<div class="relatorios-empty">' +
          'O primeiro relatorio quinzenal sera publicado ao final do Bloco 1.' +
        '</div>';
      return;
    }

    var ordenado = itens.slice().sort(function (a, b) { return a.data < b.data ? 1 : -1; });

    ordenado.forEach(function (rel) {
      var a = document.createElement('a');
      a.className = 'relatorio-card';
      a.href = rel.url || '#';
      a.target = '_blank';
      a.rel = 'noopener';
      a.innerHTML =
        '<span class="relatorio-data">' + escapeHtml(fmtData(rel.data)) + '</span>' +
        '<h3 class="relatorio-titulo">' + escapeHtml(rel.titulo) + '</h3>' +
        '<span class="relatorio-cta">Abrir documento</span>';
      container.appendChild(a);
    });
  }

  // ----------------------------------------------------------
  // Progress bars
  // ----------------------------------------------------------
  function animarProgressos(dados) {
    var geral = document.querySelector('[data-progress-bar="geral"]');
    if (geral) {
      requestAnimationFrame(function () {
        geral.style.width = (dados.progresso_geral_pct || 0) + '%';
      });
    }
    dados.blocos.forEach(function (bloco) {
      var el = document.querySelector('[data-progress-bloco="' + bloco.numero + '"]');
      if (el) {
        requestAnimationFrame(function () {
          el.style.width = (bloco.progresso_pct || 0) + '%';
        });
      }
    });
  }

  // ----------------------------------------------------------
  // Init
  // ----------------------------------------------------------
  async function init() {
    try {
      var resp = await fetch('status.json', { cache: 'no-cache' });
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      var dados = await resp.json();

      var blocoAtual = dados.blocos.find(function (b) { return b.numero === dados.bloco_atual; });
      dados.bloco_atual_titulo = blocoAtual ? blocoAtual.titulo : '\u2014';
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

      setTimeout(function () {
        document.body.classList.add('loaded');
        animarProgressos(dados);
      }, 80);
    } catch (err) {
      console.error('[Arminda Status] Falha ao carregar dados:', err);
      document.body.innerHTML =
        '<div style="padding:6rem 1.5rem;text-align:center;font-family:Inter,sans-serif;color:#6b7280">' +
          '<h1 style="font-family:Fraunces,serif;color:#111827;margin-bottom:1rem;font-size:1.5rem">Painel temporariamente indisponivel</h1>' +
          '<p>Nao foi possivel carregar as informacoes. Tente novamente em alguns minutos.</p>' +
        '</div>';
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
