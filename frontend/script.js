// ── Garde d'authentification — redirige vers login.html si pas de token ─────
const AUTH_TOKEN = sessionStorage.getItem("udx_token");
if (!AUTH_TOKEN) {
  window.location.href = "login.html";
}

function logout() {
  sessionStorage.removeItem("udx_token");
  window.location.href = "login.html";
}

const API_BASE = "https://urban-project-efrei.onrender.com";

// ── DOM refs ──────────────────────────────────────────────────────────────────
const arrSelect   = document.getElementById("arr-select");
const yearSlider  = document.getElementById("year-slider");
const yearDisplay = document.getElementById("year-display");
const yearPrev    = document.getElementById("year-prev");
const yearNext    = document.getElementById("year-next");
const kpiPrix     = document.getElementById("kpi-prix");
const kpiVentes   = document.getElementById("kpi-ventes");
const kpiLog      = document.getElementById("kpi-log");

// ── État global ───────────────────────────────────────────────────────────────
let map, markersLayer, polygonsLayer, labelsLayer, highlighted, geojsonData;
let arrMeta = [], prixData = [], logData = [], delinquanceData = [];
let densiteData = [], espacesVertsData = [], qualiteAirData = [], typologieData = [];
let years = [], currentArr = null, currentYear = null;
let choroplethMode = "prix";
let currentMode = "explore";
let timelineInterval = null;
let chartEvolution = null;
let chartTimeline = null;

// ── Palette pastel par arrondissement ─────────────────────────────────────────
const PASTEL_HUES = ["#AFD8E6", "#F3C6CE", "#F6E3A6", "#BFE0C8", "#D2C8EA", "#F3CDA8"];
const ARR_COLORS = {};
for (let i = 1; i <= 20; i++) {
  ARR_COLORS[i] = PASTEL_HUES[(i - 1) % PASTEL_HUES.length];
}

// ── Palette choroplèthe prix ──────────────────────────────────────────────────
const PRICE_BREAKS = [
  { max: 8000,  color: "#1e3a5f" },
  { max: 9000,  color: "#1d4ed8" },
  { max: 10000, color: "#0891b2" },
  { max: 11000, color: "#059669" },
  { max: 12000, color: "#d97706" },
  { max: 13000, color: "#ea580c" },
  { max: 14000, color: "#dc2626" },
  { max: Infinity, color: "#7f1d1d" }
];

function getPriceColor(price) {
  if (!price) return "#9aa3ad";
  for (const b of PRICE_BREAKS) {
    if (price <= b.max) return b.color;
  }
  return "#7f1d1d";
}

// ── Utils ─────────────────────────────────────────────────────────────────────
async function fetchJSON(url) {
  const res = await fetch(url, {
    headers: { "Authorization": `Bearer ${AUTH_TOKEN}` }
  });
  if (res.status === 401) {
    sessionStorage.removeItem("udx_token");
    window.location.href = "login.html";
    throw new Error("Session expiree, reconnexion necessaire");
  }
  if (!res.ok) throw new Error(`Erreur ${res.status} sur ${url}`);
  return res.json();
}

function getArrLabel(code) {
  const m = arrMeta.find(a => a.code === code);
  return m ? m.label : `${code}e Arrondissement`;
}

function fmt(n, suffix = "") {
  if (n == null || isNaN(n)) return "—";
  return Number(n).toLocaleString("fr-FR") + suffix;
}

// ── Streaming temps réel — qualité de l'air (C2.2) ────────────────────────────
function startLiveAirQuality() {
  const refresh = async () => {
    try {
      const data = await fetchJSON(`${API_BASE}/qualite_air/live`);
      const el = document.getElementById("live-air-status");
      if (!el) return;
      if (!data.stations || data.stations.length === 0) {
        el.innerHTML = "";
        return;
      }
      const station = data.stations.find(s => s.station === "paris") || data.stations[0];
      const maj = new Date(station.derniere_maj).toLocaleTimeString("fr-FR");
      el.innerHTML = `🟢 NO2 live (${station.station}) : <strong>${station.no2} µg/m³</strong> — maj ${maj}`;
    } catch (e) {
      console.warn("Live qualite air indisponible:", e.message);
    }
  };
  refresh();
  setInterval(refresh, 30000);
}

