"""
============================================================
  PTF (Market Clearing Price) Analysis & Forecasting
  KocSistem Renewable Energy Solutions - Internship Project
  Basak Zeynep Okumusoglu - IE400
============================================================

Kullanim:
    python ptf_fetcher.py

Gereksinimler:
    pip install -r requirements.txt
"""

import getpass
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings

warnings.filterwarnings("ignore")

# ============================================================
# Dependency checks
# ============================================================
try:
    from eptr2 import EPTR2
except ImportError:
    print("eptr2 kurulu degil. Kurmak icin:")
    print('  pip install "eptr2[allextras]"')
    sys.exit(1)

try:
    from prophet import Prophet
except ImportError:
    print("prophet kurulu degil. Kurmak icin:")
    print("  pip install prophet")
    sys.exit(1)

from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

# ============================================================
# AYARLAR
# ============================================================
START_YEAR = 2021
END_YEAR = 2026
TODAY = datetime.now().strftime("%Y-%m-%d")

# Gorsel tema
COLORS = [
    "#2563EB",  # blue
    "#DC2626",  # red
    "#059669",  # green
    "#D97706",  # amber
    "#7C3AED",  # violet
    "#DB2777",  # pink
]
SEASON_COLORS = {
    "Kis (Ara-Sub)": "#3B82F6",
    "Ilkbahar (Mar-May)": "#22C55E",
    "Yaz (Haz-Agu)": "#EF4444",
    "Sonbahar (Eyl-Kas)": "#F59E0B",
}


def setup_plot_style():
    """Matplotlib icin profesyonel tema ayarla."""
    plt.rcParams.update(
        {
            "figure.facecolor": "#FAFAFA",
            "axes.facecolor": "#FAFAFA",
            "axes.edgecolor": "#D1D5DB",
            "axes.labelcolor": "#1F2937",
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 12,
            "axes.grid": True,
            "grid.color": "#E5E7EB",
            "grid.alpha": 0.7,
            "grid.linewidth": 0.6,
            "xtick.color": "#6B7280",
            "ytick.color": "#6B7280",
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "legend.framealpha": 0.9,
            "legend.edgecolor": "#D1D5DB",
            "font.family": "sans-serif",
            "figure.dpi": 120,
            "savefig.dpi": 200,
            "savefig.bbox": "tight",
            "savefig.facecolor": "#FAFAFA",
        }
    )


def print_header(title, char="=", width=62):
    """Baslik yazdir."""
    print()
    print(char * width)
    print(f"  {title}")
    print(char * width)


def print_step(step_num, title):
    """Adim basligini yazdir."""
    print_header(f"STEP {step_num}: {title}")


# ============================================================
# 1. KIMLIK DOGRULAMA
# ============================================================
def get_credentials():
    """Kullanicidan EPIAS giris bilgilerini al."""
    print_header("EPIAS Giris Bilgileri", char="-")
    print("  EPIAS Seffaflik Platformu hesabinizla giris yapin.")
    print("  Hesabiniz yoksa: https://seffaflik.epias.com.tr/")
    print()

    username = input("  Kullanici adi (e-posta): ").strip()
    if not username:
        print("\n  [HATA] Kullanici adi bos olamaz!")
        sys.exit(1)

    password = getpass.getpass("  Sifre: ")
    if not password:
        print("\n  [HATA] Sifre bos olamaz!")
        sys.exit(1)

    return username, password


def create_client(username, password):
    """EPTR2 istemcisini olustur."""
    print("\n  EPIAS'a baglaniliyor...", end=" ")
    try:
        eptr = EPTR2(username=username, password=password)
        print("OK")
        return eptr
    except Exception as e:
        print(f"HATA\n  {e}")
        print("  Kullanici adi ve sifrenizi kontrol edin.")
        sys.exit(1)


# ============================================================
# 2. VERI CEKME
# ============================================================
def fetch_ptf_data(eptr, start_year, end_year):
    """Yil yil PTF verisi ceker ve birlestirir."""
    all_data = []

    for year in range(start_year, end_year + 1):
        start_date = f"{year}-01-01"
        end_date = TODAY if year == end_year else f"{year}-12-31"

        print(f"  {year}:  {start_date}  ->  {end_date}  ...", end=" ")

        try:
            df = eptr.call("mcp", start_date=start_date, end_date=end_date)
            if df is not None and len(df) > 0:
                all_data.append(df)
                print(f"{len(df):>6,} satir")
            else:
                print("bos")
        except Exception as e:
            print(f"HATA ({e})")

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)
    print(f"\n  Toplam: {len(combined):,} satir")
    return combined


