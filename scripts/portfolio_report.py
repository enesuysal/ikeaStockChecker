import os
import requests
from datetime import datetime

# Config
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ROUTINE_TRIGGER_URL = os.environ["ROUTINE_TRIGGER_URL"]

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


def fire_routine(text):
    """Claude Code routine'i tetikle"""
    headers = {
        "Authorization": f"Bearer {ANTHROPIC_API_KEY}",
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "experimental-cc-routine-2026-04-01",
        "Content-Type": "application/json",
    }

    payload = {"text": text}

    response = requests.post(
        ROUTINE_TRIGGER_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )

    response.raise_for_status()


def main():
    print(f"[{datetime.now()}] Portföy analizi başlıyor...")

    try:
        print("Routine tetikleniyor...")
        fire_routine(PORTFOLIO_PROMPT)
        print("✅ Routine başarıyla tetiklendi!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Portföy raporu hatası: {str(e)}")
        return


if __name__ == "__main__":
    main()