// ── Mode switching ────────────────────────────────────────────────────────────
function setMode(mode) {
  currentMode = mode;
  document.getElementById("panel-explore").style.display  = mode === "explore"  ? "" : "none";
  document.getElementById("panel-compare").style.display  = mode === "compare"  ? "" : "none";
  document.getElementById("panel-timeline").style.display = mode === "timeline" ? "" : "none";
  document.getElementById("btn-explore").classList.toggle("active", mode === "explore");
  document.getElementById("btn-compare").classList.toggle("active", mode === "compare");
  document.getElementById("btn-timeline").classList.toggle("active", mode === "timeline");
  if (mode === "timeline") initTimelineChart();
}

// ── Choroplèthe ───────────────────────────────────────────────────────────────
function setChoropleth(mode) {
  choroplethMode = mode;
  document.getElementById("choro-prix").classList.toggle("active", mode === "prix");
  document.getElementById("choro-arr").classList.toggle("active", mode === "arr");
  drawPolygons();
  const legend = document.getElementById("legend");
  legend.style.display = mode === "prix" ? "block" : "none";
  if (mode === "prix") buildLegend();
}

function buildLegend() {
  const items = document.getElementById("legend-items");
  items.innerHTML = "";
  PRICE_BREAKS.forEach((b, i) => {
    const prev = i > 0 ? PRICE_BREAKS[i-1].max : 0;
    const label = b.max === Infinity
      ? `> ${fmt(prev)} €`
      : `${fmt(prev)} – ${fmt(b.max)} €`;
    items.innerHTML += `<div class="legend-item">
      <span class="legend-color" style="background:${b.color}"></span>
      <span>${label}</span>
    </div>`;
  });
}

// ── Map init ──────────────────────────────────────────────────────────────────
function initMap() {
  map = L.map("map", { minZoom: 10, maxZoom: 18, zoomControl: true }).setView([48.8566, 2.3522], 13);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: "© CartoDB",
    minZoom: 10, maxZoom: 18
  }).addTo(map);
  map.setMaxBounds(L.latLngBounds([48.78, 2.18], [48.93, 2.48]));
  markersLayer = L.layerGroup().addTo(map);
}

async function loadGeoJSON() {
  const res = await fetch("arrondissements.geojson");
  geojsonData = await res.json();
}

// ── Polygones & choroplèthe ───────────────────────────────────────────────────
function drawPolygons() {
  if (!geojsonData) return;
  if (polygonsLayer) map.removeLayer(polygonsLayer);
  if (labelsLayer) map.removeLayer(labelsLayer);
  labelsLayer = L.layerGroup().addTo(map);

  polygonsLayer = L.geoJSON(geojsonData, {
    renderer: L.svg(),
    style: (feature) => {
      const code = parseInt(feature.properties.c_ar || feature.properties.code);
      let fillColor;
      if (choroplethMode === "prix") {
        const p = prixData.find(d => d.arrondissement === code && d.annee === currentYear);
        fillColor = getPriceColor(p ? p.prix_m2_median : null);
      } else {
        fillColor = ARR_COLORS[code] || "#cdd3d9";
      }
      return { fillColor, fillOpacity: 0.85, color: "#ffffff", weight: 1.5 };
    },
    onEachFeature: (feature, layer) => {
      const arrCode = parseInt(feature.properties.c_ar || feature.properties.code);

      try {
        const center = layer.getBounds().getCenter();
        const badge = L.marker(center, {
          icon: L.divIcon({
            className: "arr-badge",
            html: `<span>${arrCode}</span>`,
            iconSize: [34, 34],
            iconAnchor: [17, 17]
          }),
          interactive: false,
          keyboard: false
        });
        labelsLayer.addLayer(badge);
      } catch (e) { /* géométrie invalide, ignorer */ }

      layer.on("mouseover", () => {
        if (layer !== highlighted) {
          layer.setStyle({ fillOpacity: 1, weight: 2.5, color: "#2F6F8F" });
        }
        openPopup(arrCode, layer);
      });
      layer.on("mouseout", () => {
        if (layer !== highlighted) polygonsLayer.resetStyle(layer);
        map.closePopup();
      });
      layer.on("click", () => {
        currentArr = arrCode;
        arrSelect.value = String(arrCode);
        highlightPolygon(layer, arrCode);
        updateKPIs();
        updateChart();
        openPopup(arrCode, layer);
      });
    }
  }).addTo(map);
}

