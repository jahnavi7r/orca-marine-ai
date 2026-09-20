import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const UI_STRINGS = {
  te: {
    title: "🌊 ఓర్కా మెరైన్ AI",
    subtitle: "గ్లోబల్ స్వయంప్రతిపత్తి సముద్ర విశ్లేషణ వ్యవస్థ",
    langLabel: "భాష:",
    useGPS: "📍 లైవ్ GPS",
    placeholder: "తీరప్రాంతం లేదా ప్రశ్న నమోదు చేయండి (ఉదా. విశాఖపట్నం, గోవా)...",
    btnAnalyze: "సముద్ర పరిస్థితులను విశ్లేషించండి 🎙️",
    btnLoading: "ఉపగ్రహ సమాచారాన్ని విశ్లేషిస్తోంది...",
    errorTitle: "లోపం",
    statusLabel: "స్థితి",
    safe: "సురక్షితం",
    caution: "హెచ్చరిక",
    critical: "ప్రమాదం",
    waypointsTitle: "📍 సురక్షిత ప్రయాణ మార్గ పాయింట్లు:",
    seq: "క్రమం",
    evidenceTitle: "ప్రత్యేక ఏజెంట్ల విశ్లేషణ ఆధారాలు:",
    weatherAgent: "🌪️ వాతావరణ సమాచార ఏజెంట్:",
    oceanAgent: "🌊 సముద్ర తరంగాల విశ్లేషణ ఏజెంట్:",
    geofenceAgent: "🛡️ సముద్ర సరిహద్దు మరియు రక్షిత ప్రాంత ఏజెంట్:",
    pfzAgent: "🛰️ సమృద్ధి చేపల వేట ప్రాంత ఏజెంట్:",
    safeCorridorTitle: "🛡️ సురక్షిత ప్రయాణ మార్గం",
    safeCorridorDesc: "చిన్న పడవలు మరియు మోటారు బోట్లకు ధృవీకరించబడిన సురక్షిత మార్గం.",
    hazardSectorTitle: "⚠️ తీరప్రాంత ప్రమాదకర విభాగం",
    hazardAdviceTitle: "నావిగేషన్ సూచన:",
    pfzTitle: "🐟 సమృద్ధి చేపల వేట ప్రాంతం",
    catchProbLabel: "చేపలు దొరికే సంభావ్యత:",
    chlorophyllLabel: "క్లోరోఫిల్-ఎ స్థాయి:",
    sstLabel: "సముద్ర ఉపరితల ఉష్ణోగ్రత:",
    gearLabel: "సిఫార్సు చేయబడిన వలలు మరియు సాధనాలు:",
    speciesLabel: "గుర్తించబడిన చేప జాతులు:"
  },
  ta: {
    title: "🌊 ஆர்கா கடல்சார் AI",
    subtitle: "உலகளாவிய தானியங்கி கடல்சார் புலனாய்வு அமைப்பு",
    langLabel: "மொழி:",
    useGPS: "📍 நேரடி GPS",
    placeholder: "கடற்கரை இடம் அல்லது வினவலை உள்ளிடவும் (எ.கா. கொச்சி, கோவா)...",
    btnAnalyze: "கடல் நிலையை பகுப்பாய்வு செய்க 🎙️",
    btnLoading: "செயற்கைக்கோள் தரவு பகுப்பாய்வு செய்யப்படுகிறது...",
    errorTitle: "பிழை",
    statusLabel: "நிலை",
    safe: "பாதுகாப்பானது",
    caution: "எச்சரிக்கை",
    critical: "ஆபத்தானது",
    waypointsTitle: "📍 பாதுகாப்பான வழிசெலுத்தல் புள்ளிகள்:",
    seq: "வரிசை",
    evidenceTitle: "முகவர் பகுப்பாய்வு சான்றுகள்:",
    weatherAgent: "🌪️ வானிலை புலனாய்வு முகவர்:",
    oceanAgent: "🌊 கடல் அலைகள் பகுப்பாய்வு முகவர்:",
    geofenceAgent: "🛡️ கடல் எல்லை மற்றும் பாதுகாப்பு முகவர்:",
    pfzAgent: "🛰️ மீன்பிடி மண்டல கண்டுபிடிப்பு முகவர்:",
    safeCorridorTitle: "🛡️ பாதுகாப்பான வழிசெலுத்தல் பாதை",
    safeCorridorDesc: "படகுகள் செல்ல அனுமதிக்கப்பட்ட பாதுகாப்பான பாதை.",
    hazardSectorTitle: "⚠️ கடலோர ஆபத்து மண்டலம்",
    hazardAdviceTitle: "வழிசெலுத்தல் ஆலோசனை:",
    pfzTitle: "🐟 சாத்தியமான மீன்பிடி மண்டலம்",
    catchProbLabel: "மீன் பிடிக்கும் நிகழ்தகவு:",
    chlorophyllLabel: "குளோரோபில் அளவு:",
    sstLabel: "கடல் மேற்பரப்பு வெப்பநிலை:",
    gearLabel: "பரிந்துரைக்கப்பட்ட மீன்பிடி உபகரணங்கள்:",
    speciesLabel: "கண்டறியப்பட்ட மீன் இனங்கள்:"
  },
  hi: {
    title: "🌊 ओर्का मरीन एआई",
    subtitle: "ग्लोबल स्वायत्त बहु-एजेंट समुद्री बुद्धिमत्ता प्रणाली",
    langLabel: "भाषा:",
    useGPS: "📍 लाइव जीपीएस",
    placeholder: "तटीय स्थान या समुद्री प्रश्न दर्ज करें (उदा. विशाखापट्टनम, गोवा)...",
    btnAnalyze: "समुद्री स्थितियों का विश्लेषण करें 🎙️",
    btnLoading: "उपग्रह डेटा का विश्लेषण जारी है...",
    errorTitle: "त्रुटि",
    statusLabel: "स्थिति",
    safe: "सुरक्षित",
    caution: "सावधानी",
    critical: "खतरा",
    waypointsTitle: "📍 सुरक्षित नेविगेशन वेपॉइंट्स:",
    seq: "चरण",
    evidenceTitle: "डोमेन एजेंट साक्ष्य और विश्लेषण:",
    weatherAgent: "🌪️ मौसम आसूचना एजेंट:",
    oceanAgent: "🌊 महासागरीय तरंग विश्लेषण एजेंट:",
    geofenceAgent: "🛡️ समुद्री सीमा एवं सुरक्षा एजेंट:",
    pfzAgent: "🛰️ संभावित मत्स्य पालन क्षेत्र एजेंट:",
    safeCorridorTitle: "🛡️ सुरक्षित नेविगेशन गलियारा",
    safeCorridorDesc: "छोटी नौकाओं और ट्रॉलरों के लिए सुरक्षित मार्ग।",
    hazardSectorTitle: "⚠️ तटीय खतरा क्षेत्र",
    hazardAdviceTitle: "नेविगेशन परामर्श:",
    pfzTitle: "🐟 संभावित मत्स्य पालन क्षेत्र",
    catchProbLabel: "मछली पकड़ने की संभावना:",
    chlorophyllLabel: "क्लोरोफिल-ए स्तर:",
    sstLabel: "समुद्र की सतह का तापमान:",
    gearLabel: "अनुशंसित उपकरण एवं जाल:",
    speciesLabel: "पहचानी गई मछली प्रजातियाँ:"
  },
  en: {
    title: "🌊 ORCA Marine AI",
    subtitle: "Global Autonomous Multi-Agent Marine Intelligence",
    langLabel: "Language:",
    useGPS: "📍 Live GPS",
    placeholder: "Enter coastal location or query (e.g. Visakhapatnam, Goa)...",
    btnAnalyze: "Analyze Sea Conditions 🎙️",
    btnLoading: "Synthesizing Live Satellite Telemetry...",
    errorTitle: "Error",
    statusLabel: "STATUS",
    safe: "SAFE",
    caution: "CAUTION",
    critical: "CRITICAL",
    waypointsTitle: "📍 Dynamic Waypoint Routing:",
    seq: "Seq",
    evidenceTitle: "Domain Agent Evidence:",
    weatherAgent: "🌪️ Weather Intelligence:",
    oceanAgent: "🌊 Ocean Analytics:",
    geofenceAgent: "🛡️ Geofence & Boundary:",
    pfzAgent: "🛰️ PFZ Discovery:",
    safeCorridorTitle: "🛡️ Safe Navigation Corridor",
    safeCorridorDesc: "Certified safe passage for motorized boats and trawlers.",
    hazardSectorTitle: "⚠️ Coastal Hazard Sector",
    hazardAdviceTitle: "Navigation Advice:",
    pfzTitle: "🐟 Potential Fishing Zone",
    catchProbLabel: "Fish Catch Probability:",
    chlorophyllLabel: "Chlorophyll-a:",
    sstLabel: "Sea Temp (SST):",
    gearLabel: "Recommended Gear:",
    speciesLabel: "Target Species Detected:"
  }
};