def prepare_dataframe(ptf):
    """Ham veriyi analiz icin hazirla."""
    ptf["datetime"] = pd.to_datetime(ptf["date"])
    ptf["hour_int"] = ptf["datetime"].dt.hour
    ptf["year"] = ptf["datetime"].dt.year
    ptf["month"] = ptf["datetime"].dt.month
    ptf["day_of_week"] = ptf["datetime"].dt.dayofweek
    ptf["is_weekend"] = ptf["day_of_week"].isin([5, 6])

    ptf.to_csv("ptf_2021_2026.csv", index=False)
    print(f"  Kaydedildi: ptf_2021_2026.csv")
    return ptf


# ============================================================
# 3. DUCK CURVE ANALIZI
# ============================================================
def plot_duck_curve_by_year(ptf):
    """Yillik duck curve karsilastirmasi."""
    fig, ax = plt.subplots(figsize=(13, 6))

    years = sorted(ptf["year"].unique())
    for i, year in enumerate(years):
        yearly = ptf[ptf["year"] == year].groupby("hour_int")["price"].mean()
        color = COLORS[i % len(COLORS)]
        linewidth = 2.5 if year == years[-1] else 1.6
        alpha = 1.0 if year == years[-1] else 0.7
        ax.plot(
            yearly.index,
            yearly.values,
            label=str(year),
            color=color,
            linewidth=linewidth,
            alpha=alpha,
            marker="o",
            markersize=3,
        )

    ax.set_xlabel("Saat")
    ax.set_ylabel("PTF (TL/MWh)")
    ax.set_title("Duck Curve - Yillik Ortalama Saatlik PTF (2021-2026)")
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(title="Yil", loc="upper left")
    plt.tight_layout()
    plt.savefig("duck_curve_by_year.png")
    plt.close()
    print("  Kaydedildi: duck_curve_by_year.png")


def plot_duck_curve_seasonal(ptf, year=2025):
    """Mevsimsel duck curve analizi."""
    data_year = ptf[ptf["year"] == year]
    if data_year.empty:
        print(f"  {year} verisi bulunamadi, mevsimsel grafik atlanıyor.")
        return

    seasons = {
        "Kis (Ara-Sub)": [12, 1, 2],
        "Ilkbahar (Mar-May)": [3, 4, 5],
        "Yaz (Haz-Agu)": [6, 7, 8],
        "Sonbahar (Eyl-Kas)": [9, 10, 11],
    }

    fig, ax = plt.subplots(figsize=(13, 6))
    for name, months in seasons.items():
        seasonal = (
            data_year[data_year["month"].isin(months)]
            .groupby("hour_int")["price"]
            .mean()
        )
        if not seasonal.empty:
            ax.plot(
                seasonal.index,
                seasonal.values,
                label=name,
                color=SEASON_COLORS[name],
                linewidth=2.2,
                marker="o",
                markersize=3,
            )

    ax.set_xlabel("Saat")
    ax.set_ylabel("PTF (TL/MWh)")
    ax.set_title(f"Mevsimsel Duck Curve - {year} Saatlik PTF")
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(title="Mevsim")
    plt.tight_layout()
    plt.savefig("duck_curve_seasonal.png")
    plt.close()
    print("  Kaydedildi: duck_curve_seasonal.png")


def plot_weekday_vs_weekend(ptf, year=2025):
    """Hafta ici vs hafta sonu duck curve."""
    data_year = ptf[ptf["year"] == year]
    if data_year.empty:
        return

    fig, ax = plt.subplots(figsize=(13, 6))

    weekday = (
        data_year[~data_year["is_weekend"]].groupby("hour_int")["price"].mean()
    )
    weekend = (
        data_year[data_year["is_weekend"]].groupby("hour_int")["price"].mean()
    )

    ax.plot(
        weekday.index, weekday.values,
        label="Hafta Ici", color="#2563EB", linewidth=2.2, marker="o", markersize=3,
    )
    ax.plot(
        weekend.index, weekend.values,
        label="Hafta Sonu", color="#DC2626", linewidth=2.2, marker="s", markersize=3,
    )
    ax.fill_between(
        weekday.index,
        weekday.values,
        weekend.values,
        alpha=0.08,
        color="#6B7280",
    )

    ax.set_xlabel("Saat")
    ax.set_ylabel("PTF (TL/MWh)")
    ax.set_title(f"Hafta Ici vs Hafta Sonu - {year} Saatlik PTF")
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend()
    plt.tight_layout()
    plt.savefig("duck_curve_weekday_weekend.png")
    plt.close()
    print("  Kaydedildi: duck_curve_weekday_weekend.png")


