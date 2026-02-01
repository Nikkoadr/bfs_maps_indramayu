# IMPORT LIBRARY

import os                  # Untuk operasi file & path (cek file ada/tidak)
import pickle              # Untuk menyimpan & memuat objek Python (graph) ke file
from flask import Flask, request, jsonify, send_from_directory

import osmnx as ox         # Library untuk mengambil & memproses data OpenStreetMap
import networkx as nx      # Library graph & algoritma (Dijkstra)
from shapely.geometry import Point, Polygon
                            # Untuk operasi geometri (cek node di dalam polygon)

# KONFIGURASI FLASK

# static_folder='src' artinya:
# Flask akan mencari file statis (HTML, JS, CSS) di folder "src"
app = Flask(__name__, static_folder='src')

# Nama file cache graph OSM agar tidak download ulang setiap run
GRAPH_FILE = "indramayu_graph.pkl"

# Variabel global untuk menyimpan graph di memory
G_base = None


# LOAD ATAU BUAT GRAPH

def load_or_create_graph():
    """
    Fungsi ini:
    - Mengambil graph dari memory jika sudah ada
    - Jika belum, cek file pickle
    - Jika file tidak ada, download dari OpenStreetMap
    """

    global G_base

    # Jika graph sudah ada di memory, langsung pakai
    if G_base is not None:
        return G_base

    # Jika file pickle sudah ada, load dari file
    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE, "rb") as f:
            G_base = pickle.load(f)
        return G_base

    # Jika belum ada sama sekali, download graph dari OSM
    G_new = ox.graph_from_place(
        "Indramayu, West Java, Indonesia",
        network_type='drive',   # Graph jalan mobil
        simplify=True           # Sederhanakan node & edge
    )

    # Simpan graph ke file pickle
    with open(GRAPH_FILE, "wb") as f:
        pickle.dump(G_new, f, pickle.HIGHEST_PROTOCOL)

    # Simpan ke memory agar tidak reload lagi
    G_base = G_new
    return G_base


# ROUTE ROOT (/)

@app.route('/')
def index():
    """
    Endpoint root:
    - Mengirim file index.html dari folder src
    """
    return send_from_directory('src', 'index.html')


# API HITUNG RUTE

@app.route('/api/route', methods=['POST'])
def get_route():
    """
    Endpoint POST untuk menghitung rute terpendek
    dengan obstacle (polygon) opsional
    """

    # Ambil data JSON dari request
    data = request.get_json()

    # Ambil koordinat start & end
    start_lat = data.get('start_lat')
    start_lon = data.get('start_lon')
    end_lat   = data.get('end_lat')
    end_lon   = data.get('end_lon')

    # Ambil daftar obstacle (GeoJSON polygon)
    obstacles_geojson = data.get('obstacles', [])

    try:
        # Load graph utama
        G = load_or_create_graph()

        # Copy graph supaya graph asli tidak rusak
        G_modified = G.copy()

        # HAPUS NODE DALAM OBSTACLE

        nodes_to_remove = set()

        if obstacles_geojson:
            for obs_geojson in obstacles_geojson:

                # Ambil koordinat polygon GeoJSON
                coords = [
                    tuple(p)
                    for p in obs_geojson['geometry']['coordinates'][0]
                ]

                # Buat polygon Shapely
                polygon = Polygon(coords)

                # Loop semua node pada graph
                for node, data_node in G_modified.nodes(data=True):

                    # data_node['x'] = longitude
                    # data_node['y'] = latitude
                    point = Point(data_node['x'], data_node['y'])

                    # Jika node berada di dalam polygon
                    if polygon.contains(point):
                        nodes_to_remove.add(node)

            # Hapus semua node yang masuk obstacle
            if nodes_to_remove:
                G_modified.remove_nodes_from(list(nodes_to_remove))

        # CARI NODE TERDEKAT

        # Cari node terdekat dari koordinat start
        start_node = ox.distance.nearest_nodes(
            G_modified, start_lon, start_lat
        )

        # Cari node terdekat dari koordinat end
        end_node = ox.distance.nearest_nodes(
            G_modified, end_lon, end_lat
        )

        # DIJKSTRA

        # distances : jarak terpendek dari start ke semua node
        # paths     : jalur ke setiap node
        distances, paths = nx.single_source_dijkstra(
            G_modified,
            start_node,
            weight='length'   # Bobot jarak berdasarkan panjang jalan
        )

        # Jika node tujuan tidak tercapai
        if end_node not in paths:
            raise nx.NetworkXNoPath

        # Ambil rute ke node tujuan
        route = paths[end_node]
        total_distance = distances[end_node]

        # Ubah node menjadi koordinat (lat, lon)
        route_coordinates = [
            (G_modified.nodes[node]['y'], G_modified.nodes[node]['x'])
            for node in route
        ]

        # DATA VISUALISASI EXPLORASI

        # Ambil node yang dieksplor sampai jarak rute final
        explored_nodes_for_vis = [
            node for node, dist in distances.items()
            if dist <= total_distance
        ]

        temp_segments_with_dist = []

        for node in explored_nodes_for_vis:
            path_to_node = paths.get(node)

            # Pastikan path valid dan punya edge
            if path_to_node and len(path_to_node) > 1:
                p1_node = path_to_node[-2]
                p2_node = path_to_node[-1]

                dist_to_segment_end = distances.get(
                    p2_node, float('inf')
                )

                p1_coord = (
                    G_modified.nodes[p1_node]['y'],
                    G_modified.nodes[p1_node]['x']
                )
                p2_coord = (
                    G_modified.nodes[p2_node]['y'],
                    G_modified.nodes[p2_node]['x']
                )

                temp_segments_with_dist.append(
                    (dist_to_segment_end, [p1_coord, p2_coord])
                )

        # Urutkan segment berdasarkan jarak
        temp_segments_with_dist.sort(key=lambda x: x[0])

        # Ambil hanya segmentnya
        sorted_segments = [
            segment for dist, segment in temp_segments_with_dist
        ]

        # RESPONSE

        return jsonify({
            "status": "success",
            "route_coordinates": route_coordinates,
            "explored_segments": sorted_segments,
            "distance_meters": total_distance
        })

    # Jika tidak ada jalur
    except nx.NetworkXNoPath:
        return jsonify({
            "status": "error",
            "message": "Tidak ada rute yang ditemukan."
        }), 200

    # Error lain
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# RUN SERVER

if __name__ == '__main__':
    # Jalankan Flask di semua IP
    # Port 8080
    # debug=True → auto reload & tampilkan error detail
    app.run(host='0.0.0.0', port=8080, debug=True)
