from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Desteklenen Ligler ve ID'leri (TheSportsDB)
LIGLER = {
    "superlig": {"id": "4339", "ad": "Süper Lig", "bayrak": "🇹🇷"},
    "premier": {"id": "4328", "ad": "Premier League", "bayrak": "🏴󠁧󠁢󠁥󠁮󠁧󠁿"},
    "laliga": {"id": "4335", "ad": "La Liga", "bayrak": "🇪🇸"},
    "champions": {"id": "4480", "ad": "Şampiyonlar Ligi", "bayrak": "🇪🇺"}
}

# 1. DİNAMİK LİG MAÇLARI GETİR
def gercek_maclari_getir(lig_id):
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/eventspastleague.php?id={lig_id}"
        yanit = requests.get(url, timeout=5)
        if yanit.status_code == 200:
            veri = yanit.json()
            maclar = []
            for m in veri.get("events", [])[:10]:
                maclar.append({
                    "id": m.get("idEvent"),
                    "ev": m.get("strHomeTeam"),
                    "deplasman": m.get("strAwayTeam"),
                    "skor_ev": m.get("intHomeScore"),
                    "skor_dep": m.get("intAwayScore"),
                    "tarih": m.get("dateEvent"),
                    "saat": m.get("strTime", "20:00")[:5],
                    "stadyum": m.get("strVenue", "Bilinmiyor"),
                    "hafta": m.get("intRound", "1"),
                    "detay": m.get("strResult") or "Gol bilgisi bulunmuyor."
                })
            return maclar
        return []
    except Exception as e:
        print("Maç çekme hatası:", e)
        return []

# 2. DİNAMİK LİG PUAN DURUMU
def puan_durumunu_getir(lig_id):
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/lookuptable.php?l={lig_id}&s=2024-2025"
        yanit = requests.get(url, timeout=5)
        if yanit.status_code == 200:
            veri = yanit.json()
            tablo = []
            for t in veri.get("table", [])[:10]:
                tablo.append({
                    "sira": t.get("intRank"),
                    "takim": t.get("strTeam"),
                    "oynanan": t.get("intPlayed"),
                    "galibiyet": t.get("intWin"),
                    "beraberlik": t.get("intDraw"),
                    "maglubiyet": t.get("intLoss"),
                    "puan": int(t.get("intPoints", 0))
                })
            return tablo
        return []
    except Exception as e:
        print("Puan durumu hatası:", e)
        return []

# 3. YEDEKLİ HABER SERVİSİ
def haberleri_getir():
    yedek_haberler = [
        {"baslik": "🔥 Süper Lig'de Şampiyonluk Yarışı Kızışıyor", "link": "https://www.trtspor.com.tr/futbol"},
        {"baslik": "⚽ Avrupa Kupalarında Temsilcilerimizin Son Durumu", "link": "https://www.trtspor.com.tr/futbol"},
        {"baslik": "📈 Transfer Sezonunun Öne Çıkan Yıldız İsimleri", "link": "https://www.trtspor.com.tr/futbol"}
    ]
    try:
        url = "https://api.rss2json.com/v1/api.json?rss_url=https://www.trtspor.com.tr/futbol_rss.php"
        yanit = requests.get(url, timeout=4)
        if yanit.status_code == 200:
            items = yanit.json().get("items", [])
            if items:
                return [{"baslik": h.get("title"), "link": h.get("link")} for h in items[:8]]
    except Exception as e:
        print("Haber servisi hatası:", e)
    return yedek_haberler

@app.route("/", methods=["GET", "POST"])
def ana_sayfa():
    secili_lig_key = request.args.get("lig", "superlig")
    if secili_lig_key not in LIGLER:
        secili_lig_key = "superlig"
        
    aktif_lig = LIGLER[secili_lig_key]
    tum_maclar = gercek_maclari_getir(aktif_lig["id"])
    puan_tablosu = puan_durumunu_getir(aktif_lig["id"])
    haberler = haberleri_getir()

    # Takım Arama
    arama_metni = request.args.get("takim", "").strip().lower()
    if arama_metni:
        filtrelenmis_maclar = [
            m for m in tum_maclar 
            if arama_metni in m["ev"].lower() or arama_metni in m["deplasman"].lower()
        ]
    else:
        filtrelenmis_maclar = tum_maclar

    # Öne Çıkan Vitrin Maçı (Varsa ilk maç)
    vitrin_maci = tum_maclar[0] if tum_maclar else None

    return render_template(
        "index.html", 
        maclar=filtrelenmis_maclar, 
        tablo=puan_tablosu, 
        haberler=haberler,
        arama=arama_metni,
        ligler=LIGLER,
        secili_lig=secili_lig_key,
        aktif_lig_bilgi=aktif_lig,
        vitrin=vitrin_maci
    )

if __name__ == "__main__":
    app.run(debug=True)