def print_arbitrage_analysis(ptf, year=2025):
    """Arbitraj firsati analizi."""
    data = ptf[ptf["year"] == year]
    if data.empty:
        print(f"  {year} verisi yok, arbitraj analizi atlanıyor.")
        return

    hourly = data.groupby("hour_int")["price"].mean()
    midday = hourly.loc[11:14].mean()
    evening = hourly.loc[17:21].mean()
    night = hourly.loc[2:5].mean()
    morning_peak = hourly.loc[8:10].mean()
    spread = evening - midday

    print(f"\n  Duck Curve Arbitraj Analizi ({year}):")
    print(f"  {'':4}{'Zaman Dilimi':<25} {'Ort. PTF':>12}")
    print(f"  {'':4}{'-'*37}")
    print(f"  {'':4}{'Gece (02-05h)':<25} {night:>10,.0f} TL")
    print(f"  {'':4}{'Sabah peak (08-10h)':<25} {morning_peak:>10,.0f} TL")
    print(f"  {'':4}{'Gunduz / solar (11-14h)':<25} {midday:>10,.0f} TL")
    print(f"  {'':4}{'Aksam peak (17-21h)':<25} {evening:>10,.0f} TL")
    print(f"  {'':4}{'-'*37}")
    print(f"  {'':4}{'Arbitraj (aksam-gunduz)':<25} {spread:>10,.0f} TL")
    if evening > 0:
        print(f"  {'':4}{'Gunduz indirimi':<25} {(1-midday/evening)*100:>9.1f}%")


# ============================================================
# 4. ISTATISTIKLER
# ============================================================
def print_statistics(ptf):
    """Yillik temel istatistikleri yazdir."""
    stats = ptf.groupby("year")["price"].agg(["mean", "std", "min", "max", "count"])
    stats.columns = ["Ortalama", "Std Sapma", "Min", "Max", "Gozlem"]
    stats.index.name = "Yil"

    print(f"\n  Yillik PTF Istatistikleri (TL/MWh):")
    print()

    header = f"  {'Yil':>6} {'Ortalama':>10} {'Std':>10} {'Min':>10} {'Max':>10} {'Gozlem':>8}"
    print(header)
    print(f"  {'-'*54}")

    for year, row in stats.iterrows():
        print(
            f"  {year:>6} {row['Ortalama']:>10,.1f} {row['Std Sapma']:>10,.1f}"
            f" {row['Min']:>10,.1f} {row['Max']:>10,.1f} {row['Gozlem']:>8,.0f}"
        )

    print(f"  {'-'*54}")
    total = ptf["price"]
    print(
        f"  {'TOPLAM':>6} {total.mean():>10,.1f} {total.std():>10,.1f}"
        f" {total.min():>10,.1f} {total.max():>10,.1f} {len(total):>8,}"
    )

    date_min = ptf["datetime"].min().strftime("%Y-%m-%d")
    date_max = ptf["datetime"].max().strftime("%Y-%m-%d")
    print(f"\n  Tarih araligi: {date_min}  ->  {date_max}")


def plot_monthly_heatmap(ptf):
    """Aylik ortalama PTF isı haritasi."""
    pivot = ptf.pivot_table(
        values="price", index="month", columns="year", aggfunc="mean"
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns.astype(int))
    months_tr = [
        "Oca", "Sub", "Mar", "Nis", "May", "Haz",
        "Tem", "Agu", "Eyl", "Eki", "Kas", "Ara",
    ]
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([months_tr[m - 1] for m in pivot.index])

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                text_color = "white" if val > pivot.values[~np.isnan(pivot.values)].mean() else "black"
                ax.text(j, i, f"{val:,.0f}", ha="center", va="center", fontsize=8, color=text_color)

    ax.set_title("Aylik Ortalama PTF Isi Haritasi (TL/MWh)")
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("TL/MWh")
    plt.tight_layout()
    plt.savefig("ptf_monthly_heatmap.png")
    plt.close()
    print("  Kaydedildi: ptf_monthly_heatmap.png")