function highlightPolygon(layer, arrCode) {
  if (highlighted) polygonsLayer.resetStyle(highlighted);
  layer.setStyle({ fillOpacity: 1, weight: 3, color: "#2F6F8F" });
  highlighted = layer;
}

// ── Popup ─────────────────────────────────────────────────────────────────────
function openPopup(arrCode, layer) {
  const center = layer.getBounds().getCenter();
  const prix  = prixData.find(d => d.arrondissement === arrCode && d.annee === currentYear);
  const loge  = logData.find(d => d.arrondissement === arrCode && d.annee === currentYear) ||
                logData.filter(d => d.arrondissement === arrCode).sort((a,b) => b.annee - a.annee)[0];
  const delin = delinquanceData.find(d => d.arrondissement === arrCode && d.annee === currentYear);
  const dens  = densiteData.find(d => d.arrondissement === arrCode && d.annee === currentYear);
  const ev    = espacesVertsData.find(d => d.arrondissement === arrCode);
  const air   = qualiteAirData.find(d => d.arrondissement === arrCode);
  const typo  = typologieData.find(d => d.arrondissement === arrCode && d.annee === currentYear);

  const prixPrev = prixData.find(d => d.arrondissement === arrCode && d.annee === currentYear - 1);
  let varTxt = "";
  if (prix && prixPrev) {
    const v = ((prix.prix_m2_median - prixPrev.prix_m2_median) / prixPrev.prix_m2_median * 100).toFixed(1);
    varTxt = `<span style="color:${v >= 0 ? '#1f9d63' : '#c0473f'}">${v >= 0 ? "▲" : "▼"} ${Math.abs(v)}%</span> vs ${currentYear - 1}`;
  }

  const html = `
    <div class="popup-container">
      <div class="popup-title">${getArrLabel(arrCode)}</div>
      <div class="popup-section">
        <div>💶 <strong>${fmt(prix?.prix_m2_median, " €/m²")}</strong> ${varTxt}</div>
        <div>📊 Ventes : ${fmt(prix?.nb_ventes)}</div>
        <div>🏘️ Logements sociaux : ${loge?.part_logements_sociaux_pct != null ? loge.part_logements_sociaux_pct.toFixed(1) + "%" : "—"}</div>
      </div>
      <div class="popup-section">
        <div class="popup-subtitle">📌 Indicateurs</div>
        <div>👥 Densité : ${fmt(dens?.densite_hab_km2 ? Math.round(dens.densite_hab_km2) : null, " hab/km²")}</div>
        <div>🚓 Délinquance : ${delin?.score_delinquance != null ? delin.score_delinquance.toFixed(1) + "/10" : "—"}</div>
        <div>🌳 Espaces verts : ${ev?.m2_par_habitant != null ? ev.m2_par_habitant.toFixed(1) + " m²/hab" : "—"}</div>
        <div>🌫️ NO2 : ${air?.no2_moyen != null ? air.no2_moyen.toFixed(1) + " µg/m³" : "—"}</div>
      </div>
      ${typo ? `
      <div class="popup-section">
        <div class="popup-subtitle">🏷️ Typologie</div>
        <div>T1: ${typo.part_T1?.toFixed(1)}% &nbsp;|&nbsp; T2: ${typo.part_T2?.toFixed(1)}%</div>
        <div>T3: ${typo.part_T3?.toFixed(1)}% &nbsp;|&nbsp; T4+: ${typo.part_T4?.toFixed(1)}%</div>
      </div>` : ""}
      <div class="popup-footer">Année ${currentYear}</div>
    </div>`;

  L.popup({ closeButton: false, autoPan: false, className: "custom-popup" })
    .setLatLng(center).setContent(html).openOn(map);
}

