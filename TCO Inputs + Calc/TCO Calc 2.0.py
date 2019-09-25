# the way I've written this code its designed to be as organized as possible with little regard for speed.
# However, even with 6000 buses it doesnt take long at all.

from typing import Dict, Any
import pandas as pd
import numpy
import matplotlib.pyplot as plt
import copy
import random

icct_colors = ['#007A94', '#4E3227', '#D6492A', '#9B243E', '#F4AF00', '#6C953C', '#642566', '#DED5B3', '#36424A',
               '#03CCFB', '#00A6CD', '#006177', '#00495A', '#BDDB99', '#8EB461', '#507821', '#305309', '#DD7188',
               '#B7415A', '#7A0A22', '#520012']


# takes a start and an end either as numbers or as columns and produces an inclusive range for an excel sheet
def excel_to_index(start, end, size=0, flip=False, spec=()):
    if isinstance(start, str):
        start = ord(start.lower())-97 if len(start) == 1 else ord(start[0].lower())+ord(start[1].lower())-194
        end = ord(end.lower())-97 if len(end) == 1 else ord(end[0].lower())+ord(end[1].lower())-194
        if len(spec):
            for b in range(len(spec)):
                spec[b] = ord(spec[b].lower())-97
    return [x for x in list(range(0, start-1))+list(range(end, size)) if x not in spec]\
        if flip else [x for x in list(range(start, end+1)) if x not in spec]


# returns data frame indexed by row and column for a given input consisting of first and last rows and
# columns inclusive, can be given in natural excel data as well using letter column names
def read_table(r1, r2, c1, c2, path, rspec=None, cspec=None, size=500, col=True):
    return pd.read_csv(path, low_memory=False, header=0, index_col=0 if col else False,
                       skiprows=excel_to_index(r1, r2, size=size, flip=True, spec=rspec if rspec else []),
                       usecols=excel_to_index(c1, c2, spec=cspec if cspec else []))


# elegant printing method for dicts of dicts with data frames as lowest values
def pretty_print(dictionary):
    for key_value in dictionary:
        if isinstance(dictionary[key_value], dict):
            print(key_value, "\n")
            pretty_print(dictionary[key_value])
        else:
            if isinstance(dictionary[key_value], type(pd.DataFrame)):
                print("\n", key_value, "\n", str(dictionary[key_value]))
            else:
                print("\n"+str(key_value) + ":\n"+str(dictionary[key_value]))


# helper function to check for weird empty cells
def to_num(input_num):
    if isinstance(input_num, int) or isinstance(input_num, float) or isinstance(input_num, numpy.float64):
        return numpy.float(input_num)
    else:
        return 0


# reads a very simple file like the one output by the final script
def quick_read_basic(file="finalresults.csv"):
    table = read_table(1, 11, "A", "I", file)
    table = table.drop("none")
    return table


# iterates through inputs and separates out into tables by type -- look at backdat.csv
def quick_read_many(file="backdat2.csv"):
    auto_data = {}
    sheet = pd.read_csv(file, low_memory=False, header=None)
    for outcell in range(len(sheet[0])):
        if not sheet[0][outcell] is numpy.nan and sheet[2][outcell+1] is numpy.nan:
            newdict = {}
            to_next = len(sheet[0])
            for nextcell in range(outcell+1, len(sheet[0])):
                if not sheet[0][nextcell] is numpy.nan and sheet[2][nextcell + 1] is numpy.nan:
                    to_next = nextcell
                    break
            for cell in range(outcell, to_next):
                if not sheet[0][cell] is numpy.nan and not sheet[2][cell+1] is numpy.nan:
                    re = cell+1
                    while re < len(sheet[0]) and not sheet[2][re] is numpy.nan:
                        re += 1
                    ce = 2
                    end = False
                    while not end and ce < sheet.shape[1]:
                        for tcell in range(cell+1, re):
                            if numpy.isnan(to_num(sheet[ce][tcell])):
                                end = True
                                ce -= 1
                        ce += 1
                    newdict[str(sheet[0][cell])] = read_table(r1=cell+2, r2=re, c1=1, c2=ce-1, path=file)
            auto_data[sheet[0][outcell]] = newdict
    return auto_data


# obvious
def percent_to_num(num):
    assert isinstance(num, int) or isinstance(num, float) or isinstance(num, numpy.float64) or \
           isinstance(num, numpy.int64)
    return num/100.


