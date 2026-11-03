from vsl.components.electrical.battery import Battery
from vsl.components.electrical.switch import Switch
from vsl.components.electrical.bulb import Bulb
from vsl.components.electrical.resistor import Resistor
from vsl.components.electrical.meter import Ammeter, Voltmeter
from vsl.components.electrical.wire import Wire

class CircuitSolver:
    VOLTAGE_TOLERANCE = 0.0001
    MIN_RELAXATION_STEPS = 4
    BASE_MAX_RELAXATION_STEPS = 200
    latest_metrics = {
        "node_count": 0,
        "component_count": 0,
        "powered_components": 0,
        "active_sources": 0,
        "total_current": 0.0,
        "total_power": 0.0,
        "equivalent_resistance": None,
    }

    @staticmethod
    def solve(scene_objects, wires):
        CircuitSolver.latest_metrics = {
            "node_count": 0,
            "component_count": len(scene_objects),
            "powered_components": 0,
            "active_sources": 0,
            "total_current": 0.0,
            "total_power": 0.0,
            "equivalent_resistance": None,
        }
        # 1. Reset Visuals
        for obj in scene_objects:
            obj.receiving_power = False
            obj.brightness = 0.0
            obj.v_drop = 0.0
            obj.current = 0.0
            if isinstance(obj, Battery):
                obj.terminal_voltage = getattr(obj, "voltage", 9.0)
            if isinstance(obj, (Ammeter, Voltmeter)): obj.value = 0.0
            
        for wire in wires: 
            wire.has_power = False
            wire.voltage = 0.0
            wire.current = 0.0

        # 2. Node Discovery (Union-Find)
        parent = {} 
        def find(i):
            if parent[i] != i: parent[i] = find(parent[i])
            return parent[i]
        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j: parent[root_i] = root_j

        for obj in scene_objects:
            if hasattr(obj, 'terminals'):
                for i in range(len(obj.terminals)):
                    key = (obj, i)
                    parent[key] = key

        def get_term_idx(obj, offset_x, offset_y):
            if not hasattr(obj, 'terminals'): return 0
            best_idx, min_dist = 10000, 10000
            for i, term in enumerate(obj.terminals):
                dx = term['x'] - offset_x
                dy = term['y'] - offset_y
                dist = dx*dx + dy*dy
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i
            return best_idx

        for w in wires:
            t1_idx = get_term_idx(w.start_obj, w.start_offset[0], w.start_offset[1])
            t2_idx = get_term_idx(w.end_obj, w.end_offset[0], w.end_offset[1])
            key1, key2 = (w.start_obj, t1_idx), (w.end_obj, t2_idx)
            if key1 in parent and key2 in parent: union(key1, key2)

        distinct_nodes = {}
        unique_id_counter = 0
        node_map = {}
        for key in parent:
            root = find(key)
            if root not in distinct_nodes:
                distinct_nodes[root] = unique_id_counter
                unique_id_counter += 1
            node_map[key] = distinct_nodes[root]

        num_nodes = unique_id_counter
        CircuitSolver.latest_metrics["node_count"] = num_nodes
        if num_nodes == 0: return

        # 3. Build Conductance Graph
        voltages = [0.0] * num_nodes
        is_fixed = [False] * num_nodes
        
        batteries = [o for o in scene_objects if isinstance(o, Battery)]
        CircuitSolver.latest_metrics["active_sources"] = len(batteries)
        for bat in batteries:
            if (bat, 0) in node_map and (bat, 1) in node_map:
                p_node, n_node = node_map[(bat, 0)], node_map[(bat, 1)]
                if p_node == n_node:
                    continue
                bat_voltage = getattr(bat, 'voltage', 9.0)
                voltages[p_node], is_fixed[p_node] = bat_voltage, True
                voltages[n_node], is_fixed[n_node] = 0.0, True

        adj = [[] for _ in range(num_nodes)]

        def add_component_edge(obj):
            if not hasattr(obj, 'terminals') or len(obj.terminals) < 2: return
            
            term_count = len(obj.terminals)
            res = getattr(obj, 'resistance', float('inf'))
            if res == float('inf'): return 
            
            # FIX: Stabilized conductance to prevent NaN explosion on short circuits
            G = 1.0 / max(res, 0.05) / max(1, term_count - 1)
            for i in range(term_count - 1):
                n1, n2 = node_map[(obj, i)], node_map[(obj, i + 1)]
                if n1 != n2:
                    adj[n1].append((n2, G))
                    adj[n2].append((n1, G))

        for obj in scene_objects:
            if hasattr(obj, 'resistance'): 
                add_component_edge(obj)

        # 4. Iterative Solver (Relaxation)
        tolerance = CircuitSolver.VOLTAGE_TOLERANCE
        max_iterations = max(CircuitSolver.BASE_MAX_RELAXATION_STEPS, num_nodes * 50, len(adj) * 20)
        iteration = 0
        max_diff = tolerance + 1.0

        while iteration < max_iterations and (iteration < CircuitSolver.MIN_RELAXATION_STEPS or max_diff > tolerance):
            iteration += 1
            max_diff = 0
            for i in range(num_nodes):
                if is_fixed[i] or not adj[i]: continue 
                sum_vg = sum_g = 0.0
                for (neighbor, g) in adj[i]:
                    sum_vg += voltages[neighbor] * g
                    sum_g += g
                if sum_g > 0:
                    v_new = sum_vg / sum_g
                    diff = abs(voltages[i] - v_new)
                    if diff > max_diff: max_diff = diff
                    voltages[i] = v_new

        # 5. Update Visuals
        for obj in scene_objects:
            if isinstance(obj, Battery):
                bat_voltage = getattr(obj, 'voltage', 9.0)
                p_node = node_map.get((obj, 0))
                bat_current = 0.0
                if p_node is not None:
                    for neighbor, g in adj[p_node]:
                        bat_current += max(0, (voltages[p_node] - voltages[neighbor]) * g)

                obj.current = min(bat_current, 100.0)
                obj.terminal_voltage = bat_voltage
                obj.v_drop = bat_voltage
                obj.receiving_power = obj.current > 0.001

                CircuitSolver.latest_metrics["total_current"] += obj.current
                CircuitSolver.latest_metrics["total_power"] += obj.current * bat_voltage
                continue
            
            if hasattr(obj, 'terminals') and len(obj.terminals) >= 2:
                n1 = node_map[(obj, 0)]
                n2 = node_map[(obj, len(obj.terminals) - 1)] 
                
                v_drop = abs(voltages[n1] - voltages[n2])
                obj.v_drop = v_drop
                
                res = getattr(obj, 'resistance', float('inf'))
                
                if res == float('inf'):
                    current = 0.0
                else:
                    current = v_drop / max(res, 0.05)
                    
                obj.current = min(current, 100.0) 
                
                if obj.current > 0.001:
                    obj.receiving_power = True
                    CircuitSolver.latest_metrics["powered_components"] += 1
                if isinstance(obj, Voltmeter): obj.value = v_drop
                if isinstance(obj, Ammeter): obj.value = obj.current
        
        for w in wires:
            t1_idx = get_term_idx(w.start_obj, w.start_offset[0], w.start_offset[1])
            key = (w.start_obj, t1_idx)
            if key in node_map:
                v = voltages[node_map[key]]
                w.voltage = v
                if v > 1.0: w.has_power = True
            
            if hasattr(w.start_obj, 'current'):
                w.current = w.start_obj.current

        total_current = CircuitSolver.latest_metrics["total_current"]
        max_voltage = max((getattr(bat, 'voltage', 0.0) for bat in batteries), default=0.0)
        if total_current > 1e-6 and max_voltage > 0.0:
            CircuitSolver.latest_metrics["equivalent_resistance"] = max_voltage / total_current