// ── KPIs ──────────────────────────────────────────────────────────────────────
function updateKPIs() {
  if (!currentArr || !currentYear) return;

  const prix  = prixData.find(d => d.arrondissement === currentArr && d.annee === currentYear);
  const prixPrev = prixData.find(d => d.arrondissement === currentArr && d.annee === currentYear - 1);

  const loge  = logData.find(d => d.arrondissement === currentArr && d.annee === currentYear) ||
                logData.filter(d => d.arrondissement === currentArr).sort((a,b) => b.annee - a.annee)[0];

  const delin = delinquanceData.find(d => d.arrondissement === currentArr && d.annee === currentYear);
  const dens  = densiteData.find(d => d.arrondissement === currentArr && d.annee === currentYear);
  const ev    = espacesVertsData.find(d => d.arrondissement === currentArr);
  const air   = qualiteAirData.find(d => d.arrondissement === currentArr);
  const typo  = typologieData.find(d => d.arrondissement === currentArr && d.annee === currentYear);

  const variation = prix && prixPrev
    ? ((prix.prix_m2_median - prixPrev.prix_m2_median) / prixPrev.prix_m2_median * 100)
    : null;

  kpiPrix.innerHTML = `
    ${fmt(prix ? Math.round(prix.prix_m2_median) : null, " €/m²")}
    ${
      variation != null
        ? `<span class="kpi-delta ${variation >= 0 ? "up" : "down"}">
            ${variation >= 0 ? "▲" : "▼"} ${Math.abs(variation).toFixed(1)}%
          </span>`
        : ""
    }
  `;

  kpiVentes.textContent = "Ventes : " + fmt(prix?.nb_ventes);

  kpiLog.innerHTML = `
    <div class="kpi-row">🏘️ <span class="kpi-label">Logements sociaux</span><span>${loge?.part_logements_sociaux_pct != null ? loge.part_logements_sociaux_pct.toFixed(1) + "%" : "—"}</span></div>
    <div class="kpi-row">👥 <span class="kpi-label">Densité</span><span>${dens?.densite_hab_km2 ? Math.round(dens.densite_hab_km2).toLocaleString("fr-FR") + " hab/km²" : "—"}</span></div>
    <div class="kpi-row">🚓 <span class="kpi-label">Délinquance</span><span>${delin?.score_delinquance != null ? delin.score_delinquance.toFixed(1) + "/10" : "—"}</span></div>
    <div class="kpi-row">🌳 <span class="kpi-label">Espaces verts</span><span>${ev?.m2_par_habitant != null ? ev.m2_par_habitant.toFixed(1) + " m²/hab" : "—"}</span></div>
    <div class="kpi-row">🌫️ <span class="kpi-label">NO2</span><span>${air?.no2_moyen != null ? air.no2_moyen.toFixed(1) + " µg/m³" : "—"}</span></div>
  `;

  const miniSocial = document.getElementById("mini-social");
  const miniDensite = document.getElementById("mini-densite");
  const miniVerts = document.getElementById("mini-verts");
  const miniAir = document.getElementById("mini-air");
  const miniDelinquance = document.getElementById("mini-delinquance");
  const miniTypoSummary = document.getElementById("mini-typo-summary");

  if (miniSocial) miniSocial.textContent = loge?.part_logements_sociaux_pct != null ? `${loge.part_logements_sociaux_pct.toFixed(1)}%` : "—";
  if (miniDensite) miniDensite.textContent = dens?.densite_hab_km2 ? `${Math.round(dens.densite_hab_km2).toLocaleString("fr-FR")}` : "—";
  if (miniVerts) miniVerts.textContent = ev?.m2_par_habitant != null ? `${ev.m2_par_habitant.toFixed(1)} m²/hab` : "—";
  if (miniAir) miniAir.textContent = air?.no2_moyen != null ? `${air.no2_moyen.toFixed(1)} µg/m³` : "—";
  if (miniDelinquance) miniDelinquance.textContent = delin?.score_delinquance != null ? `${delin.score_delinquance.toFixed(1)}/10` : "—";

  const kpiTypo = document.getElementById("kpi-typo");

  if (kpiTypo) {
    kpiTypo.innerHTML = typo ? `
      <div class="kpi-row"><span class="kpi-label">T1</span><span>${typo.part_T1?.toFixed(1)}%</span></div>
      <div class="kpi-row"><span class="kpi-label">T2</span><span>${typo.part_T2?.toFixed(1)}%</span></div>
      <div class="kpi-row"><span class="kpi-label">T3</span><span>${typo.part_T3?.toFixed(1)}%</span></div>
      <div class="kpi-row"><span class="kpi-label">T4+</span><span>${typo.part_T4?.toFixed(1)}%</span></div>
    ` : "—";
  }

  if (miniTypoSummary && typo) {
    const parts = [
      { label: "T1", value: typo.part_T1 },
      { label: "T2", value: typo.part_T2 },
      { label: "T3", value: typo.part_T3 },
      { label: "T4+", value: typo.part_T4 }
    ];

    const dominant = parts.sort((a, b) => b.value - a.value)[0];
    miniTypoSummary.textContent = `${dominant.label} dominant`;
  }

  const insightText = document.getElementById("insight-text");

  if (insightText) {
    const priceLabel = prix?.prix_m2_median
      ? `${Math.round(prix.prix_m2_median).toLocaleString("fr-FR")} €/m²`
      : "donnée indisponible";

    const airLabel = air?.no2_moyen != null
      ? air.no2_moyen < 25 ? "bonne qualité de l'air" : air.no2_moyen < 40 ? "qualité de l'air modérée" : "qualité de l'air dégradée"
      : "qualité de l'air non disponible";

    const greenLabel = ev?.m2_par_habitant != null
      ? ev.m2_par_habitant > 10 ? "fort accès aux espaces verts" : ev.m2_par_habitant > 5 ? "accès correct aux espaces verts" : "faible accès aux espaces verts"
      : "espaces verts non disponibles";

    const trendLabel = variation != null
      ? variation >= 0
        ? `une hausse de <strong>+${variation.toFixed(1)}%</strong> par rapport à ${currentYear - 1}`
        : `une baisse de <strong>${variation.toFixed(1)}%</strong> par rapport à ${currentYear - 1}`
      : "une évolution annuelle non disponible";

    insightText.innerHTML = `
      <p><strong>${getArrLabel(currentArr)}</strong> affiche un prix médian de <strong>${priceLabel}</strong>.</p>
      <p>📈 Le marché montre ${trendLabel}.</p>
      <p>🌳 Le territoire présente un <strong>${greenLabel}</strong>.</p>
      <p>🌫️ L'indicateur NO2 signale une <strong>${airLabel}</strong>.</p>
    `;
  }

  const rankingContent = document.getElementById("ranking-content");

  if (rankingContent) {
    const ranking = prixData
      .filter(d => d.annee === currentYear && d.prix_m2_median)
      .sort((a, b) => b.prix_m2_median - a.prix_m2_median);

    const rank = ranking.findIndex(d => d.arrondissement === currentArr) + 1;

    rankingContent.innerHTML = `
      <div class="rank-big">#${rank}</div>
      <div>
        <strong>${getArrLabel(currentArr)}</strong><br>
        est le <strong>${rank}e arrondissement</strong>
        le plus cher de Paris en ${currentYear}.
      </div>
    `;
  }
}
// ── Graphique évolution ───────────────────────────────────────────────────────
function updateChart() {
  if (!currentArr) return;
  const data = prixData
    .filter(d => d.arrondissement === currentArr)
    .sort((a, b) => a.annee - b.annee);

  const labels = data.map(d => d.annee);
  const values = data.map(d => Math.round(d.prix_m2_median));

  const ctx = document.getElementById("chart-evolution").getContext("2d");
  if (chartEvolution) chartEvolution.destroy();
  chartEvolution = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        data: values,
        borderColor: "#2F6F8F",
        backgroundColor: "rgba(47,111,143,0.08)",
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: "#2F6F8F",
        tension: 0.3,
        fill: true
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#8B95A1", font: { size: 9 } }, grid: { color: "rgba(27,34,48,0.05)" } },
        y: { ticks: { color: "#8B95A1", font: { size: 9 }, callback: v => v.toLocaleString("fr-FR") + " €" }, grid: { color: "rgba(27,34,48,0.05)" } }
      }
    }
  });

  const prixActuel = prixData.find(d => d.arrondissement === currentArr && d.annee === currentYear);
  const prixPrecedent = prixData.find(d => d.arrondissement === currentArr && d.annee === currentYear - 1);
  const evActuel = espacesVertsData.find(d => d.arrondissement === currentArr);
  const variationActuelle = prixActuel && prixPrecedent
    ? ((prixActuel.prix_m2_median - prixPrecedent.prix_m2_median) / prixPrecedent.prix_m2_median * 100)
    : null;

  const mainInsight = document.getElementById("main-insight-content");

  if (mainInsight) {
    let insight = "";

    if (prixActuel?.prix_m2_median > 15000) {
      insight =
        `🔥 Cet arrondissement appartient au segment <strong>premium</strong> du marché parisien.`;
    }

    else if (prixActuel?.prix_m2_median > 12000) {
      insight =
        `📈 Cet arrondissement présente une <strong>forte valorisation immobilière</strong>.`;
    }

    else {
      insight =
        `🏠 Cet arrondissement reste relativement <strong>accessible</strong> comparé aux secteurs les plus chers de Paris.`;
    }

    if (variationActuelle != null && variationActuelle > 5) {
      insight += `<br><br>🚀 Les prix progressent rapidement avec une hausse de <strong>+${variationActuelle.toFixed(1)}%</strong>.`;
    }

    if (evActuel?.m2_par_habitant > 10) {
      insight += `<br><br>🌳 Il bénéficie également d'un excellent accès aux espaces verts.`;
    }

    mainInsight.innerHTML = insight;
  }
}

