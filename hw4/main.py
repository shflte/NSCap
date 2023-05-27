import networkx as nx
import copy

def dijkstra(cost: list[list[int]]) -> list[list[int]]:
    num_routers = len(cost)

    graph = nx.Graph()
    for i in range(len(cost)):
        for j in range(len(cost[i])):
            if cost[i][j] != 999:
                graph.add_edge(i, j, weight=cost[i][j])

    shortest_paths = dict(nx.all_pairs_dijkstra_path_length(graph))

    dist = [[0 for __ in range(num_routers)] for _ in range(num_routers)]
    for i in range(num_routers):
        for j in range(num_routers):
            dist[i][j] = shortest_paths[i][j]

    return dist

def run_ospf(link_cost: list) -> tuple[list, list]:
    num_routers = len(link_cost)
    distance_vector = dijkstra(link_cost)
    stored_linked_state = [[] for _ in range(num_routers)]
    for i in range(num_routers):
        stored_linked_state[i].append(i)

    # init log
    log = []
    converge = False
    while not converge:
        staged = [[] for _ in range(num_routers)]
        round_log = []
        converge = True

        # round start
        # for each router in graph
        for i in range(num_routers):
            # for all neighbor of ith router
            for neighbor in range(num_routers):
                # valid neighbor
                if link_cost[i][neighbor] < 999 and link_cost[i][neighbor] > 0:
                    for link_state in stored_linked_state[i]:
                        if link_state not in stored_linked_state[neighbor] and link_state not in staged[neighbor]:
                            converge = False

                            staged[neighbor].append(link_state)
                            round_log.append((i, link_state, neighbor))

        # commit staged changes of link state of each router
        for i in range(num_routers):
            stored_linked_state[i] += staged[i]
        
        if round_log:
            log += sorted(round_log)
    
    return distance_vector, log
    
def run_rip(link_cost: list) -> tuple[list, list]:
    num_routers = len(link_cost)
    distance_vector = dijkstra(link_cost)
    stored_distance_vector = copy.deepcopy(link_cost)

    # init log
    log = []
    converge = False
    changed = [True for _ in range(num_routers)]
    while not converge:
        receive_distance_vector = [[] for _ in range(num_routers)]
        round_log = []
        converge = True

        # round start
        # i is the guy that inform others
        for i in range(num_routers):
            if changed[i]:
                converge = False
                for neighbor in range(num_routers):
                    # valid neighbor
                    if link_cost[i][neighbor] < 999 and link_cost[i][neighbor] > 0: 
                        receive_distance_vector[neighbor].append((i, stored_distance_vector[i]))
                        round_log.append((i, neighbor))

        # commit staged changes of link state of each router
        changed = [False for _ in range(num_routers)]
        print(receive_distance_vector[5])
        print(stored_distance_vector[5])
        for i in range(num_routers):
            for sender, dv in receive_distance_vector[i]:
                for dest in range(num_routers):
                    if stored_distance_vector[i][sender] + dv[dest] < stored_distance_vector[i][dest]:
                        changed[i] = True
                        stored_distance_vector[i][dest] = stored_distance_vector[i][sender] + dv[dest]
        
        if round_log:
            log += sorted(round_log)
    
    return distance_vector, log


testdata = [
    [  0,   2,   5,   1, 999, 999],
    [  2,   0,   3,   2, 999, 999],
    [  5,   3,   0,   3,   1,   5],
    [  1,   2,   3,   0,   1, 999],
    [999, 999,   1,   1,   0,   2],
    [999, 999,   5, 999,   2,   0]
]

ans_ospf = (
    [[0, 2, 3, 1, 2, 4],
     [2, 0, 3, 2, 3, 5],
     [3, 3, 0, 2, 1, 3],
     [1, 2, 2, 0, 1, 3],
     [2, 3, 1, 1, 0, 2],
     [4, 5, 3, 3, 2, 0]],
    
    [(0, 0, 1), (0, 0, 2), (0, 0, 3),
     (1, 1, 0), (1, 1, 2), (1, 1, 3),
     (2, 2, 0), (2, 2, 1), (2, 2, 3),
     (2, 2, 4), (2, 2, 5), (3, 3, 0),
     (3, 3, 1), (3, 3, 2), (3, 3, 4),
     (4, 4, 2), (4, 4, 3), (4, 4, 5),
     (5, 5, 2), (5, 5, 4), (2, 0, 4),
     (2, 0, 5), (2, 1, 4), (2, 1, 5),
     (2, 3, 5), (2, 4, 0), (2, 4, 1),
     (2, 5, 0), (2, 5, 1), (2, 5, 3)]
)

ans_rip = (
    [[0, 2, 3, 1, 2, 4],
     [2, 0, 3, 2, 3, 5],
     [3, 3, 0, 2, 1, 3],
     [1, 2, 2, 0, 1, 3],
     [2, 3, 1, 1, 0, 2],
     [4, 5, 3, 3, 2, 0]],
    
    [(0, 1), (0, 2), (0, 3), (1, 0),
     (1, 2), (1, 3), (2, 0), (2, 1),
     (2, 3), (2, 4), (2, 5), (3, 0),
     (3, 1), (3, 2), (3, 4), (4, 2),
     (4, 3), (4, 5), (5, 2), (5, 4),
     (0, 1), (0, 2), (0, 3), (1, 0),
     (1, 2), (1, 3), (2, 0), (2, 1),
     (2, 3), (2, 4), (2, 5), (3, 0),
     (3, 1), (3, 2), (3, 4), (4, 2),
     (4, 3), (4, 5), (5, 2), (5, 4),
     (0, 1), (0, 2), (0, 3), (1, 0),
     (1, 2), (1, 3), (2, 0), (2, 1),
     (2, 3), (2, 4), (2, 5), (3, 0),
     (3, 1), (3, 2), (3, 4), (4, 2),
     (4, 3), (4, 5), (5, 2), (5, 4)]
)

# print(run_ospf(testdata))
print(run_rip(testdata))
# print("rip right" if run_rip(testdata) == ans_rip else "rip wrong")