function MapRecenter({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center && center[0] && center[1]) {
      map.flyTo(center, 10, { animate: true, duration: 1.5 });
    }
  }, [center, map]);
  return null;
}

function App() {
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [advisory, setAdvisory] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [mapCenter, setMapCenter] = useState([17.6868, 83.2185]);

  const t = UI_STRINGS[language] || UI_STRINGS.en;

  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    setErrorMessage(null);
  };

  const speakAdvisory = (text, targetLang) => {
    if (!('speechSynthesis' in window) || !text) return;
    window.speechSynthesis.cancel();

    const cleanText = text
      .replace(/\(GO\)/gi, '')
      .replace(/\(CAUTION\)/gi, '')
      .replace(/\(NO-GO\)/gi, '')
      .replace(/\(SAFE\)/gi, '')
      .replace(/[\(\)\[\]:]/g, ' ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    const langCodeMap = { te: 'te-IN', ta: 'ta-IN', hi: 'hi-IN', en: 'en-IN' };
    const targetCode = langCodeMap[targetLang] || 'en-IN';
    utterance.lang = targetCode;
    utterance.rate = 0.88;

    const voices = window.speechSynthesis.getVoices();
    let selectedVoice = voices.find(v => v.lang === targetCode || v.lang.replace('_', '-').toLowerCase().startsWith(targetLang));
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.includes(targetLang) || v.name.toLowerCase().includes(targetLang));
    }
    if (!selectedVoice) {
      selectedVoice = voices.find(v => v.lang.includes('IN') || v.name.includes('India'));
    }
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    window.speechSynthesis.speak(utterance);
  };

  const handleAskOrca = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setErrorMessage(null);

    try {
      const response = await axios.post("http://127.0.0.1:8080/api/v1/advisory", {
        query: query.trim(),
        language: language
      });

      if (response.data.status === "ERROR") {
        setAdvisory(null);
        setErrorMessage(response.data.message);
        return;
      }

      const decision = response.data.decision;
      setAdvisory(decision);

      if (decision.nav_waypoints && decision.nav_waypoints.length > 0) {
        setMapCenter(decision.nav_waypoints[0].coordinates);
      }

      speakAdvisory(decision.primary_recommendation, language);
    } catch (err) {
      setAdvisory(null);
      setErrorMessage(
        language === 'te' 
          ? "సర్వర్‌తో కనెక్ట్ కాలేకపోయింది లేదా స్థానం దొరకలేదు." 
          : language === 'ta' 
          ? "சேவையகத்தை இணைக்க முடியவில்லை அல்லது இடம் கிடைக்கவில்லை." 
          : language === 'hi' 
          ? "सर्वर से संपर्क नहीं हो सका या स्थान नहीं मिला।" 
          : "Location could not be resolved or server error."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleUseGPS = () => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition((pos) => {
        const lat = pos.coords.latitude.toFixed(4);
        const lon = pos.coords.longitude.toFixed(4);
        setErrorMessage(null);
        setQuery(`Coordinates ${lat}, ${lon}`);
      }, () => {
        alert("GPS access denied or unavailable.");
      });
    }
  };

  const routeLineCoords = advisory?.nav_waypoints?.map(wp => wp.coordinates) || [];

  return (
    <div className="orca-container">
      <div className="sidebar">
        {/* Fixed Top Section: Title, Language, GPS, Search */}
        <div className="sidebar-top">
          <h2>{t.title}</h2>
          <p className="subtitle">{t.subtitle}</p>

          <div className="control-row">
            <select 
              value={language} 
              onChange={(e) => handleLanguageChange(e.target.value)}
            >
              <option value="en">English</option>
              <option value="te">తెలుగు (Telugu)</option>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="hi">हिन्दी (Hindi)</option>
            </select>

            <button className="gps-btn" onClick={handleUseGPS}>
              {t.useGPS}
            </button>
          </div>

          <textarea 
            rows="2"
            className="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAskOrca();
              }
            }}
            placeholder={t.placeholder}
          />

          <button className="send-btn" onClick={handleAskOrca} disabled={loading || !query.trim()}>
            {loading ? t.btnLoading : t.btnAnalyze}
          </button>
        </div>

        {/* Scrollable Results Section */}
        <div className="sidebar-results">
          {errorMessage && (
            <div style={{
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              lineHeight: 1.4
            }}>
              <strong style={{ color: '#ef4444' }}>⚠️ {t.errorTitle}: </strong>
              <span style={{ fontSize: '0.85rem' }}>{errorMessage}</span>
            </div>
          )}

          {advisory && (
            <>
              <div>
                <span className={`badge badge-${advisory.overall_status}`}>
                  {t.statusLabel}: {advisory.overall_status === "SAFE" ? t.safe : advisory.overall_status === "CAUTION" ? t.caution : t.critical}
                </span>

                <h3 style={{ fontSize: '0.96rem', marginTop: '8px', color: '#e2e8f0', lineHeight: 1.4 }}>
                  {advisory.primary_recommendation}
                </h3>
              </div>

              {/* Waypoint 3 Card at Top */}
              {advisory.nav_waypoints && advisory.nav_waypoints.length >= 3 && (
                <div className="agent-card" style={{ border: '1px solid #38bdf8' }}>
                  <strong style={{ color: '#38bdf8' }}>
                    {t.seq} 3: {advisory.nav_waypoints[2].name}
                  </strong>
                  <div style={{ fontSize: '0.80rem', color: '#cbd5e1' }}>
                    {advisory.nav_waypoints[2].nav_instruction}
                  </div>
                </div>
              )}

              {/* Domain Agent Evidence Header in Native Language */}
              <h3 style={{ fontSize: '0.96rem', color: '#ffffff', marginTop: '6px' }}>
                {t.evidenceTitle}
              </h3>

              {/* Four Evidence Cards in Native Language */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div className="agent-card">
                  <strong>{t.weatherAgent}</strong>
                  <div>{advisory.evidence_breakdown?.weather_agent?.evidence}</div>
                </div>
                <div className="agent-card">
                  <strong>{t.oceanAgent}</strong>
                  <div>{advisory.evidence_breakdown?.ocean_agent?.evidence}</div>
                </div>
                <div className="agent-card">
                  <strong>{t.geofenceAgent}</strong>
                  <div>{advisory.evidence_breakdown?.geofence_agent?.evidence}</div>
                </div>
                <div className="agent-card">
                  <strong>{t.pfzAgent}</strong>
                  <div>{advisory.evidence_breakdown?.pfz_agent?.evidence}</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Map View */}
      <div className="map-container">
        <MapContainer center={mapCenter} zoom={10} style={{ height: '100%', width: '100%' }}>
          <MapRecenter center={mapCenter} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Cyan Transit Route Line */}
          {routeLineCoords.length > 1 && (
            <Polyline positions={routeLineCoords} color="#38bdf8" weight={4} dashArray="6, 8" />
          )}

          {/* 3 Waypoint Pins with Dynamic Popups */}
          {advisory?.nav_waypoints?.map(wp => (
            <Marker key={wp.sequence} position={wp.coordinates}>
              <Popup>
                <div style={{ fontFamily: "'Segoe UI', sans-serif", color: "#0f172a", minWidth: "200px", lineHeight: "1.4" }}>
                  <strong style={{ color: "#0284c7", fontSize: "0.90rem" }}>{t.seq} {wp.sequence}: {wp.name}</strong>
                  <div style={{ fontSize: "0.80rem", marginTop: "4px", color: "#475569" }}>
                    <b>GPS:</b> {wp.coordinates[0].toFixed(4)}, {wp.coordinates[1].toFixed(4)}
                  </div>
                  <div style={{ fontSize: "0.82rem", marginTop: "4px", color: "#1e293b" }}>
                    {wp.nav_instruction}
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Green Safe Navigation Corridor Polygon */}
          {advisory?.geojson_overlays?.safe_zone && (
            <GeoJSON 
              key={`safe-${mapCenter.join('-')}`}
              data={advisory.geojson_overlays.safe_zone}
              style={{ color: '#10b981', fillColor: '#10b981', fillOpacity: 0.20, weight: 2 }}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: 'Segoe UI', sans-serif; color: #0f172a; min-width: 230px; line-height: 1.45;">
                    <div style="display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 6px;">
                      <span style="font-size: 1.1rem;">🛡️</span>
                      <strong style="color: #059669; font-size: 0.92rem;">${t.safeCorridorTitle}</strong>
                    </div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>${t.statusLabel}:</b> <span style="color: #059669; font-weight: bold;">${props.status || advisory.overall_status}</span></div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>Wave Height:</b> ${props.wave_height || (advisory.evidence_breakdown?.ocean_agent?.significant_wave_height_m ? advisory.evidence_breakdown.ocean_agent.significant_wave_height_m + 'm' : 'Calm')}</div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>Wind Speed:</b> ${props.wind_speed || (advisory.evidence_breakdown?.weather_agent?.wind_speed_knots ? advisory.evidence_breakdown.weather_agent.wind_speed_knots + ' kts' : 'Moderate')}</div>
                    <div style="margin-top: 6px; padding: 4px 6px; background: #ecfdf5; border-radius: 4px; font-size: 0.76rem; color: #047857;">
                      ✓ ${t.safeCorridorDesc}
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* Dynamic PFZ Polygon (Cyan) */}
          {advisory?.geojson_overlays?.pfz_zone && (
            <GeoJSON 
              key={`pfz-${mapCenter.join('-')}`}
              data={advisory.geojson_overlays.pfz_zone}
              style={{
                color: '#06b6d4',
                fillColor: '#0891b2',
                fillOpacity: 0.45,
                weight: 3,
                dashArray: '4, 4'
              }}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};
                layer.bindPopup(`
                  <div style="font-family: 'Segoe UI', sans-serif; color: #0f172a; min-width: 250px; line-height: 1.45;">
                    <div style="display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 6px;">
                      <span style="font-size: 1.1rem;">🐟</span>
                      <strong style="color: #0891b2; font-size: 0.92rem;">${t.pfzTitle}</strong>
                    </div>
                    <div style="background: #e0f2fe; padding: 6px 8px; border-radius: 6px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                      <span style="font-size: 0.80rem; font-weight: 600; color: #0369a1;">${t.catchProbLabel}</span>
                      <span style="font-size: 0.92rem; font-weight: 700; color: #0284c7;">${props.fishing_potential || '88%'}</span>
                    </div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>${t.chlorophyllLabel}</b> ${props.chlorophyll || '1.85 mg/m³'}</div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>${t.sstLabel}</b> ${props.sst || '28.5°C'}</div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>${t.gearLabel}</b> ${props.recommended_gear || 'Gillnets / Longlines'}</div>
                    
                    <div style="margin-top: 6px; padding: 6px 8px; background: #f0f9ff; border-left: 3px solid #0284c7; font-size: 0.78rem; color: #075985; border-radius: 2px;">
                      <b>${t.speciesLabel}</b><br/>
                      ${props.target_species || 'High aggregation of seasonal commercial pelagic shoals.'}
                    </div>
                  </div>
                `);
              }}
            />
          )}

          {/* Flanking Hazard & Breaker Sector Polygon (Always Red) */}
          {advisory?.geojson_overlays?.danger_zone && (
            <GeoJSON 
              key={`danger-${mapCenter.join('-')}`}
              data={advisory.geojson_overlays.danger_zone}
              style={{
                color: '#ef4444',
                fillColor: '#ef4444',
                fillOpacity: 0.35,
                weight: 2
              }}
              onEachFeature={(feature, layer) => {
                const props = feature.properties || {};

                layer.bindPopup(`
                  <div style="font-family: 'Segoe UI', sans-serif; color: #0f172a; min-width: 260px; line-height: 1.45;">
                    <div style="display: flex; align-items: center; gap: 6px; border-bottom: 1px solid #fee2e2; padding-bottom: 5px; margin-bottom: 6px;">
                      <span style="font-size: 1.1rem;">⚠️</span>
                      <strong style="color: #dc2626; font-size: 0.92rem;">${t.hazardSectorTitle}</strong>
                    </div>

                    <div style="background: #fee2e2; color: #b91c1c; padding: 5px 8px; border-radius: 4px; font-weight: 700; font-size: 0.78rem; margin-bottom: 6px; letter-spacing: 0.3px; border-left: 3px solid #dc2626;">
                      ${props.hazard_class || 'COASTAL HAZARD ZONE'}
                    </div>

                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>Swell Period:</b> ${props.swell_period || 'N/A'}</div>
                    <div style="font-size: 0.82rem; margin-bottom: 3px;"><b>Peak Gusts:</b> ${props.wind_gusts || 'N/A'}</div>
                    
                    <div style="font-size: 0.80rem; color: #334155; margin-top: 6px; margin-bottom: 4px;">
                      <b>Primary Risk:</b><br/>
                      ${props.hazard_reason || 'Nearshore shoal dynamics and wave interaction.'}
                    </div>

                    <div style="margin-top: 6px; padding: 6px 8px; background: #fff1f2; border: 1px solid #fecdd3; font-size: 0.76rem; color: #9f1239; border-radius: 4px;">
                      <b>${t.hazardAdviceTitle}</b><br/>
                      ${props.action || 'Maintain heading within designated green corridor.'}
                    </div>
                  </div>
                `);
              }}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
