# Ringkasan Dataset Pipeline Benchmark

Sumber: `benchmark/common.py`, `benchmark/{n_vs_k,n_vs_q,q_vs_k,lkh_vs_pyvrp_xmax_vs_q}.py`, `benchmark/README.md`.

## Ringkas

- Instance **tidak dibaca dari file `.vrp`**. Dibuat di memori oleh `make_data(n, k, q, seed=1)` di `benchmark/common.py`.
- Satu instance = depot di (0,0) + N customer acak, koordinat integer di [-100, 100]², demand 1..10, seed = 1.
- Ada **3 grid pasangan variabel** (N–K, N–Q, Q–K) dan **1 grid tambahan** (x_max–Q). Tiap grid **8 × 8 = 64 sel**, bukan 25. Satu sel = satu instance, dijalankan satu kali per solver.
- Metrik: **makespan** (waktu kendaraan paling lambat kembali ke depot). Output di `results/<nama>.csv` dan `plots/<nama>.png`.

## Nilai tiap parameter

| Parameter | Arti | 8 nilai | Nilai tetap saat tidak divariasikan |
|---|---|---|---|
| N | jumlah customer | 10, 20, 50, 100, 200, 400, 700, 1000 | 1000 |
| K | jumlah kendaraan | 1, 2, 3, 5, 10, 20, 50, 100 | 20 |
| Q | kapasitas kendaraan | 10, 20, 40, 80, 160, 320, 640, 1280 | 320 |
| x_max | ukuran grup maksimum (hanya grid ke-4) | 10, 15, 20, 30, 40, 50, 60, 80 | - |

Catatan: N maksimum 1000 karena PyVRP membangun n² edge. Q = 10 adalah kapasitas feasible terkecil karena demand maksimum 10.

## Empat grid

| Script | Sumbu x | Sumbu y | Parameter tetap | Sel | Solver dibandingkan | CSV |
|---|---|---|---|---|---|---|
| `n_vs_k.py` | N | K | Q = 320 | 64 | held, lkh, pyvrp | `results/n_vs_k.csv` |
| `n_vs_q.py` | N | Q | K = 20 | 64 | held, lkh, pyvrp | `results/n_vs_q.csv` |
| `q_vs_k.py` | Q | K | N = 1000 | 64 | held, lkh, pyvrp | `results/q_vs_k.csv` |
| `lkh_vs_pyvrp_xmax_vs_q.py` | x_max | Q | N = 1000, K = 20 | 64 | lkh, pyvrp | `results/lkh_vs_pyvrp_xmax_vs_q.csv` |

Di grid ke-4, PyVRP tidak bergantung pada x_max sehingga hanya dijalankan sekali per Q (8 kali), hasilnya diulang di tiap baris Q yang sama.

## Cara instance dibangkitkan

`make_data(n, k, q, seed=1)` memakai `random_customers(n, coord_range=(-100, 100), demand_range=(1, 10), seed=1)`.

- Sel dengan N yang sama memakai customer dan demand yang identik. Hanya K atau Q yang berbeda.
- Antar N berbeda, titik tidak dijamin bersarang (demand digambar setelah koordinat, jadi urutan acak bergeser).
- Satu instance (satu seed) per sel. Perbedaan beberapa persen antar sel bertetangga bisa berupa noise.

## Solver di tiap sel

| Nama | Metode | x_max |
|---|---|---|
| `held` | `dsu_bsta`: DSU grouping, TSP eksak Held-Karp per grup, BSTA untuk membagi tour ke kendaraan | 10 |
| `lkh` | `dsu_bsta` dengan Lin-Kernighan (`tsp_lk`) per grup | 40 (grid ke-4: 10..80) |
| `pyvrp` | PyVRP (HGS), tanpa batas waktu, berhenti setelah 20000 iterasi tanpa best baru | - |

## Kolom CSV

- Tiga grid pertama: `x`, `y`, lalu `held_makespan`, `held_seconds`, `lkh_makespan`, `lkh_seconds`, `pyvrp_makespan`, `pyvrp_seconds`. `nan` berarti solver gagal atau tidak menemukan solusi.
- Grid ke-4: `x_max`, `q`, `lkh_makespan`, `lkh_seconds`, `pyvrp_makespan`, `pyvrp_seconds`.

## Hal yang perlu diingat saat membaca hasil

- **Objektif berbeda.** PyVRP meminimalkan total jarak semua tour, kita meminimalkan makespan. Selisih negatif sebagian berasal dari perbedaan objektif ini. Dengan K = 1 keduanya sama.
- **held vs lkh berbeda dua hal sekaligus** (metode TSP dan x_max 10 vs 40), jadi selisihnya tidak bisa dikaitkan ke satu penyebab.
- **Waktu PyVRP tidak tetap**, naik bersama N, jadi speedup terhadap PyVRP jauh lebih besar untuk N besar.
- **K besar atau N kecil**: jumlah tour lebih sedikit dari kendaraan, makespan = tour terpanjang, solver hampir seri.
- **x_max membatasi ukuran grup** walau Q mengizinkan lebih besar, jadi pada Q besar baris-baris grid terlihat mirip.
- **File lama.** Beberapa file di `results/` (`held_*`, `lkh_*`, `n_vs_k.csv`, dll.) berasal dari versi sebelumnya, misalnya PyVRP dibatasi 5 detik. Skrip saat ini tidak membacanya.

## Dataset file-based di `data/` (versi sebelumnya)

`spec.py` masih mendeklarasikan grid berbasis file `.vrp`: N ∈ {10, 30, 100, 300, 1000} × K ∈ {2, 3, 5, 10, 20} = **25 file** (`instance-n{N}-k{K}.vrp`, seed 1, kapasitas default 2 × demand maksimum = 20), ditambah sweep kapasitas `n1000-k20-q*` (Q = 10 s/d 10240). Ini kemungkinan sumber angka "25" yang kamu ingat. Grid 8 × 8 di atas menggantikannya.

## Dataset poster (terpisah)

`data/poster-n8-k2.vrp`: N = 8, K = 2, Q = 10, hanya untuk gambar poster (`poster_viz.py`), tidak masuk benchmark. Hasil: 4 grup, waktu tour 254 / 223 / 222 / 190, T\* = 445.