# converts strings to floats and cleans along way
def clean_num_string(num):
    assert isinstance(num, str) or isinstance(num, int) or isinstance(num, float) or isinstance(num, numpy.float64) or \
           isinstance(num, numpy.int64)
    clean_str = "0"
    for char in str(num):
        if char.isnumeric() or char == ".":
            clean_str += char
    return float(clean_str)


print("Reading Background Data")
background = quick_read_many()

# the output from autonomie. See Opensimulations matlab script to better understand what each stat is.
autonomie_outp = quick_read_basic()

# converts between autonomie bus name and actual bus type, data currently in it is false, needs to be generated by auto
bus_name_dict = {
    "BSVI_diesel+standard": "electricbus12moscar_acc.exp#1"
}


# converts between name of data you want and actual excel sheet entry name on the highest level (eg cost, activity)
high_key_dict = {
    "cost": "Cost",
    "activity": "Activity",
    "fuel": "Fuel consumption and emissions"
}
# converts between name of data you want and actual excel sheet entry name on the lowest level
key_dict = {
    "VKT": "VKT (km/bus/yr)",
    "bus_years_ownership": "Bus - years ownership",
    "bus_purchase_price": "Bus purchase price (INR)",
    "inf_purchase_price": "Infrastructure purchase price (INR/bus)",
    "bus_loan_?": "Bus loan? ",
    "inf_loan_?": "Infrastructure loan?",
    "bus_loan_percent": "Bus percent down payment (%)",
    "inf_loan_percent": "Infrastructure down payment (%)",
    "discount_rate": "Discount rate",
    "fuel_price": "Fuel price (INR/DLE) ",
    "fuel_usage": "Fuel/energy consumption (DLE/km)",
    "maintenance": "Maintenance (INR/km)",
    "inf_maintenance": "Infrastructure maintenance cost (INR/DLE)",
    "staff": "Staff costs (INR/km)",
    "def": "DEF price (INR/km)",
    "nox_emission": "NOx tailpipe emission factor (g/km)",
    "pm_emission": "PM tailpipe emission factor (g/km)",
    "pn_emission": "PN tailpipe emission factor (g/km)",
    "bc_emission": "BC tailpipe emission factor (g/km)",
    "oc_emission": "OC tailpipe emission factor (g/km)",
    "co_emission": "CO tailpipe emission factor (g/km)"
}


# gives approximate numerical data for bus sizes
sizes_dict = {"midi": 20,
              "midi_AC": 20,
              "standard": 50,
              "standard_AC": 50,
              "articulated": 80,
              "articulated_AC": 80}


