"""
EPIAS PTF (Piyasa Takas Fiyati) Multi-Year Fetcher
===================================================
EPIAS Seffaflik Platformu'ndan yil yil PTF verisi ceker.
Kullanici adi ve sifre her calistirmada kullanicidan istenir.

Kullanim:
    python ptf_fetcher.py

Gereksinimler:
    pip install "eptr2[allextras]"
"""

import getpass
import sys
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

try:
    from eptr2 import EPTR2
except ImportError:
    print("eptr2 kurulu degil. Kurmak icin:")
    print("  pip install \"eptr2[allextras]\"")
    sys.exit(1)

# ============================================
# AYARLAR
# ============================================
START_YEAR = 2021
END_YEAR = 2026


def get_credentials():
    """Kullanicidan EPIAS giris bilgilerini al."""
    print("\n--- EPIAS Giris Bilgileri ---")
    print("(EPIAS Seffaflik Platformu hesabiniz ile giris yapin)")
    print("Hesabiniz yoksa: https://seffaflik.epias.com.tr/\n")

    username = input("Kullanici adi (e-posta): ").strip()
    if not username:
        print("Kullanici adi bos olamaz!")
        sys.exit(1)

    password = getpass.getpass("Sifre: ")
    if not password:
        print("Sifre bos olamaz!")
        sys.exit(1)

    return username, password


def create_client(username, password):
    """EPTR2 istemcisini olustur ve baglantiyi test et."""
    print("\nEPIAS'a baglaniliyor...")
    try:
        eptr = EPTR2(username=username, password=password)
        print("Baglanti basarili!")
        return eptr
    except Exception as e:
        print(f"Baglanti hatasi: {e}")
        print("Kullanici adi ve sifrenizi kontrol edin.")
        sys.exit(1)


def fetch_ptf_by_year(eptr, start_year, end_year):
    """Yil yil PTF verisi ceker ve birlestirir."""
    all_data = []

    for year in range(start_year, end_year + 1):
        start_date = f"{year}-01-01"

        if year == end_year:
            end_date = datetime.now().strftime("%Y-%m-%d")
        else:
            end_date = f"{year}-12-31"

        print(f"\n{year} verisi cekiliyor: {start_date} -> {end_date}...")

        try:
            df = eptr.call("mcp", start_date=start_date, end_date=end_date)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"  {len(df)} satir cekildi")
            else:
                print(f"  {year} icin veri bos geldi!")
        except Exception as e:
            print(f"  {year} icin hata: {e}")

    if not all_data:
        print("\nHic veri cekilemedi!")
        return None

    combined = pd.concat(all_data, ignore_index=True)
    print(f"\nToplam: {len(combined)} satir ({start_year}-{end_year})")
    return combined


def process_and_save(df):
    """Veriyi temizle, analiz et, kaydet."""
    date_cols = [
        c
        for c in df.columns
        if "date" in c.lower() or "tarih" in c.lower() or "time" in c.lower()
    ]
    price_cols = [
        c
        for c in df.columns
        if "ptf" in c.lower()
        or "price" in c.lower()
        or "mcp" in c.lower()
        or "fiyat" in c.lower()
    ]

    print(f"\nKolonlar: {list(df.columns)}")
    print(f"Tarih kolonlari: {date_cols}")
    print(f"Fiyat kolonlari: {price_cols}")

    output_file = "ptf_multi_year.csv"
    df.to_csv(output_file, index=False)
    print(f"\nKaydedildi: {output_file}")

    print("\nTemel Istatistikler:")
    print(df.describe())

    return df


def plot_duck_curve(df):
    """Saatlik ortalama fiyat grafigi (duck curve pattern)."""
    print("\nDuck curve analizi icin veri:")
    print(f"Kolonlar: {list(df.columns)}")
    print(f"Boyut: {df.shape}")
    print("Ilk 5 satir:")
    print(df.head())


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("EPIAS PTF Multi-Year Fetcher")
    print("=" * 60)

    # 1. Kimlik dogrulama
    username, password = get_credentials()
    eptr = create_client(username, password)

    # 2. Veri cek
    df = fetch_ptf_by_year(eptr, START_YEAR, END_YEAR)

    if df is not None:
        # 3. Isle ve kaydet
        df = process_and_save(df)

        # 4. Analiz
        plot_duck_curve(df)

        print("\nTamamlandi! ptf_multi_year.csv dosyasini kontrol edin.")
    else:
        print("\nMevcut API metodlarini gormek icin:")
        print("  eptr = EPTR2(username='...', password='...')")
        print("  print(eptr.get_available_calls())")
        print("\nManuel indirme:")
        print(
            "  https://seffaflik.epias.com.tr/electricity/electricity-markets/"
            "day-ahead-market-gop/market-clearing-price-mcp"
        )
