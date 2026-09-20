import re
from deep_translator import GoogleTranslator

SUPPORTED_LANGUAGES = {
    "hi": "hindi",
    "te": "telugu",
    "ta": "tamil",
    "en": "english"
}

def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translates incoming user query from regional languages into English
    for processing in the multi-agent graph.
    """
    if not text or not source_lang or source_lang == "en":
        return text
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"[Translation to English error]: {e}")
        return text

def translate_hindi_marine_text(text: str) -> str:
    """
    Translates marine operational terms, waypoints, and agent evidence into Hindi.
    Includes regex replacements to handle composite sentences and brackets.
    """
    if not text:
        return text
    try:
        res = GoogleTranslator(source='auto', target='hi').translate(text)
        if res and not any(phrase in res for phrase in ["Conditions favorable", "Depart coastline", "Significant wave height"]):
            return res
    except Exception:
        pass

    t = text
    # Status & Directives
    t = re.sub(
        r'GO:\s*Conditions favorable off (.*?)\.\s*Clear satellite navigation route identified\.',
        r'जाइए (GO): \1 के पास समुद्री स्थितियां पूरी तरह अनुकूल हैं। सुरक्षित उपग्रह नेविगेशन मार्ग उपलब्ध है।',
        t
    )
    t = re.sub(
        r'CAUTION:\s*Elevated swell or choppy conditions off (.*?)\.\s*Large motorized vessels advised only\.',
        r'सावधानी (CAUTION): \1 के पास ऊंची समुद्री लहरें हैं। केवल बड़ी मोटरबोट को जाने की सलाह दी जाती है।',
        t
    )
    t = re.sub(
        r'NO-GO:\s*Dangerous conditions or restricted border sector detected off (.*?)\.\s*Sailing prohibited\.',
        r'मत जाइए (NO-GO): \1 के पास गंभीर समुद्री खतरा या प्रतिबंधित सीमा क्षेत्र है। समुद्र में जाना सख्त मना है।',
        t
    )

    # Waypoints & Nav Instructions
    t = re.sub(r'Berth:\s*(.*)', r'प्रस्थान बर्थ: \1', t)
    t = t.replace("Safe Coastal Transit Corridor", "सुरक्षित तटीय पारगमन गलियारा")
    t = t.replace("Satellite PFZ Feeding Grounds", "उपग्रह-आधारित संभावित मत्स्य पालन क्षेत्र (PFZ)")
    t = t.replace("Depart coastline heading outward to open waters.", "तट से प्रस्थान कर गहरे समुद्र की ओर बढ़ें।")
    t = t.replace("Steer clear of coastal shallows and designated protected buffers.", "तटीय उथले क्षेत्रों और पर्यावरण-संरक्षित बफर क्षेत्रों से दूर रहें।")
    t = t.replace("Arrive at chlorophyll-rich thermal boundary.", "क्लोरोफिल-समृद्ध और अनुकूल तापमान वाले मत्स्य क्षेत्र में पहुंचें।")

    # Telemetry
    t = re.sub(
        r'Wind:\s*([\d\.]+)\s*kts,\s*Gusts:\s*([\d\.]+)\s*kts\.\s*Squall warning:\s*(.*?)\.\s*\[Source:\s*(.*?)\]',
        r'हवा की गति: \1 समुद्री मील (kts), झोंके: \2 kts। तूफान की चेतावनी: \3। [स्रोत: \4]',
        t
    )
    t = re.sub(
        r'Significant wave height:\s*([\d\.]+)m,\s*Swell period:\s*([\d\.]+)s,\s*SST:\s*([\d\.]+)°C\.\s*\[Source:\s*(.*?)\]',
        r'लहरों की महत्वपूर्ण ऊंचाई: \1 मीटर, स्वेल अवधि: \2 सेकंड, समुद्र सतह तापमान: \3°C। [स्रोत: \4]',
        t
    )
    t = t.replace("IMBL Alert: CLEAR | Protected Area: CLEAR.", "अंतर्राष्ट्रीय समुद्री सीमा (IMBL): सुरक्षित (CLEAR) | संरक्षित समुद्री क्षेत्र: सुरक्षित (CLEAR)।")
    t = t.replace("IMBL Alert: ACTIVE | Protected Area: RESTRICTED.", "अंतर्राष्ट्रीय समुद्री सीमा (IMBL): सक्रिय (खतरा) | संरक्षित समुद्री क्षेत्र: प्रतिबंधित।")
    t = t.replace("IMBL Alert: CLEAR | Protected Area: RESTRICTED.", "अंतर्राष्ट्रीय समुद्री सीमा (IMBL): सुरक्षित | संरक्षित समुद्री क्षेत्र: प्रतिबंधित।")
    t = re.sub(
        r'Active biological feeding zone detected with Chlorophyll-a concentration of ([\d\.]+) mg/m³ and SST of ([\d\.]+)°C\.',
        r'सक्रिय मत्स्य भोजन क्षेत्र मिला: क्लोरोफिल-ए घनत्व \1 mg/m³ और समुद्र सतह तापमान \2°C दर्ज किया गया।',
        t
    )

    t = t.replace("CLEAR", "सुरक्षित").replace("ACTIVE", "सक्रिय (खतरा)").replace("RESTRICTED", "प्रतिबंधित")
    t = t.replace("NOAA WaveWatch III / ECMWF Global Marine Analysis", "नोवा वेववॉच III / ईसीएमडब्ल्यूएफ वैश्विक समुद्री विश्लेषण")
    t = t.replace("Live Copernicus / NOAA WaveWatch III", "लाइव कोपरनिकस / नोवा वेववॉच III")
    t = t.replace("Position", "स्थान")
    return t

def translate_telugu_marine_text(text: str) -> str:
    """
    Translates marine operational terms, waypoints, and agent evidence into Telugu.
    Includes regex replacements to handle composite sentences and brackets.
    """
    if not text:
        return text
    try:
        res = GoogleTranslator(source='auto', target='te').translate(text)
        if res and not any(phrase in res for phrase in ["Conditions favorable", "Depart coastline", "Significant wave height"]):
            return res
    except Exception:
        pass

    t = text
    # Status & Directives
    t = re.sub(
        r'GO:\s*Conditions favorable off (.*?)\.\s*Clear satellite navigation route identified\.',
        r'ప్రయాణించవచ్చు (GO): \1 వద్ద సముద్ర పరిస్థితులు అనుకూలంగా ఉన్నాయి. సురక్షిత ఉపగ్రహ నావిగేషన్ మార్గం గుర్తించబడింది.',
        t
    )
    t = re.sub(
        r'CAUTION:\s*Elevated swell or choppy conditions off (.*?)\.\s*Large motorized vessels advised only\.',
        r'హెచ్చరిక (CAUTION): \1 వద్ద సముద్ర అలలు తీవ్రంగా ఉన్నాయి. పెద్ద మోటారు పడవలకు మాత్రమే అనుమతి ఉంది.',
        t
    )
    t = re.sub(
        r'NO-GO:\s*Dangerous conditions or restricted border sector detected off (.*?)\.\s*Sailing prohibited\.',
        r'వెళ్లవద్దు (NO-GO): \1 వద్ద ప్రమాదకర పరిస్థితులు లేదా నిషేధిత సరిహద్దు ప్రాంతం ఉంది. సముద్రంలోకి వేటకు వెళ్లరాదు.',
        t
    )

    # Waypoints & Nav Instructions
    t = re.sub(r'Berth:\s*(.*)', r'బయలుదేరే బెర్త్: \1', t)
    t = t.replace("Safe Coastal Transit Corridor", "సురక్షిత తీరప్రాంత రవాణా కారిడార్")
    t = t.replace("Satellite PFZ Feeding Grounds", "ఉపగ్రహ-ఆధారిత చేపల లభ్యత మండలం (PFZ)")
    t = t.replace("Depart coastline heading outward to open waters.", "తీరం నుంచి బయలుదేరి లోతైన సముద్రం వైపు ప్రయాణించండి.")
    t = t.replace("Steer clear of coastal shallows and designated protected buffers.", "తీరప్రాంత లోతులేని ప్రాంతాలు మరియు పర్యావరణ రక్షిత బఫర్ మండలాల నుండి దూరంగా ఉండండి.")
    t = t.replace("Arrive at chlorophyll-rich thermal boundary.", "క్లోరోఫిల్ అధికంగా ఉన్న అనుకూల ఉష్ణోగ్రత గల చేపల వేట ప్రాంతానికి చేరుకోండి.")

    # Telemetry
    t = re.sub(
        r'Wind:\s*([\d\.]+)\s*kts,\s*Gusts:\s*([\d\.]+)\s*kts\.\s*Squall warning:\s*(.*?)\.\s*\[Source:\s*(.*?)\]',
        r'గాలి వేగం: \1 నాట్స్ (kts), గాలుల తీవ్రత: \2 kts. తుఫాను హెచ్చరిక: \3. [మూలం: \4]',
        t
    )
    t = re.sub(
        r'Significant wave height:\s*([\d\.]+)m,\s*Swell period:\s*([\d\.]+)s,\s*SST:\s*([\d\.]+)°C\.\s*\[Source:\s*(.*?)\]',
        r'సముద్ర అలల ఎత్తు: \1 మీటర్లు, అలల సమయం: \2 సెకన్లు, సముద్ర ఉపరితల ఉష్ణోగ్రత: \3°C. [మూలం: \4]',
        t
    )
    t = t.replace("IMBL Alert: CLEAR | Protected Area: CLEAR.", "అంతర్జాతీయ సముద్ర సరిహద్దు (IMBL): సురక్షితం (CLEAR) | రక్షిత సముద్ర ప్రాంతం: సురక్షితం (CLEAR).")
    t = t.replace("IMBL Alert: ACTIVE | Protected Area: RESTRICTED.", "అంతర్జాతీయ సముద్ర సరిహద్దు (IMBL): ప్రమాదం/సక్రియం | రక్షిత సముద్ర ప్రాంతం: నిషేధితం.")
    t = t.replace("IMBL Alert: CLEAR | Protected Area: RESTRICTED.", "అంతర్జాతీయ సముద్ర సరిహద్దు (IMBL): సురక్షితం | రక్షిత సముద్ర ప్రాంతం: నిషేధితం.")
    t = re.sub(
        r'Active biological feeding zone detected with Chlorophyll-a concentration of ([\d\.]+) mg/m³ and SST of ([\d\.]+)°C\.',
        r'చేపల మేత ప్రాంతం లభ్యమైంది: క్లోరోఫిల్-ఎ సాంద్రత \1 mg/m³ మరియు సముద్ర ఉపరితల ఉష్ణోగ్రత \2°C గా నమోదైంది.',
        t
    )

    t = t.replace("CLEAR", "సురక్షితం").replace("ACTIVE", "సక్రియం (ప్రమాదం)").replace("RESTRICTED", "నిషేధితం")
    t = t.replace("NOAA WaveWatch III / ECMWF Global Marine Analysis", "నోవా వేవ్‌వాచ్ III / ఈసీఎమ్‌డబ్ల్యూఎఫ్ గ్లోబల్ మెరైన్ విశ్లేషణ")
    t = t.replace("Live Copernicus / NOAA WaveWatch III", "లైవ్ కోపర్నికస్ / నోవా వేవ్‌వాచ్ III")
    t = t.replace("Position", "స్థానం")
    return t

def translate_tamil_marine_text(text: str) -> str:
    """
    Translates marine operational terms, waypoints, and agent evidence into Tamil.
    Includes regex replacements to handle composite sentences and brackets.
    """
    if not text:
        return text
    try:
        res = GoogleTranslator(source='auto', target='ta').translate(text)
        if res and not any(phrase in res for phrase in ["Conditions favorable", "Depart coastline", "Significant wave height"]):
            return res
    except Exception:
        pass

    t = text
    # Status & Directives
    t = re.sub(
        r'GO:\s*Conditions favorable off (.*?)\.\s*Clear satellite navigation route identified\.',
        r'செல்லலாம் (GO): \1 பகுதியில் கடல் நிலை முற்றிலும் சாதகமாக உள்ளது. பாதுகாப்பான செயற்கைக்கோள் வழிப்பாதை கண்டறியப்பட்டது.',
        t
    )
    t = re.sub(
        r'CAUTION:\s*Elevated swell or choppy conditions off (.*?)\.\s*Large motorized vessels advised only\.',
        r'எச்சரிக்கை (CAUTION): \1 பகுதியில் கடல் அலைகள் அதிகமாக உள்ளன. பெரிய விசைப்படகுகள் மட்டுமே செல்ல அறிவுறுத்தப்படுகிறது.',
        t
    )
    t = re.sub(
        r'NO-GO:\s*Dangerous conditions or restricted border sector detected off (.*?)\.\s*Sailing prohibited\.',
        r'செல்ல வேண்டாம் (NO-GO): \1 பகுதியில் கடுமையான கடல் ஆபத்து அல்லது தடைசெய்யப்பட்ட எல்லை உள்ளது. கடலுக்குள் செல்ல தடை விதிக்கப்பட்டுள்ளது.',
        t
    )

    # Waypoints & Nav Instructions
    t = re.sub(r'Berth:\s*(.*)', r'புறப்படும் பெர்த்: \1', t)
    t = t.replace("Safe Coastal Transit Corridor", "பாதுகாப்பான கடலோரப் போக்குவரத்து பாதை")
    t = t.replace("Satellite PFZ Feeding Grounds", "செயற்கைக்கோள் வழி கண்டறியப்பட்ட மீன்பிடி மண்டலம் (PFZ)")
    t = t.replace("Depart coastline heading outward to open waters.", "கடற்கரையில் இருந்து புறப்பட்டு ஆழ்கடலை நோக்கி செல்லவும்.")
    t = t.replace("Steer clear of coastal shallows and designated protected buffers.", "ஆழமற்ற கடலோர பகுதிகள் மற்றும் பாதுகாக்கப்பட்ட மண்டலங்களை கடந்து செல்லவும்.")
    t = t.replace("Arrive at chlorophyll-rich thermal boundary.", "குளோரோபில் நிறைந்த மற்றும் உகந்த வெப்பநிலையுள்ள மீன்பிடி மண்டலத்தை அடையுங்கள்.")

    # Telemetry
    t = re.sub(
        r'Wind:\s*([\d\.]+)\s*kts,\s*Gusts:\s*([\d\.]+)\s*kts\.\s*Squall warning:\s*(.*?)\.\s*\[Source:\s*(.*?)\]',
        r'காற்றின் வேகம்: \1 நாட்ஸ் (kts), சூறாவளி காற்று: \2 kts. புயல் எச்சரிக்கை: \3. [மூலம்: \4]',
        t
    )
    t = re.sub(
        r'Significant wave height:\s*([\d\.]+)m,\s*Swell period:\s*([\d\.]+)s,\s*SST:\s*([\d\.]+)°C\.\s*\[Source:\s*(.*?)\]',
        r'கடல் அலையின் உயரம்: \1 மீட்டர், அலை காலம்: \2 வினாடிகள், கடல் மேற்பரப்பு வெப்பநிலை: \3°C. [மூலம்: \4]',
        t
    )
    t = t.replace("IMBL Alert: CLEAR | Protected Area: CLEAR.", "சர்வதேச கடல் எல்லை (IMBL): பாதுகாப்பானது (CLEAR) | பாதுகாக்கப்பட்ட கடல் பகுதி: பாதுகாப்பானது (CLEAR).")
    t = t.replace("IMBL Alert: ACTIVE | Protected Area: RESTRICTED.", "சர்வதேச கடல் எல்லை (IMBL): தீவிர எச்சரிக்கை | பாதுகாக்கப்பட்ட கடல் பகுதி: தடைசெய்யப்பட்டுள்ளது.")
    t = t.replace("IMBL Alert: CLEAR | Protected Area: RESTRICTED.", "சர்வதேச கடல் எல்லை (IMBL): பாதுகாப்பானது | பாதுகாக்கப்பட்ட கடல் பகுதி: தடைசெய்யப்பட்டுள்ளது.")
    t = re.sub(
        r'Active biological feeding zone detected with Chlorophyll-a concentration of ([\d\.]+) mg/m³ and SST of ([\d\.]+)°C\.',
        r'செயலில் உள்ள மீன் உணவு மண்டலம் கண்டறியப்பட்டது: குளோரோபில்-ஏ செறிவு \1 mg/m³ மற்றும் கடல் வெப்பநிலை \2°C பதிவாகியுள்ளது.',
        t
    )

    t = t.replace("CLEAR", "பாதுகாப்பானது").replace("ACTIVE", "தீவிர எச்சரிக்கை").replace("RESTRICTED", "தடைசெய்யப்பட்டது")
    t = t.replace("NOAA WaveWatch III / ECMWF Global Marine Analysis", "நோவா வேவ்வாட்ச் III / இசிஎம்டபிள்யூஎஃப் உலகளாவிய கடல்சார் பகுப்பாய்வு")
    t = t.replace("Live Copernicus / NOAA WaveWatch III", "நேரடி கோப்பர்நிக்கஸ் / நோவா வேவ்வாட்ச் III")
    t = t.replace("Position", "இடம்")
    return t

def translate_advisory_text(text: str, target_lang: str) -> str:
    """
    Entry point for translating synthesized agent advisories, waypoints,
    and domain evidence into the selected regional language.
    """
    if not text or not target_lang or target_lang == "en":
        return text

    if target_lang == "hi":
        return translate_hindi_marine_text(text)
    elif target_lang == "te":
        return translate_telugu_marine_text(text)
    elif target_lang == "ta":
        return translate_tamil_marine_text(text)

    # General fallback for other ISO language codes
    try:
        target = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"[Translation fallback error for {target_lang}]: {e}")
        return text