# bus class with functions to get each of the relevant statistics
class Bus:

    def __init__(self, emission_type, size, data_loc=None, keys=None,
                 high_keys=None, age=1, year=2019, charge_time=None, capacity_dict=None):
        self.year = year  # current year
        self.age = age  # age of bus
        self.key_dict = keys if keys else key_dict  # dictionary of keys converting between correct name and table name
        self.high_key_dict = high_keys if high_keys else high_key_dict  # same but for top keys ie cost fuel activity
        self.data_loc = data_loc if data_loc else background  # actual object containing all the tables
        self.standard = emission_type  # emission standard
        self.size = size  # size of bus ie standard articulated or standard_AC
        self.charge_time = charge_time if charge_time else 1000  # time taken to charge from 0 to full
        self.sizes = capacity_dict if capacity_dict else sizes_dict  # dictionary with capacity based on size

    # reads data from the passed in background data, for example can be used to determine get_data("fuel_price", "fuel")
    # first input is the specific table you want and second is the category, defaulted to cost which is the largest
    def get_data(self, low_key, file=None, high_key="cost"):
        assert low_key in self.key_dict and high_key in self.high_key_dict
        return file[self.high_key_dict[high_key]][self.key_dict[low_key]][0][self.get_standard()] if file else \
            self.data_loc[self.high_key_dict[high_key]][self.key_dict[low_key]][self.get_standard()][self.get_size(
            )]

    # gets the yearly def cost, whatever that may be
    def get_def_cost(self):
        return float(self.get_data("def"))

    # gets the total distance traveled in a year
    def get_distance(self):
        return float(clean_num_string(self.get_data("VKT", high_key="activity")))

    # ages the bus by a given number of years
    def age_years(self, yrs=1):
        self.age += yrs

    # gets age
    def get_age(self):
        return self.age

    # returns bus type
    def get_size(self):
        return str(self.size)

    # returns emission standard
    def get_standard(self):
        return str(self.standard)

    # returns the total number of years a bus can be operational
    def get_operational_years(self):
        return float(self.get_data("bus_years_ownership"))

    # returns the total upfront cost of purchasing the bus
    def get_total_bus_cost(self):
        return float(clean_num_string(self.get_data("bus_purchase_price")))

    # returns total upfront cost of purchasing infrastructure
    def get_total_inf_cost(self):
        return float(clean_num_string(self.get_data("inf_purchase_price")))

    # returns the downpayment if a loan is taken out for bus
    def get_down_payment_bus(self):
        if self.get_data("bus_loan_?") == "yes":
            percent_down = percent_to_num(clean_num_string(self.get_data("bus_loan_percent")))
            return float(percent_down * float(self.get_total_bus_cost()))
        else:
            return float(self.get_total_bus_cost())

    # returns the downpayment if a loan is taken out for inf
    def get_down_payment_inf(self):
        if self.get_data("inf_loan_?") == "yes":
            percent_down = percent_to_num(clean_num_string(self.get_data("inf_loan_percent")))
            return float(percent_down * float(self.get_total_inf_cost()))
        else:
            return float(self.get_total_inf_cost())

    # calculates the resale value of the bus at the end of its life
    def get_bus_resale(self):
        deprec_factor = (1.0 - percent_to_num(clean_num_string(self.get_data("discount_rate"))))
        return float(self.get_total_bus_cost() * deprec_factor ** self.get_operational_years())

    # calculates the resale value of the inf at the end of its life
    def get_inf_resale(self):
        deprec_factor = (1.0 - percent_to_num(clean_num_string(self.get_data("discount_rate"))))
        return float(self.get_total_inf_cost() * deprec_factor ** self.get_operational_years())

    # calculates the fuel cost for a year
    def get_fuel_cost(self):
        price = clean_num_string(self.get_data("fuel_price"))
        usage = clean_num_string(self.get_data("fuel_usage", high_key="fuel"))
        return float(self.get_distance()*usage*price+self.get_distance()*self.get_def_cost())

    # calculates lifetime fuel cost
    def get_total_fuel_cost(self):
        return float(self.get_fuel_cost() * self.get_operational_years())

    # calculates yearly vehicle maintenance cost
    def get_vehicle_maintenance_cost(self):
        return float(self.get_distance() * self.get_data("maintenance"))

    # calculates lifetime vehicle maintenance cost
    def get_total_vehicle_maintenance_cost(self):
        return float(self.get_operational_years() * self.get_vehicle_maintenance_cost())

    # yearly infrastructure cost
    def get_inf_maintenance_cost(self):
        return float(self.get_distance() * self.get_data("inf_maintenance"))

    # lifetime infrastructure maintenance cost
    def get_total_inf_maintenance_cost(self):
        return float(self.get_operational_years() * self.get_vehicle_maintenance_cost())

    # yearly staff cost
    def get_staff_cost(self):
        return float(self.get_data("staff")) * self.get_distance()

    # lifetime staff cost
    def get_total_staff_cost(self):
        return float(self.get_staff_cost() * self.get_operational_years())

    # yearly nox emissions
    def get_nox_emissions(self):
        return float(self.get_data("nox_emission", high_key='fuel'))*self.get_distance()

    # yearly pm emissions
    def get_pm_emissions(self):
        return float(self.get_data("pm_emission", high_key='fuel'))*self.get_distance()

    # yearly pn emissions
    def get_pn_emissions(self):
        return float(self.get_data("pn_emission", high_key='fuel'))*self.get_distance()

    # yearly bc emissions
    def get_bc_emissions(self):
        return float(self.get_data("bc_emission", high_key='fuel'))*self.get_distance()

    # yearly oc emissions
    def get_oc_emissions(self):
        return float(self.get_data("oc_emission", high_key='fuel'))*self.get_distance()

    # yearly co emissions
    def get_co_emissions(self):
        return float(self.get_data("co_emission", high_key='fuel'))*self.get_distance()

    # bus person capacity
    def get_person_capacity(self):
        return self.sizes[self.get_size()]

    # time to charge to full
    def get_charge_time(self):
        return self.charge_time