# ============================================================
# 5. PROPHET TAHMINLEME
# ============================================================
def run_prophet_forecast(ptf):
    """Prophet ile PTF tahmini yap."""
    df_prophet = ptf[["datetime", "price"]].copy()
    df_prophet.columns = ["ds", "y"]
    df_prophet["ds"] = df_prophet["ds"].dt.tz_localize(None)

    # Train/Test split (%80 / %20)
    split_idx = int(len(df_prophet) * 0.8)
    train = df_prophet.iloc[:split_idx]
    test = df_prophet.iloc[split_idx:]

    print(f"  Train:  {len(train):>7,} satir  ({train['ds'].min().date()} -> {train['ds'].max().date()})")
    print(f"  Test:   {len(test):>7,} satir  ({test['ds'].min().date()} -> {test['ds'].max().date()})")

    # Model egitimi
    print("\n  Prophet modeli egitiliyor (birkaç dakika surebilir)...", end=" ", flush=True)
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=True,
    )
    model.fit(train)
    print("OK")

    # Tahmin
    future = model.make_future_dataframe(periods=len(test), freq="h")
    forecast = model.predict(future)

    # Metrikler
    pred = forecast.tail(len(test))["yhat"].values
    actual = test["y"].values

    mae = mean_absolute_error(actual, pred)
    mape = mean_absolute_percentage_error(actual, pred)
    rmse = np.sqrt(np.mean((actual - pred) ** 2))

    print(f"\n  Tahmin Performansi:")
    print(f"  {'':4}MAE:   {mae:>10,.2f} TL/MWh")
    print(f"  {'':4}RMSE:  {rmse:>10,.2f} TL/MWh")
    print(f"  {'':4}MAPE:  {mape:>9.2%}")

    return model, forecast, train, test, {"mae": mae, "rmse": rmse, "mape": mape}


def plot_prophet_components(model, forecast):
    """Prophet bilesenleri (trend, seasonality)."""
    fig = model.plot_components(forecast)
    fig.set_size_inches(13, 10)
    fig.patch.set_facecolor("#FAFAFA")
    plt.savefig("prophet_components.png")
    plt.close()
    print("  Kaydedildi: prophet_components.png")


def plot_actual_vs_predicted(test, forecast, days=14):
    """Gercek vs tahmin karsilastirmasi."""
    n_points = 24 * days
    last_test = test.tail(n_points).copy()
    last_pred = forecast.tail(len(test)).tail(n_points)

    fig, ax = plt.subplots(figsize=(14, 5))

    ax.plot(
        last_test["ds"].values, last_test["y"].values,
        label="Gercek", color="#2563EB", alpha=0.8, linewidth=1.0,
    )
    ax.plot(
        last_pred["ds"].values, last_pred["yhat"].values,
        label="Tahmin", color="#DC2626", alpha=0.8, linewidth=1.0,
    )
    ax.fill_between(
        last_pred["ds"].values,
        last_pred["yhat_lower"].values,
        last_pred["yhat_upper"].values,
        alpha=0.12,
        color="#DC2626",
        label="Guven araligi",
    )

    ax.set_xlabel("Tarih")
    ax.set_ylabel("PTF (TL/MWh)")
    ax.set_title(f"Prophet Tahmini vs Gercek - Son {days} Gun")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend()
    plt.tight_layout()
    plt.savefig("prophet_actual_vs_predicted.png")
    plt.close()
    print("  Kaydedildi: prophet_actual_vs_predicted.png")