// ── Mode Comparaison ──────────────────────────────────────────────────────────
async function runComparison() {
  const arr1 = parseInt(document.getElementById("arr-compare-1").value);
  const arr2 = parseInt(document.getElementById("arr-compare-2").value);
  const year = parseInt(document.getElementById("year-compare").value);
  const result = document.getElementById("compare-result");

  result.innerHTML = `<div class="loading">Chargement...</div>`;

  try {
    const data = await fetchJSON(`${API_BASE}/comparaison?arr1=${arr1}&arr2=${arr2}&annee=${year}`);
    const a = data.arrondissement_1;
    const b = data.arrondissement_2;

    const row = (label, va, vb, suffix = "") => {
      const na = parseFloat(va), nb = parseFloat(vb);
      const better = !isNaN(na) && !isNaN(nb) ? (na < nb ? "a" : na > nb ? "b" : "") : "";
      return `<tr>
        <td class="${better === 'a' ? 'win' : ''}">${!isNaN(na) ? na.toLocaleString("fr-FR") + suffix : "—"}</td>
        <td class="compare-label">${label}</td>
        <td class="${better === 'b' ? 'win' : ''}">${!isNaN(nb) ? nb.toLocaleString("fr-FR") + suffix : "—"}</td>
      </tr>`;
    };

    result.innerHTML = `
      <div class="compare-result-box">
        <div class="compare-header">
          <span class="compare-arr-label arr-a">${getArrLabel(arr1)}</span>
          <span class="compare-vs">VS</span>
          <span class="compare-arr-label arr-b">${getArrLabel(arr2)}</span>
        </div>
        <table class="compare-table">
          ${row("Prix/m²", a.prix?.prix_m2_median ? Math.round(a.prix.prix_m2_median) : null, b.prix?.prix_m2_median ? Math.round(b.prix.prix_m2_median) : null, " €")}
          ${row("Ventes", a.prix?.nb_ventes, b.prix?.nb_ventes)}
          ${row("Logements sociaux %", a.logements_sociaux?.part_logements_sociaux_pct, b.logements_sociaux?.part_logements_sociaux_pct, "%")}
          ${row("Densité hab/km²", a.densite?.densite_hab_km2 ? Math.round(a.densite.densite_hab_km2) : null, b.densite?.densite_hab_km2 ? Math.round(b.densite.densite_hab_km2) : null)}
          ${row("Délinquance /10", a.delinquance?.score_delinquance, b.delinquance?.score_delinquance)}
          ${row("Espaces verts m²/hab", a.espaces_verts?.m2_par_habitant, b.espaces_verts?.m2_par_habitant)}
          ${row("NO2 µg/m³", a.qualite_air?.no2_moyen, b.qualite_air?.no2_moyen)}
        </table>
        <canvas id="chart-compare" height="130"></canvas>
      </div>`;

    setTimeout(() => {
      const tlA = (a.timeline || []).sort((x,y) => x.annee - y.annee);
      const tlB = (b.timeline || []).sort((x,y) => x.annee - y.annee);
      const labelsC = tlA.map(d => d.annee);
      const ctx2 = document.getElementById("chart-compare")?.getContext("2d");
      if (ctx2) {
        new Chart(ctx2, {
          type: "line",
          data: {
            labels: labelsC,
            datasets: [
              { label: getArrLabel(arr1), data: tlA.map(d => Math.round(d.prix_m2_median)), borderColor: "#2F6F8F", backgroundColor: "rgba(47,111,143,0.05)", borderWidth: 2, tension: 0.3, pointRadius: 2 },
              { label: getArrLabel(arr2), data: tlB.map(d => Math.round(d.prix_m2_median)), borderColor: "#D17A3E", backgroundColor: "rgba(209,122,62,0.05)", borderWidth: 2, tension: 0.3, pointRadius: 2 }
            ]
          },
          options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#5A6473", font: { size: 9 } } } },
            scales: {
              x: { ticks: { color: "#8B95A1", font: { size: 8 } }, grid: { color: "rgba(27,34,48,0.05)" } },
              y: { ticks: { color: "#8B95A1", font: { size: 8 }, callback: v => v.toLocaleString("fr-FR") + "€" }, grid: { color: "rgba(27,34,48,0.05)" } }
            }
          }
        });
      }
    }, 100);

  } catch(e) {
    result.innerHTML = `<div class="error">Erreur : ${e.message}</div>`;
  }
}

