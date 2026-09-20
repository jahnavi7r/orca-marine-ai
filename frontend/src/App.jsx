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
    subtitle: "ఇస్రో SIH26176 గ్లోబల్ మల్టీ-ఏజెంట్ మెరైన్ ఇంటెలిజెన్స్",
    langLabel: "ప్రాంతీయ భాష:",
    useGPS: "📍 లైవ్ GPS",
    placeholder: "తీరప్రాంతం లేదా ప్రశ్న నమోదు చేయండి...",
    btnAnalyze: "సముద్ర పరిస్థితులను విశ్లేషించండి 🎙️",
    btnLoading: "ఉపగ్రహ సమాచారాన్ని విశ్లేషిస్తోంది...",
    errorTitle: "లోపం",
    statusLabel: "స్థితి",
    safe: "సురక్షితం (SAFE)",
    caution: "హెచ్చరిక (CAUTION)",
    critical: "ప్రమాదం (CRITICAL)",
    waypointsTitle: "📍 సురక్షిత ప్రయాణ మార్గం (వేపాయింట్లు):",
    seq: "క్రమం",
    evidenceTitle: "Domain Agent Evidence:",
    weatherAgent: "🌪️ Weather Intelligence:",
    oceanAgent: "🌊 Ocean Analytics:",
    geofenceAgent: "🛡️ Geofence & Boundary:",
    pfzAgent: "🛰️ PFZ Discovery:"
  },
  ta: {
    title: "🌊 ஆர்கா கடல்சார் AI",
    subtitle: "இஸ்ரோ SIH26176 பல-முகவர் கடல்சார் புலனாய்வு அமைப்பு",
    langLabel: "வட்டார மொழி:",
    useGPS: "📍 நேரடி GPS",
    placeholder: "கடற்கரை இடம் அல்லது வினவலை உள்ளிடவும்...",
    btnAnalyze: "கடல் நிலையை பகுப்பாய்வு செய்க 🎙️",
    btnLoading: "செயற்கைக்கோள் தரவு பகுப்பாய்வு செய்யப்படுகிறது...",
    errorTitle: "பிழை",
    statusLabel: "நிலை",
    safe: "பாதுகாப்பானது (SAFE)",
    caution: "எச்சரிக்கை (CAUTION)",
    critical: "ஆபத்தானது (CRITICAL)",
    waypointsTitle: "📍 பாதுகாப்பான வழிசெலுத்தல் புள்ளிகள்:",
    seq: "வரிசை",
    evidenceTitle: "Domain Agent Evidence:",
    weatherAgent: "🌪️ Weather Intelligence:",
    oceanAgent: "🌊 Ocean Analytics:",
    geofenceAgent: "🛡️ Geofence & Boundary:",
    pfzAgent: "🛰️ PFZ Discovery:"
  },
  hi: {
    title: "🌊 ओर्का मरीन एआई",
    subtitle: "इसरो SIH26176 बहु-एजेंट समुद्री बुद्धिमत्ता प्रणाली",
    langLabel: "क्षेत्रीय भाषा:",
    useGPS: "📍 लाइव जीपीएस",
    placeholder: "तटीय स्थान या समुद्री प्रश्न दर्ज करें...",
    btnAnalyze: "समुद्री स्थितियों का विश्लेषण करें 🎙️",
    btnLoading: "उपग्रह डेटा का विश्लेषण जारी है...",
    errorTitle: "त्रुटि",
    statusLabel: "स्थिति",
    safe: "सुरक्षित (SAFE)",
    caution: "सावधानी (CAUTION)",
    critical: "खतरा (CRITICAL)",
    waypointsTitle: "📍 सुरक्षित नेविगेशन वेपॉइंट्स:",
    seq: "चरण",
    evidenceTitle: "Domain Agent Evidence:",
    weatherAgent: "🌪️ Weather Intelligence:",
    oceanAgent: "🌊 Ocean Analytics:",
    geofenceAgent: "🛡️ Geofence & Boundary:",
    pfzAgent: "🛰️ PFZ Discovery:"
  },
  en: {
    title: "🌊 ORCA Marine AI",
    subtitle: "ISRO SIH26176 Global Multi-Agent Marine Intelligence",
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
    pfzAgent: "🛰️ PFZ Discovery:"
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

        {/* Scrollable Results Section matching Screenshot (414) */}
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

              {/* Waypoint 3 Card at Top (Matching Screenshot 414) */}
              {advisory.nav_waypoints && advisory.nav_waypoints.length >= 3 && (
                <div className="agent-card" style={{ border: '1px solid #38bdf8' }}>
                  <strong style={{ color: '#38bdf8' }}>
                    Seq 3: {advisory.nav_waypoints[2].name}
                  </strong>
                  <div style={{ fontSize: '0.80rem', color: '#cbd5e1' }}>
                    {advisory.nav_waypoints[2].nav_instruction}
                  </div>
                </div>
              )}

              {/* Domain Agent Evidence Header */}
              <h3 style={{ fontSize: '0.96rem', color: '#ffffff', marginTop: '6px' }}>
                {t.evidenceTitle}
              </h3>

              {/* Four Evidence Cards (Weather, Ocean, Geofence, PFZ) */}
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

      {/* Map View matching Screenshot (414) */}
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

          {/* 3 Waypoint Pins */}
          {advisory?.nav_waypoints?.map(wp => (
            <Marker key={wp.sequence} position={wp.coordinates}>
              <Popup>
                <strong>{wp.name}</strong><br />
                {wp.nav_instruction}
              </Popup>
            </Marker>
          ))}

          {/* Green Corridor Box */}
          {advisory?.geojson_overlays?.safe_zone && (
            <GeoJSON 
              key={`safe-${mapCenter.join('-')}`}
              data={advisory.geojson_overlays.safe_zone}
              style={{ color: '#10b981', fillColor: '#10b981', fillOpacity: 0.18, weight: 2 }}
            />
          )}

          {/* Cyan PFZ Feeding Zone Circle (around Pin 3) */}
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
                layer.bindPopup(`
                  <div style="color: #0f172a; font-family: sans-serif;">
                    <strong style="color: #0891b2;">🐟 Potential Fishing Zone (PFZ)</strong><br/>
                    <b>Chlorophyll:</b> ${feature.properties.chlorophyll || '1.85 mg/m³'}<br/>
                    <b>Satellite:</b> ${feature.properties.sensor || 'Sentinel-3 / NOAA VIIRS'}<br/>
                    <small>High pelagic fish aggregation sector</small>
                  </div>
                `);
              }}
            />
          )}

          {/* Red Offshore Hazard Sector */}
          {advisory?.geojson_overlays?.danger_zone && (
            <GeoJSON 
              key={`danger-${mapCenter.join('-')}`}
              data={advisory.geojson_overlays.danger_zone}
              style={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.28, weight: 2 }}
            />
          )}
        </MapContainer>
      </div>
    </div>
  );
}

export default App;
