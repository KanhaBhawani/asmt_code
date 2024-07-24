import simpy
import random
import matplotlib.pyplot as plt

def log(txt, txt2=''):
    with open("logs.txt", 'a') as f:
        f.write(txt + str(txt2) + "\n")

class ContainerTerminal:
    def __init__(self, env, num_berths, num_cranes, num_trucks):
        self.env = env
        self.berths = simpy.Resource(env, capacity=num_berths)
        self.cranes = simpy.Resource(env, capacity=num_cranes)
        self.trucks = simpy.Resource(env, capacity=num_trucks)
        self.unloaded_containers = simpy.Store(env)

        # For visualization
        self.vessels = []
        self.unloading_times = []
        self.vessele_meta_data = []

    def add_metadata(self, dist):
      self.vessele_meta_data.append(dist)

    def load_truck(self, name, i):
        log(f"{self.env.now:.2f}: {name} is waiting for a truck.")
        with self.trucks.request() as truck_request:
            yield truck_request
            log(f"{self.env.now:.2f}: Truck is transporting container {i + 1} from {name}.")
            # Notify the crane that the container has been loaded onto the truck
            yield self.unloaded_containers.put(True)
            yield self.env.timeout(6)  # Simulate truck transport

    def unload_containers(self, vessel):
        start_time = self.env.now
        for i in range(vessel.containers):
            with self.cranes.request() as crane_request:
                log(f"{self.env.now:.2f}: {vessel.name} is waiting for a crane.")
                yield crane_request
                log(f"{self.env.now:.2f}: {vessel.name} is unloading container {i + 1}.")
                yield self.env.timeout(3)  # Simulate unloading a container

                # Start truck loading process after crane unloads
                self.env.process(self.load_truck(vessel.name, i))
                # Wait until the container is loaded onto the truck
                yield self.unloaded_containers.get()


        self.unloading_times.append(self.env.now - start_time)
        log(f"****** {self.env.now:.2f}: {vessel.name} has finished unloading all containers ******")
        vessel.leave_terminal()

    def add_vessel(self, vessel):
        self.vessels.append(vessel)

class ContainerShip:
    def __init__(self, env, name, terminal):
        self.env = env
        self.name = name
        self.terminal = terminal
        self.containers = 150  # Each vessel carries 150 containers
        self.action = env.process(self.arrival())
        self.arrival_time = None
        self.finish_time = None

    def arrival(self):
        self.arrival_time = self.env.now
        log(f"====== {self.env.now:.2f}: {self.name} arriving at the terminal ======")
        with self.terminal.berths.request() as berth_request:
            yield berth_request
            log(f"****** {self.env.now:.2f}: {self.name} has berthed at the terminal ******")
            self.terminal.add_vessel(self)
            yield self.env.process(self.terminal.unload_containers(self))

    def leave_terminal(self):
        log(f"====== {self.env.now:.2f}: {self.name} is leaving the terminal ======")
        self.finish_time = self.env.now
        dist = {
            "name": self.name,
            "arrival_time": self.arrival_time,
            "finish_time": self.finish_time
        }
        self.terminal.add_metadata(dist)

def vessel_arrivals(env, terminal):
    vessel_count = 0
    while True:
        yield env.timeout(random.expovariate(1 / 5))  # Average 5 hours between arrivals in minutes
        vessel_count += 1
        ship = ContainerShip(env, f"Vessel-{vessel_count}", terminal)

def run_simulation(simulation_time, num_berths=2, num_cranes=2, num_trucks=3):
    env = simpy.Environment()
    terminal = ContainerTerminal(env, num_berths, num_cranes, num_trucks)
    env.process(vessel_arrivals(env, terminal))
    env.run(until=simulation_time)

    return terminal.vessels, terminal.unloading_times, terminal.vessele_meta_data

def visualize_simulation(vessels, unloading_times):
    # Create a figure and axis
    fig, ax = plt.subplots()

    if unloading_times:
        # Ensure tick labels match the number of unloading times
        ax.bar(range(len(unloading_times)), unloading_times, tick_label=[v.name for v in vessels[:len(unloading_times)]])
        ax.set_xlabel('Vessels')
        ax.set_ylabel('Total Unloading Time (minutes)')
        ax.set_title('Unloading Times for Each Vessel')

        # Show the plot
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    else:
        log("No vessels processed during the simulation or unloading times are empty.")

if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    SIMULATION_TIME = 60 * 24  # Set to 1440 minutes (24 hours)
    vessels, unloading_times, meta_data = run_simulation(SIMULATION_TIME)
    
    # Debugging information
    log("\n\nVessels processed:", len(vessels))
    log("Unloading Times:", unloading_times)
    log("Metadata", meta_data)
    
    visualize_simulation(vessels, unloading_times)