// ── Mode Timeline animée ──────────────────────────────────────────────────────
function initTimelineChart() {
  const ctx = document.getElementById("chart-timeline")?.getContext("2d");
  if (!ctx) return;
  if (chartTimeline) chartTimeline.destroy();
  chartTimeline = new Chart(ctx, {
    type: "bar",
    data: { labels: [], datasets: [{ data: [], backgroundColor: "#2F6F8F", borderRadius: 3 }] },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#8B95A1", font: { size: 8 } }, grid: { display: false } },
        y: { ticks: { color: "#8B95A1", font: { size: 8 }, callback: v => v.toLocaleString("fr-FR") + "€" }, grid: { color: "rgba(27,34,48,0.05)" } }
      }
    }
  });
}

function playTimeline() {
  stopTimeline();
  const arr = parseInt(document.getElementById("arr-timeline").value);
  const data = prixData.filter(d => d.arrondissement === arr).sort((a,b) => a.annee - b.annee);
  if (!data.length) return;

  document.getElementById("btn-play").textContent = "⏸ En cours...";
  document.getElementById("btn-play").disabled = true;

  if (chartTimeline) {
    chartTimeline.data.labels = data.map(d => d.annee);
    chartTimeline.data.datasets[0].data = data.map(() => 0);
    chartTimeline.update();
  }

  let i = 0;
  timelineInterval = setInterval(() => {
    if (i >= data.length) { stopTimeline(); return; }
    const d = data[i];
    document.getElementById("timeline-year").textContent = d.annee;
    document.getElementById("timeline-prix").textContent = `Prix : ${Math.round(d.prix_m2_median).toLocaleString("fr-FR")} €/m²`;

    currentYear = d.annee;
    yearDisplay.textContent = d.annee;
    drawPolygons();

    if (chartTimeline) {
      chartTimeline.data.datasets[0].data[i] = Math.round(d.prix_m2_median);
      chartTimeline.data.datasets[0].backgroundColor = data.map((_, idx) => idx === i ? "#D17A3E" : "#2F6F8F");
      chartTimeline.update();
    }

    i++;
  }, 800);
}

