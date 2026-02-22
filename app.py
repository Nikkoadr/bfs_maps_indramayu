import os
import pickle
from flask import Flask, request, jsonify, send_from_directory

import osmnx as ox
import networkx as nx
from shapely.geometry import Point, Polygon

# KONFIGURASI FLASK
app = Flask(__name__, static_folder='src')

GRAPH_FILE = "indramayu_graph.pkl"
G_base = None


# FUNGSI UNTUK LOAD ATAU BUAT GRAPH
def load_or_create_graph():
    global G_base
    if G_base is not None:
        return G_base

    if os.path.exists(GRAPH_FILE):
        with open(GRAPH_FILE, "rb") as f:
            G_base = pickle.load(f)
        return G_base

    # Mengambil data jalan drive di Indramayu
    G_new = ox.graph_from_place(
        "Indramayu, West Java, Indonesia",
        network_type='drive',
        simplify=True
    )

    with open(GRAPH_FILE, "wb") as f:
        pickle.dump(G_new, f, pickle.HIGHEST_PROTOCOL)

    G_base = G_new
    return G_base


# ROUTE ROOT
@app.route('/')
def index():
    return send_from_directory('src', 'index.html')


# API AMBIL SEMUA NODE
@app.route('/api/nodes', methods=['GET'])
def get_all_nodes():
    try:
        G = load_or_create_graph()
        # Ekstrak koordinat x (lon) dan y (lat) dari setiap node di graph
        nodes_data = [
            {"lat": data['y'], "lon": data['x']} 
            for node, data in G.nodes(data=True)
        ]
        return jsonify({
            "status": "success",
            "nodes": nodes_data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# API HITUNG RUTE
@app.route('/api/route', methods=['POST'])
def get_route():
    data = request.get_json()

    start_lat = data.get('start_lat')
    start_lon = data.get('start_lon')
    end_lat = data.get('end_lat')
    end_lon = data.get('end_lon')
    obstacles_geojson = data.get('obstacles', [])

    try:
        G = load_or_create_graph()
        G_modified = G.copy()

        # HAPUS NODE DI DALAM OBSTACLE
        nodes_to_remove = set()

        if obstacles_geojson:
            for obs_geojson in obstacles_geojson:
                coords = [tuple(p) for p in obs_geojson['geometry']['coordinates'][0]]
                polygon = Polygon(coords)

                for node, data_node in G_modified.nodes(data=True):
                    point = Point(data_node['x'], data_node['y'])
                    if polygon.contains(point):
                        nodes_to_remove.add(node)

            if nodes_to_remove:
                G_modified.remove_nodes_from(list(nodes_to_remove))

        # NODE TERDEKAT START & END
        start_node = ox.distance.nearest_nodes(G_modified, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G_modified, end_lon, end_lat)

        # BFS MURNI TANPA BOBOT
        path = nx.shortest_path(G_modified, start_node, end_node)
        total_steps = len(path) - 1

        # Konversi node -> koordinat (lat, lon)
        route_coordinates = [
            (G_modified.nodes[node]['y'], G_modified.nodes[node]['x'])
            for node in path
        ]

        # SIMULASI PENJELAJAHAN (untuk animasi)
        distances = nx.single_source_shortest_path_length(G_modified, start_node)
        paths = nx.single_source_shortest_path(G_modified, start_node)

        explored_nodes_for_vis = [
            node for node, dist in distances.items()
            if dist <= total_steps
        ]

        temp_segments_with_dist = []
        for node in explored_nodes_for_vis:
            path_to_node = paths.get(node)
            if path_to_node and len(path_to_node) > 1:
                p1_node = path_to_node[-2]
                p2_node = path_to_node[-1]
                dist_to_segment_end = distances.get(p2_node, float('inf'))
                p1_coord = (G_modified.nodes[p1_node]['y'], G_modified.nodes[p1_node]['x'])
                p2_coord = (G_modified.nodes[p2_node]['y'], G_modified.nodes[p2_node]['x'])
                temp_segments_with_dist.append((dist_to_segment_end, [p1_coord, p2_coord]))

        temp_segments_with_dist.sort(key=lambda x: x[0])
        sorted_segments = [segment for dist, segment in temp_segments_with_dist]

        return jsonify({
            "status": "success",
            "route_coordinates": route_coordinates,
            "explored_segments": sorted_segments,
            "distance_steps": total_steps
        })

    except nx.NetworkXNoPath:
        return jsonify({"status": "error", "message": "Tidak ada rute yang ditemukan."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)