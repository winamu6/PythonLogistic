import networkx as nx
import matplotlib.pyplot as plt
from heapq import heappush, heappop


def main():
    print("ранспортная логистика: оптимизация маршрутов доставки")

    cities = input_cities()
    roads = input_roads()
    vehicles = input_vehicles()
    warehouse_stock = float(input("Введите запас товара на центральном складе: "))
    start_city = input("Введите город, где расположен центральный склад: ").strip()

    G = build_graph(cities, roads, warehouse_stock)

    total_demand = sum(G.nodes[node]["demand"] for node in G.nodes if node != start_city)
    if total_demand > warehouse_stock:
        print("Ошибка: Недостаточно товара на складе!")
        return

    routes = allocate_resources(G, start_city, vehicles)

    print("\n=== Результаты ===")
    for city, data in routes.items():
        print(f"\nГород: {city}")
        print(f"Маршрут: {' -> '.join([start_city] + [u for u, v in data['path']] + [city])}")
        print(f"Транспорт: {data['vehicle']}")
        print(f"Стоимость доставки: {data['cost']:.2f} у.е.")
        print(f"Время доставки: {data['time']:.2f} ч")

    visualize(G, routes, start_city)


def input_cities():
    cities = []
    print("\nВвод данных о городах (для завершения введите 'end'):")
    while True:
        city_id = input("Идентификатор города: ").strip()
        if city_id.lower() == 'end':
            break
        demand = float(input("Спрос на товар: "))
        deadline = float(input("Крайний срок доставки (часы): "))
        x = float(input("Координата X для визуализации: "))
        y = float(input("Координата Y для визуализации: "))
        cities.append({"id": city_id, "demand": demand, "deadline": deadline, "x": x, "y": y})
    return cities


def input_roads():
    roads = []
    print("\nВвод данных о дорогах (для завершения введите 'end'):")
    while True:
        from_city = input("Город отправления: ").strip()
        if from_city.lower() == 'end':
            break
        to_city = input("Город назначения: ").strip()
        length = float(input("Длина дороги (км): "))
        cost = float(input("Стоимость проезда: "))
        load = float(input("Уровень загрузки (0-1): "))
        roads.append({"from": from_city, "to": to_city, "length": length, "cost": cost, "load": load})
    return roads


def input_vehicles():
    vehicles = []
    print("\nВвод данных о транспортных средствах (для завершения введите 'end'):")
    while True:
        vehicle_type = input("Тип транспорта: ").strip()
        if vehicle_type.lower() == 'end':
            break
        capacity = float(input("Грузоподъёмность (кг): "))
        speed = float(input("Скорость (км/ч): "))
        cost_per_km = float(input("Стоимость за км: "))
        vehicles.append({"type": vehicle_type, "capacity": capacity, "speed": speed, "cost_per_km": cost_per_km})
    return vehicles


def build_graph(cities, roads, warehouse_stock):
    G = nx.Graph()
    for city in cities:
        G.add_node(
            city["id"],
            demand=city["demand"],
            deadline=city["deadline"],
            pos=(city["x"], city["y"])
        )
    G.nodes[cities[0]["id"]]["stock"] = warehouse_stock  # Центральный склад
    for road in roads:
        G.add_edge(
            road["from"],
            road["to"],
            length=road["length"],
            cost=road["cost"],
            load=road["load"]
        )
    return G


def dijkstra(graph, start, vehicle_speed):
    times = {node: float('inf') for node in graph.nodes}
    times[start] = 0
    queue = [(0, start)]
    paths = {start: []}

    while queue:
        current_time, current_node = heappop(queue)
        if current_time > times[current_node]:
            continue
        for neighbor in graph.neighbors(current_node):
            edge = graph[current_node][neighbor]
            effective_speed = vehicle_speed * (1 - edge["load"])
            time = edge["length"] / effective_speed
            new_time = current_time + time
            if new_time < times[neighbor]:
                times[neighbor] = new_time
                paths[neighbor] = paths[current_node] + [(current_node, neighbor)]
                heappush(queue, (new_time, neighbor))
    return times, paths


def select_vehicle(demand, distance, vehicles):
    suitable = []
    for vehicle in vehicles:
        if vehicle["capacity"] >= demand:
            cost = distance * vehicle["cost_per_km"]
            suitable.append((vehicle, cost))
    if not suitable:
        return None
    return min(suitable, key=lambda x: x[1])[0]


def allocate_resources(graph, start, vehicles):
    routes = {}
    for node in graph.nodes:
        if node == start:
            continue
        demand = graph.nodes[node]["demand"]
        deadline = graph.nodes[node]["deadline"]

        best_time = float('inf')
        best_path = []
        best_vehicle = None
        best_cost = float('inf')

        for vehicle in vehicles:
            if vehicle["capacity"] < demand:
                continue
            times, paths = dijkstra(graph, start, vehicle["speed"])
            if times[node] > deadline:
                continue
            distance = sum(graph[u][v]["length"] for u, v in paths[node])
            cost = distance * vehicle["cost_per_km"]
            if times[node] < best_time or (times[node] == best_time and cost < best_cost):
                best_time = times[node]
                best_path = paths[node]
                best_vehicle = vehicle
                best_cost = cost

        if best_vehicle:
            routes[node] = {
                "path": best_path,
                "vehicle": best_vehicle["type"],
                "cost": best_cost,
                "time": best_time
            }
        else:
            print(f"Предупреждение: Невозможно доставить товар в город {node} с учётом ограничений!")
    return routes


def visualize(graph, routes, start_city):
    pos = nx.get_node_attributes(graph, "pos")
    plt.figure(figsize=(12, 8))
    nx.draw(graph, pos, with_labels=True, node_color="lightblue", edge_color="gray", node_size=500)

    nx.draw_networkx_nodes(graph, pos, nodelist=[start_city], node_color="red", node_size=700)

    for city, data in routes.items():
        path = data["path"]
        if path:
            edges = [(u, v) for u, v in path]
            nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color="green", width=2)

    plt.title("Оптимальные маршруты доставки")
    plt.show()