function stopTimeline() {
  if (timelineInterval) { clearInterval(timelineInterval); timelineInterval = null; }
  const btn = document.getElementById("btn-play");
  if (btn) { btn.textContent = "▶ Play"; btn.disabled = false; }
}

// ── Contrôles ─────────────────────────────────────────────────────────────────
function initControls() {
  arrSelect.addEventListener("change", () => {
    currentArr = parseInt(arrSelect.value, 10);
    updateKPIs();
    updateChart();
  });

  yearSlider.addEventListener("input", () => {
    currentYear = parseInt(yearSlider.value, 10);
    yearDisplay.textContent = currentYear;
    drawPolygons();
    updateKPIs();
  });

  yearPrev.addEventListener("click", () => {
    const idx = years.indexOf(currentYear);
    if (idx > 0) { currentYear = years[idx - 1]; yearDisplay.textContent = currentYear; yearSlider.value = currentYear; drawPolygons(); updateKPIs(); }
  });

  yearNext.addEventListener("click", () => {
    const idx = years.indexOf(currentYear);
    if (idx < years.length - 1) { currentYear = years[idx + 1]; yearDisplay.textContent = currentYear; yearSlider.value = currentYear; drawPolygons(); updateKPIs(); }
  });
}

function updateYearUI() {
  yearDisplay.textContent = currentYear;
  yearSlider.value = currentYear;
  yearPrev.disabled = years.indexOf(currentYear) <= 0;
  yearNext.disabled = years.indexOf(currentYear) >= years.length - 1;
}