def plot_future_forecast(model, test, days=30):
    """Gelecek tahmini grafigi."""
    future = model.make_future_dataframe(periods=len(test) + 24 * days, freq="h")
    forecast = model.predict(future)
    future_only = forecast.tail(24 * days)

    fig, ax = plt.subplots(figsize=(14, 5))

    ax.plot(
        future_only["ds"].values, future_only["yhat"].values,
        label="Tahmin", color="#D97706", linewidth=1.5,
    )
    ax.fill_between(
        future_only["ds"].values,
        future_only["yhat_lower"].values,
        future_only["yhat_upper"].values,
        alpha=0.15,
        color="#D97706",
        label="Guven araligi",
    )

    ax.set_xlabel("Tarih")
    ax.set_ylabel("PTF (TL/MWh)")
    ax.set_title(f"{days} Gunluk PTF Tahmini (Prophet)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend()
    plt.tight_layout()
    plt.savefig("prophet_30day_forecast.png")
    plt.close()
    print("  Kaydedildi: prophet_30day_forecast.png")


# ============================================================
# 6. OZET RAPOR
# ============================================================
def print_summary(ptf, metrics, arbitrage_year=2025):
    """Sonuc ozeti yazdir."""
    data = ptf[ptf["year"] == arbitrage_year]
    hourly = data.groupby("hour_int")["price"].mean() if not data.empty else None

    if hourly is not None and len(hourly) > 0:
        midday = hourly.loc[11:14].mean()
        evening = hourly.loc[17:21].mean()
        spread = evening - midday
    else:
        midday = evening = spread = 0

    date_min = ptf["datetime"].min().strftime("%Y-%m-%d")
    date_max = ptf["datetime"].max().strftime("%Y-%m-%d")

    print(f"""
  Veri:
    {len(ptf):,} saatlik PTF gozlemi
    {date_min}  ->  {date_max}
    Kaynak: EPIAS Seffaflik Platformu (eptr2)

  Duck Curve ({arbitrage_year}):
    Gunduz ort (11-14h):   {midday:>10,.0f} TL/MWh
    Aksam ort  (17-21h):   {evening:>10,.0f} TL/MWh
    Arbitraj farki:        {spread:>10,.0f} TL/MWh

  Prophet Modeli:
    MAE:   {metrics['mae']:>10,.2f} TL/MWh
    RMSE:  {metrics['rmse']:>10,.2f} TL/MWh
    MAPE:  {metrics['mape']:>9.2%}

  Olusturulan Dosyalar:
    ptf_2021_2026.csv                - Ham veri
    duck_curve_by_year.png           - Yillik duck curve
    duck_curve_seasonal.png          - Mevsimsel duck curve
    duck_curve_weekday_weekend.png   - Hafta ici / sonu duck curve
    ptf_monthly_heatmap.png          - Aylik PTF isi haritasi
    prophet_components.png           - Prophet mevsimsellik bilesenleri
    prophet_actual_vs_predicted.png  - Tahmin dogruluk grafigi
    prophet_30day_forecast.png       - 30 gunluk gelecek tahmini""")


# ============================================================
# MAIN
# ============================================================
def main():
    setup_plot_style()

    print_header(
        "PTF Analysis & Forecasting\n"
        "  KocSistem Renewable Energy Solutions\n"
        "  Basak Zeynep Okumusoglu - IE400"
    )

    # 1. Kimlik dogrulama
    username, password = get_credentials()
    eptr = create_client(username, password)

    # 2. Veri cekme
    print_step(1, "EPIAS'tan PTF Verisi Cekme")
    ptf = fetch_ptf_data(eptr, START_YEAR, END_YEAR)
    if ptf is None:
        print("\n  Hic veri cekilemedi. Cikis yapiliyor.")
        print("  Mevcut endpointleri gormek icin:")
        print("    eptr.get_available_calls()")
        sys.exit(1)

    ptf = prepare_dataframe(ptf)

    # 3. Duck curve analizi
    print_step(2, "Duck Curve Analizi")
    plot_duck_curve_by_year(ptf)
    plot_duck_curve_seasonal(ptf, year=2025)
    plot_weekday_vs_weekend(ptf, year=2025)
    print_arbitrage_analysis(ptf, year=2025)

    # 4. Istatistikler
    print_step(3, "Temel Istatistikler")
    print_statistics(ptf)
    plot_monthly_heatmap(ptf)

    # 5. Prophet tahminleme
    print_step(4, "Prophet Tahminleme")
    model, forecast, train, test, metrics = run_prophet_forecast(ptf)
    plot_prophet_components(model, forecast)
    plot_actual_vs_predicted(test, forecast, days=14)
    plot_future_forecast(model, test, days=30)

    # 6. Ozet
    print_step(5, "OZET")
    print_summary(ptf, metrics)

    print("\n  Tamamlandi!")
    print()


if __name__ == "__main__":
    main()
