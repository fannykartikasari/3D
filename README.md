# Dashboard Gambut Indonesia
Isi: `app.py`, `requirements.txt`, dan `Data_Gambut_dan_Restorasi_per_Provinsi.xlsx`.

Jalankan:
1. Python 3.10+
2. `pip install -r requirements.txt`
3. `streamlit run app.py`

Dashboard mengagregasi data dari workbook sumber:
- Luas gambut dan jumlah KHG dari `KHGN 2017`
- Jumlah APTMAT dari `APTMA_Tiap_KHG_20240205`
- Catatan revitalisasi, infrastruktur, demplot, DMPG 2022 dan DMPG 2023 dari sheet masing-masing
- Workbook output juga menyertakan sheet sumber dan `Definisi Data`

Catatan: agregasi kegiatan adalah jumlah catatan, bukan otomatis jumlah lokasi unik. Peta mengambil GeoJSON dari repositori publik saat aplikasi berjalan, sehingga perlu internet. Validasi nama provinsi dan angka sebelum publikasi.