// ── Boot ──────────────────────────────────────────────────────────────────────
async function main() {
  initMap();
  await loadGeoJSON();

  const [arrRaw, prixRaw, logRaw, delinRaw, densRaw, evRaw, airRaw, typoRaw] = await Promise.all([
    fetchJSON(`${API_BASE}/arrondissements`),
    fetchJSON(`${API_BASE}/prix_m2`),
    fetchJSON(`${API_BASE}/logements_sociaux`),
    fetchJSON(`${API_BASE}/delinquance`),
    fetchJSON(`${API_BASE}/densite`),
    fetchJSON(`${API_BASE}/espaces_verts`),
    fetchJSON(`${API_BASE}/qualite_air`),
    fetchJSON(`${API_BASE}/typologie`)
  ]);

  arrMeta = arrRaw.map(d => {
    const code = parseInt(d.code_arrondissement, 10);
    if (!Number.isInteger(code) || code < 1 || code > 20) return null;
    const suffix = code === 1 ? "er" : "ème";
    return { code, label: `${code}${suffix} — ${d.nom_officiel || d.nom || ""}` };
  }).filter(Boolean).sort((a,b) => a.code - b.code);

  prixData        = prixRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), annee: parseInt(d.annee), prix_m2_median: Number(d.prix_m2_median), nb_ventes: Number(d.nb_ventes) })).filter(d => !isNaN(d.arrondissement));
  logData         = logRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), annee: parseInt(d.annee), nb_programmes: Number(d.nb_programmes), part_logements_sociaux_pct: Number(d.part_logements_sociaux_pct) })).filter(d => !isNaN(d.arrondissement));
  delinquanceData = delinRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), annee: parseInt(d.annee), score_delinquance: Number(d.score_delinquance) })).filter(d => !isNaN(d.arrondissement));
  densiteData     = densRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), annee: parseInt(d.annee), densite_hab_km2: Number(d.densite_hab_km2) })).filter(d => !isNaN(d.arrondissement));
  espacesVertsData = evRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), m2_par_habitant: Number(d.m2_par_habitant), superficie_totale_m2: Number(d.superficie_totale_m2) })).filter(d => !isNaN(d.arrondissement));
  qualiteAirData  = airRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), no2_moyen: Number(d.no2_moyen), o3_moyen: Number(d.o3_moyen), pm10_moyen: Number(d.pm10_moyen) })).filter(d => !isNaN(d.arrondissement));
  typologieData   = typoRaw.map(d => ({ arrondissement: parseInt(d.arrondissement), annee: parseInt(d.annee), part_T1: Number(d.part_T1), part_T2: Number(d.part_T2), part_T3: Number(d.part_T3), part_T4: Number(d.part_T4) })).filter(d => !isNaN(d.arrondissement));

  years = [...new Set(prixData.map(d => d.annee))].sort((a,b) => a-b);
  currentYear = years.includes(2024) ? 2024 : years[years.length - 1];
  yearSlider.min = years[0]; yearSlider.max = years[years.length - 1];

  const selects = ["arr-select", "arr-compare-1", "arr-compare-2", "arr-timeline"];
  selects.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    arrMeta.forEach(a => {
      const opt = document.createElement("option");
      opt.value = a.code; opt.textContent = a.label;
      el.appendChild(opt);
    });
  });

  const yearCompare = document.getElementById("year-compare");
  years.slice().reverse().forEach(y => {
    const opt = document.createElement("option");
    opt.value = y; opt.textContent = y;
    if (y === currentYear) opt.selected = true;
    yearCompare.appendChild(opt);
  });

  const c2 = document.getElementById("arr-compare-2");
  if (c2) c2.value = "6";

  currentArr = arrMeta[0].code;
  arrSelect.value = String(currentArr);

  updateYearUI();
  drawPolygons();
  buildLegend();
  initControls();
  updateKPIs();
  updateChart();

  setChoropleth("prix");
  startLiveAirQuality();
}

main().catch(err => {
  console.error(err);
  alert("Erreur chargement : " + err.message);
});