# route object consisting of a bunch of buses and a method dictating the rate at which the are procured with route spec
# info
class Route:

    result: Dict[str, Dict[Any, Any]]

    def __init__(self, procurement_method, current_cost=0, year=2019, current_fleet=None, daily_route_consumption=None,
                 person_count=0, hours=10, rid=None, bus_dict=None):
        self.result = {"total": {}, "main": {}, "fuel": {}, "staff": {}, "inf": {}, "bus": {}}
        self.current_cost = current_cost
        self.buses = current_fleet if current_fleet else set()
        self.year = year
        self.procurement = procurement_method
        self.daily_route_consumption = daily_route_consumption if daily_route_consumption else autonomie_outp
        self.person_count = person_count
        self.current_person_count = 0
        self.hours = hours
        self.rid = rid if rid else "23067"
        self.bus_dict = bus_dict if bus_dict else bus_name_dict
        self.emissions = {"nox": 0, "pm": 0, "pn": 0, "bc": 0, "co": 0, "oc": 0}

    # returns rid
    def get_rid(self):
        return self.rid

    # increments current number of people being transported along the route
    def increment_current_person_count(self, amt):
        self.current_person_count += amt

    # adds a bus to the route
    def add_bus(self, bus):
        self.increment_current_person_count(self.get_bus_person_capacity(bus))
        self.buses.add(bus)

    # removes a bus from the route
    def remove_bus(self, bus):
        self.increment_current_person_count(-self.get_bus_person_capacity(bus))
        self.buses.remove(bus)

    # returns result, dictionary with consts inside
    def get_result(self):
        return self.result

    # adds an amount to a subsection of result
    def set_result(self, division, inc, year):
        self.result[division][year] = self.result[division].get(year, 0) + inc

    # returns the current total cost
    def get_current_cost(self):
        return self.current_cost

    # ret hours
    def get_seconds(self):
        return self.hours*3600.

    # increments current total cost
    def increment_current_cost(self, amt, year):
        self.set_result("total", amt, year)
        self.current_cost += float(amt)

    # increments maintenance cost
    def increment_maintenance_cost(self, amt, year):
        self.set_result("main", amt, year)

    # increments fuel cost
    def increment_fuel_cost(self, amt, year):
        self.set_result("fuel", amt, year)

    # increments staff cost
    def increment_staff_cost(self, amt, year):
        self.set_result("staff", amt, year)

    # increments inf cost
    def increment_inf_cost(self, amt, year):
        self.set_result("inf", amt, year)

    # increments bus cost
    def increment_bus_cost(self, amt, year):
        self.set_result("bus", amt, year)

    def increment_emissions(self, bus):
        self.emissions["nox"] += bus.get_nox_emissions()
        self.emissions["pm"] += bus.get_pm_emissions()
        self.emissions["pn"] += bus.get_pn_emissions()
        self.emissions["bc"] += bus.get_bc_emissions()
        self.emissions["co"] += bus.get_co_emissions()
        self.emissions["oc"] += bus.get_oc_emissions()

    # simulates one year for the bus adding to costs appropriately
    def age_bus(self, bus):
        self.increment_emissions(bus)
        self.increment_maintenance_cost(bus.get_vehicle_maintenance_cost() +
                                        bus.get_inf_maintenance_cost(), self.year)
        self.increment_fuel_cost(bus.get_fuel_cost(), self.year)
        self.increment_staff_cost(bus.get_staff_cost(), self.year)
        self.increment_current_cost(
            bus.get_staff_cost() + bus.get_vehicle_maintenance_cost() + bus.get_inf_maintenance_cost() +
            bus.get_fuel_cost(), self.year)

    # inputs zeros for places where the cost isnt incremented
    def fill_gaps(self):
        self.increment_inf_cost(0, self.year)
        self.increment_bus_cost(0, self.year)
        self.increment_staff_cost(0, self.year)
        self.increment_fuel_cost(0, self.year)
        self.increment_maintenance_cost(0, self.year)
        self.increment_current_cost(0, self.year)

    # gets delta soc from autonomie output for this combo of bus and route
    def get_soc(self, bus):
        return float(self.daily_route_consumption["SOCorfuelvol"]["data_RID"+self.get_rid() + "+"
                                                                  + self.bus_dict[bus.get_standard() + "+"
                                                                  + bus.get_size()]])

    # gets cycle time from autonomie ouptut for this combo of bus and route
    def get_cycle_time(self, bus):
        return float(self.daily_route_consumption["duration"]["data_RID"+self.get_rid() + "+"
                                                              + self.bus_dict[bus.get_standard() + "+"
                                                              + bus.get_size()]])

    # returns the adjusted person capacity for this particular route taking into account potential charging
    def get_bus_person_capacity(self, bus):
        if self.get_soc(bus)*(self.get_seconds()/self.get_cycle_time(bus)) < 80:
            return bus.get_person_capacity()
        else:
            return (self.get_soc(bus)*(self.get_seconds()/self.get_cycle_time(bus))-80)/80.*bus.get_charge_time()

    # simulates one year of this route, aging and removing buses appropriately
    def increment_year(self):
        self.fill_gaps()
        for bus_types in self.procurement(self.year, len(self.buses), self.current_person_count):
            assert bus_types["count"] >= 0
            for b in range(bus_types["count"]):  # add all buses given by procurement method
                to_add = Bus(bus_types["emi_type"], bus_types["size"])
                self.add_bus(to_add)
                self.increment_current_person_count(self.get_bus_person_capacity(to_add))  # increase things
                self.increment_bus_cost(to_add.get_total_bus_cost(), self.year)
                self.increment_inf_cost(to_add.get_total_inf_cost(), self.year)
                self.increment_current_cost(to_add.get_total_bus_cost() + to_add.get_total_inf_cost(), self.year)
        current_buses = list(self.buses)
        for ind in range(len(current_buses)):  # age buses and remove old ones
            bus = current_buses[ind]
            bus.age_years()
            self.age_bus(bus)
            if bus.get_age() > bus.get_operational_years():
                self.remove_bus(bus)
                self.increment_current_cost(-(bus.get_bus_resale() + bus.get_inf_resale()), self.year)
                self.increment_bus_cost(-(bus.get_bus_resale() + bus.get_inf_resale()), self.year)
        self.year += 1
        return self.result, self.emissions

    # simulates multiple years
    def tco_sim(self, years=12):
        for n in range(years):
            self.increment_year()
        return self.result, self.emissions


