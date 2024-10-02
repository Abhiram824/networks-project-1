# Base router class
from router import Router
# import priority queue
from queue import PriorityQueue

# This is long enough so that broadcasts complete even on large topologies
BROADCAST_INTERVAL = 10


# Class representing link state routers
class LSRouter(Router):
    def __init__(self, router_id, clock):
        # Common initialization routines
        Router.__init__(self, router_id, clock)

        # Is the broadcast complete? => Can we run Dijkstra's algorithm?
        # For now, we'll use a simple heuristic for this:
        # If BROADCAST_INTERVAL since the first link state advertisement (LSA) at time 0,
        # we'll declare the broadcast complete
        self.broadcast_complete = False

        # Have you run Dijkstra's algorithm? This is to ensure you don't repeatedly run it.
        self.routes_computed = False

        # LSA dictionary mapping from a router ID to the links for that router.
        # We'll initialize lsa_dict to  this router's own links.
        self.lsa_dict = dict()

        # For each LSA received from a distinct router,
        # maintain if it has been broadcasted or not.
        # This is to avoid repeated broadcasts of the same LSA
        # We'll initialize self.broadcasted to reflect the fact that this router's own links
        # have not yet been broadcasted as of time 0.
        self.broadcasted = {self.router_id: False}

    # Initialize link state to this router's own links alone
    def initialize_algorithm(self):
        self.lsa_dict = {self.router_id: self.links}

    def run_one_tick(self):
        if self.clock.read_tick() >= BROADCAST_INTERVAL and not self.routes_computed:
            # If broadcast phase is over, compute routes and return
            self.broadcast_complete = True
            self.dijkstras_algorithm()
            self.routes_computed = True
            return
        elif self.clock.read_tick() < BROADCAST_INTERVAL:
            # TODO: Go through the LSAs received so far.
            # broadcast each LSA to this router's neighbors if the LSA has not been broadcasted yet
            for id, lsa in self.lsa_dict.items():
                if id not in self.broadcasted or not self.broadcasted[id] :
                    for obj in self.neighbors:
                        if id != obj.router_id:
                            self.send(obj, lsa, id)
                    self.broadcasted[id] = True
        else:
            return

    # Note that adv_router is the router that generated this advertisement,
    # which may be different from "self",
    # the router that is broadcasting this advertisement by sending it to a neighbor of self.
    def send(self, neighbor, ls_adv, adv_router):
        neighbor.lsa_dict[adv_router] = ls_adv
        # It's OK to reinitialize this even if adv_router even if adv_router is in lsa_dict

    def dijkstras_algorithm(self):
        # TODO:
        # (1) Implement Dijkstra's single-source shortest path algorithm
        # to find the shortest paths from this router to all other destinations in the network.
        # Feel free to use a different shortest path algo. if you're more comfortable with it.
        # (2) Remember to populate self.fwd_table with the next hop for every destination
        # because simulator.py uses this to check your LS implementation.
        # (3) If it helps, you can use the helper function next_hop below to compute the next hop once you
        # have populated the prev dictionary which maps a destination to the penultimate hop
        # on the shortest path to this destination from this router.
        # needed when there are two paths of same size
        counter = 0
        tentative = PriorityQueue()
        tentative.put((0, counter, self, self))
        counter += 1
        confirmed = {}
        while tentative.qsize() > 0:
            next = tentative.get()
            if next[2] in confirmed:
                continue
            confirmed[next[2]] = next[3]
            for neighbor in next[2].neighbors:
                if neighbor in confirmed:
                    continue
                tentative.put((next[0] + next[2].links[neighbor.router_id], counter, neighbor,  next[2]))
                counter += 1
        
        prev = {key.router_id: confirmed[key].router_id for key in confirmed}
        for key in prev:
            if key == self.router_id:
                continue
            self.fwd_table[key] = self.next_hop(key, prev)

    # Recursive function for computing next hops using the prev dictionary
    def next_hop(self, dst, prev):
        # Can't find next_hop if dst is disconnected from self.router_id
        assert prev[dst] != -1
        # Nor if dst and self.router_id are the same
        assert self.router_id != dst
        if prev[dst] == self.router_id:
            # base case, src and dst are directly connected
            return dst
        else:
            return self.next_hop(prev[dst], prev)
