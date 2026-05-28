import os
import requests
from datetime import datetime

# Config
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ROUTINE_TRIGGER_URL = os.environ.get("ROUTINE_TRIGGER_URL", "")

PORTFOLIO_PROMPT = """
Aşağıdaki portföyü analiz et ve Telegram için kısa özet rapor hazırla.

## PORTFÖY

### WIO Securities (USD)
| Hisse | Adet |
|-------|------|
| AMZN  | 9.00 |
| NVDA  | 5.88 |
| AAPL  | 3.87 |
| GOOGL | 1.53 |
| CVX   | 2.41 |
| GLD   | 1.67 |
| RDDT  | 1.18 |
| DVN   | 3.57 |

Bekleyen Emir: MSFT yarısını $460'ta sat (limit order aktif)

### Revolut (EUR)
| Hisse | Adet  |
|-------|-------|
| AAPL  | 3.84  |
| AMZN  | 1.00  |
| VUAA  | 1.90  |
| DVN   | 3.26  |
| MSFT  | 0.13  |
| MDLN  | 1.05  |
| XAG   | 8.40  |

### Kuveyt Türk — Altın DCA Planı
- Toplam hedef: $25,000
- Sonraki dilim: €7,400 — Haziran 2026
- İdeal alım: €3,750/oz altı

## YAPILACAKLAR
1. Web search ile güncel fiyatları çek (Yahoo Finance)
2. Her hisse için günlük değişim hesapla
3. Toplam portföy değeri ve günlük P&L
4. Her hisse için TUT/AL/İZLE/SAT kararı
5. MSFT $460 limit takibi
6. Altın DCA fırsatı var mı?

## ÇIKTI FORMAT (Telegram Markdown)
Şu formatta yaz, başka hiçbir şey ekleme:

📊 *GÜNLÜK PORTFÖY RAPORU*
🗓 {tarih}

💼 *TOPLAM*
Wio: ~${wio_toplam}
Revolut: ~€{revolut_toplam}

📈 *PERFORMANS*
En iyi: {hisse} +{%}
En kötü: {hisse} -{%}
Günlük P&L: {tutar}

📌 *AKSİYONLAR*
{hisse}: {TUT/AL/İZLE/SAT} — {1 satır neden}
[tüm hisseler]

🎯 *MSFT LİMİT*
${fiyat} → $460 hedef (%{fark} kaldı)

🥇 *ALTIN DCA*
€{fiyat}/oz — Alım fırsatı: {Evet/Hayır}

⚡ *BUGÜN AKSİYON*
{evet/hayır ve neden}

_Bilgi amaçlıdır, yatırım tavsiyesi değildir._
"""


def call_claude_api(prompt):
    """Claude API'ye direkt istek at"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "tools": [
            {
                "type": "web_search_20250305",
                "name": "web_search",
            }
        ],
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()
    data = response.json()

    # Tüm text bloklarını birleştir
    result = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            result += block.get("text", "")

    return result.strip()


def send_telegram(message):
    """Telegram'a mesaj gönder"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def trigger_routine_if_configured():
    """Opsiyonel routine trigger çağrısı"""
    if not ROUTINE_TRIGGER_URL:
        return

    try:
        response = requests.post(ROUTINE_TRIGGER_URL, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(
            f"Routine trigger çağrısı başarısız oldu: {exc}"
        ) from exc


def main():
    print(f"[{datetime.now()}] Portföy analizi başlıyor...")

    try:
        # Claude API'yi çağır
        print("Claude API'ye istek gönderiliyor...")
        analysis = call_claude_api(PORTFOLIO_PROMPT)

        if not analysis:
            raise ValueError("Claude'dan boş yanıt geldi")

        print("Analiz tamamlandı, Telegram'a gönderiliyor...")

        # Telegram'a gönder
        send_telegram(analysis)

        # Opsiyonel routine trigger
        trigger_routine_if_configured()

        print("✅ Telegram'a başarıyla gönderildi!")

    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Portföy raporu hatası: {str(e)}"
        print(error_msg)
        try:
            send_telegram(error_msg)
        except requests.exceptions.RequestException:
            pass
        return


if __name__ == "__main__":
    main()
