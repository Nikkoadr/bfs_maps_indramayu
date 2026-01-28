# Sistem Pencarian Rute Terpendek dengan Obstacle

## Deskripsi

Aplikasi web ini adalah alat visualisasi untuk mencari rute terpendek antara dua titik pada peta, dengan kemampuan untuk menambahkan rintangan (obstacles) dinamis. Aplikasi ini menggunakan Flask sebagai backend untuk kalkulasi graf dan Leaflet.js untuk tampilan peta interaktif di frontend.

## Fitur

- **Pemilihan Titik Awal dan Akhir:** Klik pada peta untuk menentukan lokasi awal dan tujuan.
- **Gambar Rintangan:** Gambar poligon di atas peta untuk mendefinisikan area yang tidak dapat dilalui.
- **Algoritma Dijkstra:** Menggunakan algoritma Dijkstra untuk menemukan jalur terpendek, dengan mempertimbangkan rintangan yang ada.
- **Visualisasi Animasi:** Menampilkan proses pencarian algoritma (sebaran eksplorasi) secara visual sebelum menunjukkan rute final.

## Teknologi

- **Backend:** Python, Flask, OSMnx, NetworkX, Shapely
- **Frontend:** HTML, CSS, JavaScript, Leaflet.js, Leaflet-draw
- **Data:** OpenStreetMap

## Instalasi & Menjalankan di Lokal

Pastikan Anda memiliki Python 3 terinstal di sistem Anda.

1.  **Clone atau Unduh Repositori**

    ```bash
    git clone <URL_REPOSITORI_ANDA>
    cd <NAMA_FOLDER_PROYEK>
    ```

2.  **Buat dan Aktifkan Virtual Environment**

    Sangat disarankan untuk menggunakan lingkungan virtual (virtual environment) untuk mengisolasi dependensi proyek.

    ```bash
    # Buat virtual environment
    python -m venv .venv

    # Aktifkan di macOS/Linux
    source .venv/bin/activate

    # Aktifkan di Windows
    .venv\Scripts\activate
    ```

3.  **Install Dependensi**

    Install semua pustaka Python yang dibutuhkan yang tercantum dalam `requirements.txt`.

    ```bash
    pip install -r requirements.txt
    ```

4.  **Jalankan Aplikasi**

    Setelah dependensi terinstal, jalankan server Flask:

    ```bash
    python app.py
    ```

5.  **Buka di Browser**

    Buka browser web Anda dan kunjungi `http://127.0.0.1:8080` atau `http://localhost:8080`.

    **Catatan Penting:** Saat Anda pertama kali menjalankan pencarian rute, aplikasi akan mengunduh data peta untuk wilayah Indramayu dan menyimpannya dalam file `indramayu_graph.pkl`. Proses ini mungkin **memakan waktu beberapa menit** dan membutuhkan koneksi internet. Harap bersabar. Pencarian rute selanjutnya akan berjalan jauh lebih cepat karena menggunakan data yang sudah di-cache.
