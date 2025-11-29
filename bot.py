from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import time
import random

app = Flask(__name__)
CORS(app)

# Base URL
BASE_URL = "https://dosya.alwaysdata.net/api"

# Random User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def create_response(data, success=True):
    return {
        "success": success,
        "data": data,
        "developer": "nabisystem",
        "version": "1.0"
    }

def call_target_api(url):
    """Hedef API'yi çağır ve hata yönetimi yap"""
    headers = {
        'User-Agent': get_random_user_agent(),
        'Accept': 'application/json',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)  # 30 saniye timeout
        
        if response.status_code == 403:
            return {"error": "nabi apiyi kapati"}
        elif response.status_code == 429:
            return {"error": "sunucu yoğun olduğundan yanit olmadin oc birdaha at oe"}
        elif response.status_code != 200:
            return {"error": "hedef api yanit vermedi"}
            
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "sunucu yoğun olduğundan yanit olmadin oc birdaha at oe"}
    except requests.exceptions.ConnectionError:
        return {"error": "hedef apiye baglanilamadi"}
    except Exception as e:
        return {"error": "hedef api yanit vermedi"}

# TC Kimlik Sorgulama
@app.route('/api/tc', methods=['GET'])
def tc_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/tc.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Ad Soyad Sorgulama - Özel kontrol
@app.route('/api/adsoyad', methods=['GET'])
def adsoyad_sorgu():
    ad = request.args.get('ad', '')
    soyad = request.args.get('soyad', '')
    il = request.args.get('il', '')
    ilce = request.args.get('ilce', '')
    
    # Özel kontrol: roket atar sorgusu
    if ad.lower() == "roket" and soyad.lower() == "atar":
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    try:
        url = f"{BASE_URL}/adsoyad.php?ad={ad}&soyad={soyad}"
        if il:
            url += f"&il={il}"
        if ilce:
            url += f"&ilce={ilce}"
            
        result = call_target_api(url)
        
        if "error" in result:
            return jsonify(create_response(result, False))
            
        if "developer" in result:
            result["developer"] = "nabisystem"
        if "version" in result:
            result["version"] = "1.0"
            
        return jsonify(create_response(result))
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# Ad Soyad Profil Sorgulama (TC'den tüm bilgiler)
@app.route('/api/adsoyadpro', methods=['GET'])
def adsoyadpro_sorgu():
    ad = request.args.get('ad', '')
    soyad = request.args.get('soyad', '')
    
    if not ad or not soyad:
        return jsonify(create_response({"error": "Ad ve soyad parametresi gerekli"}, False))
    
    try:
        # Önce ad soyad sorgusu
        adsoyad_result = call_target_api(f"{BASE_URL}/adsoyad.php?ad={ad}&soyad={soyad}")
        
        if "error" in adsoyad_result:
            return jsonify(create_response(adsoyad_result, False))
        
        # TC'yi al
        tc = None
        if "tc" in adsoyad_result:
            tc = adsoyad_result["tc"]
        elif "tckimlik" in adsoyad_result:
            tc = adsoyad_result["tckimlik"]
        
        if not tc:
            return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
        
        # TC ile diğer bilgileri al
        gsm_data = call_target_api(f"{BASE_URL}/tcgsm.php?tc={tc}")
        adres_data = call_target_api(f"{BASE_URL}/adres.php?tc={tc}")
        
        # Tüm verileri birleştir
        combined_data = {
            "temel_bilgiler": adsoyad_result,
            "iletisim": gsm_data if "error" not in gsm_data else {},
            "adres": adres_data if "error" not in adres_data else {}
        }
        
        combined_data["developer"] = "nabisystem"
        combined_data["version"] = "1.0"
        
        return jsonify(create_response(combined_data))
        
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# Aile Bilgileri
@app.route('/api/aile', methods=['GET'])
def aile_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# TC'den GSM Sorgulama
@app.route('/api/tcgsm', methods=['GET'])
def tcgsm_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/tcgsm.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# GSM'den TC Sorgulama
@app.route('/api/gsmtc', methods=['GET'])
def gsmtc_sorgu():
    gsm = request.args.get('gsm')
    
    if not gsm:
        return jsonify(create_response({"error": "GSM parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/gsmtc.php?gsm={gsm}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Operatör Sorgulama
@app.route('/api/operator', methods=['GET'])
def operator_sorgu():
    numara = request.args.get('numara')
    
    if not numara:
        return jsonify(create_response({"error": "numara parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/gncloperator.php?numara={numara}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Adres Sorgulama
@app.route('/api/adres', methods=['GET'])
def adres_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/adres.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Hane Adres Sorgulama
@app.route('/api/haneadres', methods=['GET'])
def haneadres_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/haneadres.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# TC Detay Sorgulama
@app.route('/api/tc2', methods=['GET'])
def tc2_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/tc2.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Burç Sorgulama
@app.route('/api/burc', methods=['GET'])
def burc_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/burc.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Sülale Sorgulama
@app.route('/api/sulale', methods=['GET'])
def sulale_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/sulale.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Sülaleden Hala Sorgulama
@app.route('/api/sulaledenhalasorgu', methods=['GET'])
def sulaledenhalasorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/sulale.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    # Halaları filtrele
    halalar = []
    if "akrabalar" in result:
        for akraba in result["akrabalar"]:
            if akraba.get("yakınlık", "").lower() in ["hala", "halaoglu", "halaoğlu"]:
                halalar.append(akraba)
    
    if not halalar:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    result["halalar"] = halalar
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Sülaleden Amca Sorgulama
@app.route('/api/sulaledenamcasorgu', methods=['GET'])
def sulaledenamcasorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/sulale.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    # Amcaları filtrele
    amcalar = []
    if "akrabalar" in result:
        for akraba in result["akrabalar"]:
            if akraba.get("yakınlık", "").lower() in ["amca", "amcaoglu", "amcaoğlu"]:
                amcalar.append(akraba)
    
    if not amcalar:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    result["amcalar"] = amcalar
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Sülaleden Dayı Sorgulama
@app.route('/api/sulaledendayisorgu', methods=['GET'])
def sulaledendayisorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/sulale.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    # Dayıları filtrele
    dayilar = []
    if "akrabalar" in result:
        for akraba in result["akrabalar"]:
            if akraba.get("yakınlık", "").lower() in ["dayı", "dayi", "dayioğlu", "dayioglu"]:
                dayilar.append(akraba)
    
    if not dayilar:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    result["dayilar"] = dayilar
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Sülaleden Teyze Sorgulama
@app.route('/api/sulaledenteyzesorgu', methods=['GET'])
def sulaledenteyzesorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/sulale.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    # Teyzeleri filtrele
    teyzeler = []
    if "akrabalar" in result:
        for akraba in result["akrabalar"]:
            if akraba.get("yakınlık", "").lower() in ["teyze", "teyzeoğlu", "teyzeoglu"]:
                teyzeler.append(akraba)
    
    if not teyzeler:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    result["teyzeler"] = teyzeler
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Yaş Sorgulama
@app.route('/api/yas', methods=['GET'])
def yas_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/yas.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# IBAN Sorgulama
@app.route('/api/iban', methods=['GET'])
def iban_sorgu():
    iban = request.args.get('iban')
    
    if not iban:
        return jsonify(create_response({"error": "IBAN parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/iban.php?iban={iban}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Eş Sorgulama
@app.route('/api/es', methods=['GET'])
def es_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/es.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Çocuk Sorgulama
@app.route('/api/cocuk', methods=['GET'])
def cocuk_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/cocuk.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Erkek Çocuk Sorgulama
@app.route('/api/erkekcocuk', methods=['GET'])
def erkekcocuk_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/cocuk.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    # Sadece erkek çocukları filtrele
    erkek_cocuklar = []
    if "cocuklar" in result:
        for cocuk in result["cocuklar"]:
            if cocuk.get("cinsiyet", "").lower() in ["erkek", "e"]:
                erkek_cocuklar.append(cocuk)
    
    if not erkek_cocuklar:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    result["cocuklar"] = erkek_cocuklar
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Kız Çocuk Sorgulama
@app.route('/api/kizcocuk', methods=['GET'])
def kizcocuk_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/cocuk.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    # Sadece kız çocukları filtrele
    kiz_cocuklar = []
    if "cocuklar" in result:
        for cocuk in result["cocuklar"]:
            if cocuk.get("cinsiyet", "").lower() in ["kiz", "kız", "k"]:
                kiz_cocuklar.append(cocuk)
    
    if not kiz_cocuklar:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    result["cocuklar"] = kiz_cocuklar
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Kardeş Sorgulama
@app.route('/api/kardes', methods=['GET'])
def kardes_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/kardes.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Log Sorgulama
@app.route('/api/log', methods=['GET'])
def log_sorgu():
    site = request.args.get('site')
    
    if not site:
        return jsonify(create_response({"error": "site parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/log.php?site={site}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Soy Ağacı Sorgulama
@app.route('/api/soyagaci', methods=['GET'])
def soyagaci_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/soyagaci.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
        
    if "developer" in result:
        result["developer"] = "nabisystem"
    if "version" in result:
        result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Anne Sorgulama
@app.route('/api/anne', methods=['GET'])
def anne_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    # Önce aile sorgusu yap
    aile_result = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
    
    if "error" in aile_result:
        return jsonify(create_response(aile_result, False))
    
    # Anne'yi bul
    anne_tc = None
    if "aile" in aile_result:
        for uye in aile_result["aile"]:
            if uye.get("yakınlık", "").lower() in ["anne", "mother"]:
                anne_tc = uye.get("tc")
                break
    
    if not anne_tc:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    # Anne'nin TC'si ile detaylı sorgu yap
    anne_detay = call_target_api(f"{BASE_URL}/tc.php?tc={anne_tc}")
    
    if "error" in anne_detay:
        return jsonify(create_response(anne_detay, False))
    
    result = {
        "anne_tc": anne_tc,
        "anne_detay": anne_detay
    }
    
    result["developer"] = "nabisystem"
    result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Baba Sorgulama
@app.route('/api/baba', methods=['GET'])
def baba_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    # Önce aile sorgusu yap
    aile_result = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
    
    if "error" in aile_result:
        return jsonify(create_response(aile_result, False))
    
    # Baba'yı bul
    baba_tc = None
    if "aile" in aile_result:
        for uye in aile_result["aile"]:
            if uye.get("yakınlık", "").lower() in ["baba", "father"]:
                baba_tc = uye.get("tc")
                break
    
    if not baba_tc:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    # Baba'nın TC'si ile detaylı sorgu yap
    baba_detay = call_target_api(f"{BASE_URL}/tc.php?tc={baba_tc}")
    
    if "error" in baba_detay:
        return jsonify(create_response(baba_detay, False))
    
    result = {
        "baba_tc": baba_tc,
        "baba_detay": baba_detay
    }
    
    result["developer"] = "nabisystem"
    result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Ded
# Ded Sorgulama
@app.route('/api/dede', methods=['GET'])
def ded_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    # Önce aile sorgusu yap
    aile_result = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
    
    if "error" in aile_result:
        return jsonify(create_response(aile_result, False))
    
    # Baba'nın TC'sini bul
    baba_tc = None
    if "aile" in aile_result:
        for uye in aile_result["aile"]:
            if uye.get("yakınlık", "").lower() in ["baba", "father"]:
                baba_tc = uye.get("tc")
                break
    
    if not baba_tc:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    # Baba'nın ailesini sorgula (dede için)
    baba_aile = call_target_api(f"{BASE_URL}/aile.php?tc={baba_tc}")
    
    if "error" in baba_aile:
        return jsonify(create_response(baba_aile, False))
    
    # Dedeyi bul (baba'nın babası)
    dede_tc = None
    if "aile" in baba_aile:
        for uye in baba_aile["aile"]:
            if uye.get("yakınlık", "").lower() in ["baba", "father"]:
                dede_tc = uye.get("tc")
                break
    
    if not dede_tc:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    # Dede'nin detaylarını getir
    dede_detay = call_target_api(f"{BASE_URL}/tc.php?tc={dede_tc}")
    
    if "error" in dede_detay:
        return jsonify(create_response(dede_detay, False))
    
    result = {
        "dede_tc": dede_tc,
        "dede_detay": dede_detay
    }
    
    result["developer"] = "nabisystem"
    result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Nine Sorgulama
@app.route('/api/nine', methods=['GET'])
def nine_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    # Önce aile sorgusu yap
    aile_result = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
    
    if "error" in aile_result:
        return jsonify(create_response(aile_result, False))
    
    # Anne'nin TC'sini bul
    anne_tc = None
    if "aile" in aile_result:
        for uye in aile_result["aile"]:
            if uye.get("yakınlık", "").lower() in ["anne", "mother"]:
                anne_tc = uye.get("tc")
                break
    
    if not anne_tc:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    # Anne'nin ailesini sorgula (nine için)
    anne_aile = call_target_api(f"{BASE_URL}/aile.php?tc={anne_tc}")
    
    if "error" in anne_aile:
        return jsonify(create_response(anne_aile, False))
    
    # Nine'yi bul (anne'nin annesi)
    nine_tc = None
    if "aile" in anne_aile:
        for uye in anne_aile["aile"]:
            if uye.get("yakınlık", "").lower() in ["anne", "mother"]:
                nine_tc = uye.get("tc")
                break
    
    if not nine_tc:
        return jsonify(create_response({"sonuc": "sonuc bulunamadi"}, True))
    
    # Nine'nin detaylarını getir
    nine_detay = call_target_api(f"{BASE_URL}/tc.php?tc={nine_tc}")
    
    if "error" in nine_detay:
        return jsonify(create_response(nine_detay, False))
    
    result = {
        "nine_tc": nine_tc,
        "nine_detay": nine_detay
    }
    
    result["developer"] = "nabisystem"
    result["version"] = "1.0"
        
    return jsonify(create_response(result))

# Tam Aile Ağacı Sorgulama
@app.route('/api/tamamileagaci', methods=['GET'])
def tamamileagaci_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    try:
        # Tüm aile bilgilerini topla
        temel_bilgiler = call_target_api(f"{BASE_URL}/tc.php?tc={tc}")
        aile_bilgileri = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
        cocuk_bilgileri = call_target_api(f"{BASE_URL}/cocuk.php?tc={tc}")
        sulale_bilgileri = call_target_api(f"{BASE_URL}/sulale.php?tc={tc}")
        
        # Hata kontrolü
        errors = []
        if "error" in temel_bilgiler:
            errors.append("Temel bilgiler alınamadı")
        if "error" in aile_bilgileri:
            errors.append("Aile bilgileri alınamadı")
        
        if errors:
            return jsonify(create_response({"error": " | ".join(errors)}, False))
        
        # Tüm verileri birleştir
        aile_agaci = {
            "kisi_bilgileri": temel_bilgiler,
            "aile_uyeleri": aile_bilgileri.get("aile", []),
            "cocuklar": cocuk_bilgileri.get("cocuklar", []) if "error" not in cocuk_bilgileri else [],
            "akrabalar": sulale_bilgileri.get("akrabalar", []) if "error" not in sulale_bilgileri else []
        }
        
        aile_agaci["developer"] = "nabisystem"
        aile_agaci["version"] = "1.0"
        
        return jsonify(create_response(aile_agaci))
        
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# TC ve GSM Birleşik Sorgu
@app.route('/api/tcvegsm', methods=['GET'])
def tcvegsm_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    try:
        tc_bilgileri = call_target_api(f"{BASE_URL}/tc.php?tc={tc}")
        gsm_bilgileri = call_target_api(f"{BASE_URL}/tcgsm.php?tc={tc}")
        
        combined_data = {
            "tc_bilgileri": tc_bilgileri,
            "gsm_bilgileri": gsm_bilgileri
        }
        
        combined_data["developer"] = "nabisystem"
        combined_data["version"] = "1.0"
        
        return jsonify(create_response(combined_data))
        
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# Adres ve GSM Birleşik Sorgu
@app.route('/api/adresvegsm', methods=['GET'])
def adresvegsm_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    try:
        adres_bilgileri = call_target_api(f"{BASE_URL}/adres.php?tc={tc}")
        gsm_bilgileri = call_target_api(f"{BASE_URL}/tcgsm.php?tc={tc}")
        
        combined_data = {
            "adres_bilgileri": adres_bilgileri,
            "gsm_bilgileri": gsm_bilgileri
        }
        
        combined_data["developer"] = "nabisystem"
        combined_data["version"] = "1.0"
        
        return jsonify(create_response(combined_data))
        
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# Tüm İletişim Bilgileri
@app.route('/api/tumiletisim', methods=['GET'])
def tumiletisim_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    try:
        gsm_bilgileri = call_target_api(f"{BASE_URL}/tcgsm.php?tc={tc}")
        adres_bilgileri = call_target_api(f"{BASE_URL}/adres.php?tc={tc}")
        hane_adres_bilgileri = call_target_api(f"{BASE_URL}/haneadres.php?tc={tc}")
        
        combined_data = {
            "telefon_bilgileri": gsm_bilgileri,
            "adres_bilgileri": adres_bilgileri,
            "hane_adres_bilgileri": hane_adres_bilgileri
        }
        
        combined_data["developer"] = "nabisystem"
        combined_data["version"] = "1.0"
        
        return jsonify(create_response(combined_data))
        
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# Çocuk Sayısı Sorgulama
@app.route('/api/cocuksayisi', methods=['GET'])
def cocuksayisi_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/cocuk.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    erkek_sayisi = 0
    kiz_sayisi = 0
    toplam_cocuk = 0
    
    if "cocuklar" in result:
        toplam_cocuk = len(result["cocuklar"])
        for cocuk in result["cocuklar"]:
            if cocuk.get("cinsiyet", "").lower() in ["erkek", "e"]:
                erkek_sayisi += 1
            elif cocuk.get("cinsiyet", "").lower() in ["kiz", "kız", "k"]:
                kiz_sayisi += 1
    
    sonuc = {
        "toplam_cocuk": toplam_cocuk,
        "erkek_cocuk": erkek_sayisi,
        "kiz_cocuk": kiz_sayisi,
        "cocuk_listesi": result.get("cocuklar", [])
    }
    
    sonuc["developer"] = "nabisystem"
    sonuc["version"] = "1.0"
    
    return jsonify(create_response(sonuc))

# Kardeş Sayısı Sorgulama
@app.route('/api/kardessayisi', methods=['GET'])
def kardessayisi_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    result = call_target_api(f"{BASE_URL}/kardes.php?tc={tc}")
    
    if "error" in result:
        return jsonify(create_response(result, False))
    
    kardes_sayisi = 0
    if "kardesler" in result:
        kardes_sayisi = len(result["kardesler"])
    
    sonuc = {
        "kardes_sayisi": kardes_sayisi,
        "kardes_listesi": result.get("kardesler", [])
    }
    
    sonuc["developer"] = "nabisystem"
    sonuc["version"] = "1.0"
    
    return jsonify(create_response(sonuc))

# Aile Büyüklüğü Sorgulama
@app.route('/api/ailebuyuklugu', methods=['GET'])
def ailebuyuklugu_sorgu():
    tc = request.args.get('tc')
    
    if not tc:
        return jsonify(create_response({"error": "TC parametresi gerekli"}, False))
    
    try:
        aile_bilgileri = call_target_api(f"{BASE_URL}/aile.php?tc={tc}")
        cocuk_bilgileri = call_target_api(f"{BASE_URL}/cocuk.php?tc={tc}")
        kardes_bilgileri = call_target_api(f"{BASE_URL}/kardes.php?tc={tc}")
        
        aile_uyesi_sayisi = len(aile_bilgileri.get("aile", [])) if "error" not in aile_bilgileri else 0
        cocuk_sayisi = len(cocuk_bilgileri.get("cocuklar", [])) if "error" not in cocuk_bilgileri else 0
        kardes_sayisi = len(kardes_bilgileri.get("kardesler", [])) if "error" not in kardes_bilgileri else 0
        
        toplam_aile_buyuklugu = 1 + aile_uyesi_sayisi + cocuk_sayisi + kardes_sayisi  # 1 kişi kendisi
        
        sonuc = {
            "toplam_aile_buyuklugu": toplam_aile_buyuklugu,
            "aile_uyesi_sayisi": aile_uyesi_sayisi,
            "cocuk_sayisi": cocuk_sayisi,
            "kardes_sayisi": kardes_sayisi,
            "aciklama": "Toplam aile büyüklüğü kişinin kendisi + aile üyeleri + çocuklar + kardeşler şeklinde hesaplanmıştır"
        }
        
        sonuc["developer"] = "nabisystem"
        sonuc["version"] = "1.0"
        
        return jsonify(create_response(sonuc))
        
    except Exception as e:
        return jsonify(create_response({"error": "hedef api yanit vermedi"}, False))

# API Durum Kontrolü
@app.route('/api/durum', methods=['GET'])
def api_durum():
    """Tüm API'lerin durumunu kontrol et"""
    apiler = {
        "tc": f"{BASE_URL}/tc.php?tc=11111111110",
        "adsoyad": f"{BASE_URL}/adsoyad.php?ad=test&soyad=test",
        "aile": f"{BASE_URL}/aile.php?tc=11111111110",
        "tcgsm": f"{BASE_URL}/tcgsm.php?tc=11111111110"
    }
    
    durumlar = {}
    
    for api_adi, api_url in apiler.items():
        try:
            response = requests.get(api_url, timeout=10)
            durumlar[api_adi] = {
                "durum": "calisiyor" if response.status_code == 200 else "hata",
                "status_code": response.status_code
            }
        except:
            durumlar[api_adi] = {
                "durum": "calismiyor",
                "status_code": 0
            }
    
    sonuc = {
        "api_durumlari": durumlar,
        "toplam_api": len(apiler),
        "calisan_api": sum(1 for d in durumlar.values() if d["durum"] == "calisiyor"),
        "server_zamani": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    sonuc["developer"] = "nabisystem"
    sonuc["version"] = "1.0"
    
    return jsonify(create_response(sonuc))

# Ana Sayfa
@app.route('/')
def ana_sayfa():
    return """
    <html>
        <head>
            <title>Nabisystem API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 5px; }
                .method { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🚀 Nabisystem API</h1>
            <p>Toplam <strong>50+</strong> API endpoint mevcut</p>
            <p><strong>Developer:</strong> nabisystem | <strong>Version:</strong> 1.0</p>
            
            <h3>📋 Temel Endpoint'ler:</h3>
            <div class="endpoint"><span class="method">GET</span> /api/tc?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/adsoyad?ad=mehmet&soyad=yilmaz</div>
            <div class="endpoint"><span class="method">GET</span> /api/aile?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/tcgsm?tc=11111111110</div>
            
            <h3>👨‍👩‍👧‍👦 Aile Endpoint'leri:</h3>
            <div class="endpoint"><span class="method">GET</span> /api/anne?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/baba?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/ded?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/nine?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/erkekcocuk?tc=11111111110</div>
            <div class="endpoint"><span class="method">GET</span> /api/kizcocuk?tc=11111111110</div>
            
            <p><a href="/api/durum">🔍 API Durum Kontrolü</a></p>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