# fleet object consisting of a bunch of buses and a method dictating the rate at which the are procured
class Fleet:

    result: Dict[str, Dict[Any, Any]]

    def __init__(self, routes, year=2019):
        self.routes = routes
        self.year = year

    # performs simulations for each underlying route and compiles the results
    def simulate(self, years=30):
        total_results = {"total": {}, "main": {}, "fuel": {}, "staff": {}, "inf": {}, "bus": {}}
        total_emissions = {"nox": 0, "pm": 0, "pn": 0, "bc": 0, "co": 0, "oc": 0}
        for route in self.routes:
            for n in range(self.year, self.year+years):
                (a, b) = route.increment_year()
                for key in a:
                    total_results[key][n] = total_results[key].get(n, 0)+a[key][n]
                for key in b:
                    total_emissions[key] += b[key]
        return total_results, total_emissions


# example of a procurement function which takes in year fleet size and capacity and returns a list of dictionaries
# dictating the kind amount and size of bus to be added to the fleet
def simple_procurement(year, fleet_size=None, capacity=0):
    print(year if year and fleet_size and capacity else year)
    return [{"count": int(year/40 + random.randint(1, 30)),  "size": "standard", "emi_type": "BSVI_diesel"}]


# method for creating aesthetic bar graphs, takes in list of items to be graphed, legend, and bottom label, see
# bottom for example
def barstack(itemslist, legend, bottom_label=None):
    barsize = len(itemslist[0])
    barslist = []
    count = 1
    bottom = list(map(lambda x: 0, range(barsize)))
    for bar in itemslist:
        assert len(bar) == barsize
        barslist.append(plt.bar(range(barsize), bar, align='center', color=icct_colors[count], bottom=bottom))
        bottom = [bar[i]+bottom[i] for i in range(barsize)]
        count += 1
    plt.legend([b[0] for b in barslist], legend)
    if bottom_label:
        plt.xticks(range(0, barsize, 2), bottom_label)
    plt.show()


# displays results using barstacking, takes in an output object as generated in the simulation
def display_results(output):
    d1 = output["staff"]
    d2 = output["inf"]
    d3 = output["fuel"]
    d4 = output["main"]
    d5 = output["bus"]

    lister = [list(d1.values()), list(d2.values()), list(d3.values()), list(d4.values()), list(d5.values())]

    barstack(lister, ['Staff', 'Infrastructure', 'Fuel', "Maintenance", "Bus"],
             bottom_label=[list(d1)[i] for i in range(0, len(d1), 2)])


print("Initializing Fleet")

fleet = set()

for k in range(1000):
    ree = Bus("BSVI_diesel", "standard", charge_time=2)
    ree.age_years(k % 12)
    fleet.add(ree)

# sample simulation
bang = Route(simple_procurement, current_fleet=fleet, person_count=1000)
chicka = Fleet([bang, copy.deepcopy(bang), copy.deepcopy(bang)])


print("Simulating...")
(f, g) = chicka.simulate(years=12)

print(g)

for ker in f:
    print(ker, sum(f[ker].values()))

print(sum(f["total"].values()))

print("Displaying Outputs")

display_results(f)
