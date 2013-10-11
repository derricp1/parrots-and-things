# ---------------------------------------------------------------------------- #
# parrots.py
# George Corser, January 28, 2013
# Simulation of PARROTS, a VANET privacy model, wirtten in Python 2.7
# PARROTS: Position Altered Random Repetition of Transporation Signature
#
# See the "Main" section at the bottom of this file to change parameters.
# This simulation assumes a grid of roads 100m apart on a 3000mx3000m area
# ---------------------------------------------------------------------------- #

def PARROTS(t, v, parrotee_percent, parroter_percent):
    # Function arguments ----------------------------------------------------- #
    # t is number of time slices. Each time slice is: comfreq = 300 ms
    # v is number of vehicles in simulation
    # parrotee_percent is the ratio of vehicles that wish to request parroting
    # parroter_percent is the ratio of vehicles that volunteer to be parrots
    
    ret_list = list()
    # ret_list is the list of integers output by each iteration of PARROTS()
    
    # ------------------------------------------------------------------------ #
    # SECTION 0: DECLARATIONS
    # ------------------------------------------------------------------------ #
    
    # ----- General Declarations --------------------------------------------- #
    import time # for timestamp
    import decimal # needed for Decimal() function
    import math # needed for sqrt() function
    import random # needed for pseudo random numbers
    random.seed(1) # initialize pseudo random number generator
    topspeed = 30 # meters per second: 30 m/s ~= 108 kph ~= 67 mph
    comfreq = 300 # milliseconds between time intervals
    comrange = 300 # meters: max range of wireless communications
    xmax = 3000 # meters: boundary of traffic grid from (0,0) to (xmax,ymax)
    ymax = 3000
    # t = 600 # number of time slices # function argument
    ti = 0 # index for looping 0-t-1
    # v = 500 # number of vehicles in simulation # function argument
    vi = 0 # index for looping 0 to v-1
    x = list() # list of current x coordinates
    y = list() # list of current y coordinates
    xprior = list() # list of prior x coordinates
    yprior = list() # list of prior y coordinates
    xdir = list() # x direction (-1 = left, 1 = right)
    ydir = list() # y direction (-1 = down, 1 = up)
    leader = list() # vehicle number of group leader
    anonymity = list() # anonymity set size =groupsize of leader, if self only =1
    cum_anonymity = 0 # accumulator to calculate average anonymity set size
    spcp = 0 # 1 = spcp = synch pseudo change protocoal, 0 = aosa = anon online svc access protocol

    # ----- Parroting Declarations ------------------------------------------- #
    # parrotee_percent = 50 # percent chance a vehicle will request parroting # function argument
    # parroter_percent = 50 # percent chance a vehicle will perform parroting # function argument
    # only vehicles desiring more privacy will request parroting
    # only vehicles willing to assist others will perform parroting
    # vehicles may do one, the other, both or neither
    # if a vehicle requests a parrot, all willing vehicles in group will parrot...
    # ... after they change group leaders, not before...
    # this increases the anonymity set size for the parrotee
    # the new anonymity set is the parrottee's current group size plus 
    # the sum of the group sizes of all the parroter's groups
    parroted_id = list() # the id parroted by this vehicle (increases anon set of other vehicle)
    p_anonymity = list() # additional anonymity offered by parroted group
    parrotee = list() # 0 default; 1 if this vehicle requests parroting
    parroter = list() # 0 default; 1 if this vehicle performs parroting
    v_timeout = list() # let timeout be the number of time slices remaining for validity of id
    g_timeout = list() # time slices left for group # for spcp
    p_timeout = list() 
    cum_parrotees = 0
    cum_parroters = 0

    total_pirates = 0
    pirate_sizes = 0
    normal_sizes = 0
    pirate_entropy = 0

    # ------------------------------------------------------------------------ #
    # SECTION 1: INITIALIZATION
    # ------------------------------------------------------------------------ #
    # Assume 15 city blocks per mile, 30 blocks per 2 miles ~= 10000 ft ~= 3000m
    # below: assume roads between blocks at 0, 100, 200, ..., 3000 for xmax=3000m
    # Each car starts at a random intersection on the road grid
    # ------------------------------------------------------------------------ #
    # Step 1.a. Initialize vehicle locations
    # ------------------------------------------------------------------------ #
    for ti in range(1): # initialize vehicles at random coordinates on road grid
        for vi in range(v):
            
            # ----- Vehicles, Groups and Leaders ----------------------------- #
            if vi % 2 == 0: # if vi is even, let x be an even 100 and y be random
                x.append(100*random.randint(0,xmax/100))
                y.append(random.randint(0,ymax))
            else:
                x.append(random.randint(0,xmax))
                y.append(100*random.randint(0,ymax/100))
            xprior.append(0)
            yprior.append(0)
            xdir.append((-1)**random.randint(1,2)) # randomly select -1 or 1 
            ydir.append((-1)**random.randint(1,2))
            leader.append(-1) # -1 means has not been set
            anonymity.append(-1)

            # ----- Parroting ------------------------------------------------ #
            parroted_id.append(-1) # no parroting at initialization
            p_anonymity.append(0) # at first there are zero parroters from previous groups (PAS)
            
            if random.randint(1,101) < parrotee_percent:
                parrotee.append(1)
            else:
                parrotee.append(0)
                
            if random.randint(1,101) < parroter_percent:
                parroter.append(1)
            else:
                parroter.append(0)

            # ----- Parroting Timeout lists ---------------------------------- #
            v_timeout.append(1+random.randint(1,2000)) # use 1+ to prevent <0 later (when decrementing)
            # 2000 is 10 minutes worth of time slices at 300ms per time slice
            p_timeout.append(-1) # none because parroting has not started yet
                
    # ------------------------------------------------------------------------ #
    # Step 1.b. Initialize group leader for each vehicle
    # ------------------------------------------------------------------------ #
    # No parroting on initialization
    for ti in range(1): 
        for vi in range(v):
            cur_dist = comrange + 1 # no distance set yet
            
            if leader[vi] > -1: # if this vehicle already has a group leader
                # check if group leader in still in communications range
                cur_dist = math.sqrt((x[leader[vi]]-x[vi])**2+(y[leader[vi]]-y[vi])**2)
                # if leader is still in commuications range, do nothing for this vi
                if cur_dist > comrange: # if group leader is out of range
                    anonymity[leader[vi]] -= 1 # decrement anonymity set for leader
                    leader[vi] = -1 # establish that vi has no leader
                    anonymity[vi] = 0
                    
            if leader[vi] == -1: # if vi has no leader
                leader[vi] = vi # if no leader found, leader defaults to self
                anonymity[vi] = 1 # if self is leader then anonymity set = 1 (assume anon set = size of group)
                for di in range (vi): # find lowest-numbered vehicle di < vi that is already a group leader
                    if leader[di] == di: # if lower numbered vehicle is already a group leader (leads itself)
                        cur_dist = math.sqrt((x[di]-x[vi])**2+(y[di]-y[vi])**2) # compute euclidean distance
                        if cur_dist < comrange: # if in comrange
                            leader[vi] = di # set leader
                            anonymity[leader[vi]] += 1 # increment anonymity set of leader
                            # anonymity set of this follower will be updated later, in Step 1.c.
                            break # break out of "for" loop: stop looking for more leaders for this vi
            if spcp == 1:
                if leader[vi] == vi:
                    g_timeout.append(1+random.randint(1,1000)) # set group timeout
                else:
                    g_timeout.append(0) # set group timeout 0 for non-leaders
                v_timeout[vi] = g_timeout[leader[vi]]
                        
    # ------------------------------------------------------------------------ #
    # Step 1.c. Initialize anonymity set values for all vehicles
    # ------------------------------------------------------------------------ #
    for ti in range(1): 
        for vi in range(v):
            anonymity[vi] = anonymity[leader[vi]] # vehicle's anonymity set size equals leader's group size

    # ------------------------------------------------------------------------ #
    # SECTION 2: VEHICLE MOVEMENTS -- INCLUDES GROUP LEADER CHANGES, TIMEOUTS,
    # ANONYMITY SET (A.S.) CHANGES, PARROTING CHANGES, AND PARROT A.S. CHANGES
    # ------------------------------------------------------------------------ #

    for ti in range(t): # move vehicles to nearby coordinates on road grid

        total_pirates = 0
        pirate_sizes = 0
        normal_sizes = 0
        pirate_entropy = 0

        # -------------------------------------------------------------------- #       
        # Decrement timeout for all vehicles and parrots
        # -------------------------------------------------------------------- #
        for vi in range(v):
            v_timeout[vi] -= 1
            if v_timeout[vi] == 0: # if vehicle pseudo-id times out, reset timer
                v_timeout[vi] = random.randint(1,2000)
            if p_timeout[vi] != -1:
                p_timeout[vi] -= 1
                if p_timeout[vi] == 0: 
                    p_timeout[vi] = -1 # end parroting
                    parroted_id[vi] = -1
                
        # -------------------------------------------------------------------- #
        # Initialize accumulators for output
        # -------------------------------------------------------------------- #
        entropy = 0.0
        as1 = 0.0
        cum_anonymity = 0 # initialize anonymity set accumulator
        # cum_anonymity is used to calculate the overall A. S. size at end of program
        cum_parrotees = 0
        cum_parroters = 0
        cum_p_anonymity = 0
        parrot_counter = 0
        
        # -------------------------------------------------------------------- #
        # Step 2.a. Vehicle movements - randomize vehicles as they traverse the road grid
        # -------------------------------------------------------------------- #
        for vi in range(v):
            new_group_leader = 0
            xprior[vi] = x[vi]
            yprior[vi] = y[vi]
            increment = random.randint(0,topspeed*comfreq/1000)
            if x[vi] % 100 == 0: # if vehicle is on vertical road stay vertical
                x[vi] = x[vi]
                if y[vi] + ydir[vi] * increment > ymax:
                    y[vi] = ymax
                    ydir[vi] = - ydir[vi]
                elif y[vi] + ydir[vi] * increment < 0:
                    y[vi] = 0
                    ydir[vi] = - ydir[vi]
                else:
                    y[vi] = y[vi] + ydir[vi] * increment
                if y[vi] % 100 > 90: # if close to horizontal
                    y[vi] = y[vi] + 100 - y[vi] % 100 # then switch to vertical next time
                    x[vi] = x[vi] - 1
                    if x[vi] < 0:
                        x[vi] = 1
            else:
                y[vi] = y[vi]
                if x[vi] + xdir[vi] * increment > xmax:
                    x[vi] = xmax
                    xdir[vi] = - xdir[vi]
                elif x[vi] + xdir[vi] * increment < 0:
                    x[vi] = 0
                    xdir[vi] = - xdir[vi]
                else:
                    x[vi] = x[vi] + xdir[vi] * increment
                if x[vi] % 100 > 90: # if close to vertical
                    x[vi] = x[vi] + 100 - x[vi] % 100 # then switch to horizontal next time
                    y[vi] = y[vi] - 1
                    if y[vi] < 0:
                        y[vi] = 1
                        
            # ---------------------------------------------------------------- #
            # Step 2.b. Group Leader updates - vehicles change group leaders
            # depending on transmission range (default comrange = 300m)
            # ---------------------------------------------------------------- #
            cur_dist = comrange + 1 # no distance set yet

            if leader[vi] > -1: # if this vehicle already has a group leader
                # check if group leader in still in communications range
                cur_dist = math.sqrt((x[leader[vi]]-x[vi])**2+(y[leader[vi]]-y[vi])**2)
                # if leader is still in commuications range, do nothing for this vi
                if cur_dist > comrange: # if group leader is out of range
                    anonymity[leader[vi]] -= 1 # decrement anonymity set for leader
                    leader[vi] = -1 # establish that vi has no leader
                    anonymity[vi] = 0
                    if spcp == 1:
                        g_timeout[vi] = 1+random.randint(1,1000) # set group timeout for spcp
                    
            if leader[vi] == -1: # if vi has no leader
                leader[vi] = vi # if no leader found, leader defaults to self
                anonymity[vi] = 1 # if self is leader then anonymity set = 1 (assume anon set = size of group)
                for di in range (vi): # find lowest-numbered vehicle di < vi that is already a group leader
                    if leader[di] == di: # if lower numbered vehicle is already a group leader (leads itself)
                        cur_dist = math.sqrt((x[di]-x[vi])**2+(y[di]-y[vi])**2) # compute euclidean distance
                        if cur_dist < comrange: # if in comrange
                            leader[vi] = di # set leader
                            anonymity[leader[vi]] += 1 # increment anonymity set of leader
                            # anonymity set of this follower will be updated later, in Step 2.c.

                            break # break out of "for" loop: stop looking for more leaders for this vi
            if spcp == 1:
                if leader[vi] == vi:
                    g_timeout[vi] -= g_timeout[vi] # set group timeout
                    if g_timeout < 0:
                        exit(1)
                else:
                    g_timeout.append(0) # set group timeout 0 for non-leaders
                v_timeout[vi] = g_timeout[leader[vi]]  # v_timeout decrements with g_timeout

            # ---------------------------------------------------------------- #
            # Step 2.c. Update anonymity set (A. S.) 
            # ---------------------------------------------------------------- #
            anonymity[vi] = anonymity[leader[vi]] # vehicle's anonymity set size equals leader's group size

            # ---------------------------------------------------------------- #
            # Step 2.d. Update parroting status
            # parrots identified while in same group, though
            # parroting only occurs when parroter NOT in same group as parrotee
            # parroter parrots only one parrotee at any given time
            # max parrots = v, the number of vehicles
            # This simulation assume a parrot parrots only ONE other vehicle
            # ---------------------------------------------------------------- #
            # Find a parrot... vi is parroter and pi is parrotee
            for pi in range (v): # search all vehicles
                if leader[pi] == leader[vi]:       # find vehicle in same group
                    if pi != vi:                   # but not self same vehicle
                        if parrotee[pi] == 1:      # pi wants a parrot
                            if parroter[vi] == 1:  # vi wants to be a parrot
                                if parroted_id[vi] == -1: # no parrot set yet
                                    parroted_id[vi] = pi  # vi parrots for pi
                                    p_timeout[vi] = v_timeout[parroted_id[vi]]
                                    # parroting times out when parrotee's pseudoid times out
                                    p_anonymity[parroted_id[vi]] += 1 #gpc
                                    parrot_counter += 1
                                    break     # get out of "for" loop
                                
            # ---------------------------------------------------------------- #
            # Step 2.e. Update all parrot anonymity sets (P. A. S.) 
            # ---------------------------------------------------------------- #
            # what if two vehicles in same group parroting same parrotee? IT could happen...
            for pi in range(v): # parrotee's p_anonymity equals sum of all parrots' group sizes
                p_anonymity[pi]= 0
            for pi in range(v):
                if parroted_id[pi] > -1:
                    p_anonymity[parroted_id[pi]] += anonymity[pi] 

        # -------------------------------------------------------------------- #
        # Increment accumulators for output
        # -------------------------------------------------------------------- #
            #if leader[vi] == vi:
            #temp_entropy = 1 / (anonymity[vi]+p_anonymity[vi]+.0000000000001)
            #temp_entropy_log = 0.0
            #temp_entropy_log = math.log(temp_entropy,2) # log of fraction is negative
            #entropy = entropy - temp_entropy_log
            entropy = entropy + math.log(anonymity[vi]+p_anonymity[vi],2) # see eq p.101
            if anonymity[vi] + p_anonymity[vi] == 1: # as1 ia number of cars with as=1
               as1 = as1 + 1
            cum_anonymity += anonymity[vi]    # add this vi's A. S. to the total A. S.
            cum_parrotees += parrotee[vi]
            cum_parroters += parroter[vi]
            cum_p_anonymity += p_anonymity[vi]
            if parroted_id[vi] > -1:
                parrot_counter += 1

            normal_sizes += (p_anonymity[vi] + anonymity[vi])
            isparroted = 0
            for (check) in range(v):
                if parroted_id[check] == vi:
                    isparroted = 1

            if isparroted == 1:
                pirate_sizes = pirate_sizes + (p_anonymity[vi] + anonymity[vi])
                pirate_entropy = pirate_entropy + math.log(anonymity[vi]+p_anonymity[vi],2)
                total_pirates += 1
            
        if ((ti+1) % 100) == 0:              # on last iteration print output
            ret_list = list()
            ret_list.append(t)                # total time slices
            ret_list.append(v)                # total vehicles
            ret_list.append(cum_anonymity)    # sum(AS): sum of all anonymity set values
            ret_list.append(parrotee_percent) # PEP: parrotee percent
            ret_list.append(parroter_percent) # PRP: parroter percent
            ret_list.append(cum_parrotees)    # sum(PR): number of potetial parrotees
            ret_list.append(cum_parroters)    # sum(PR): number of potetial parroters
            ret_list.append(cum_p_anonymity)  # sum(PAS): sum of AS's of active parroters
            ret_list.append(parrot_counter)   # count(PAS): number of active parroters
            ret_list.append(time.clock())     # timestamp
            ret_list.append(as1)              # count of vehicles with as size = 1
            ret_list.append(as1 / v)          # tracking probability
            ret_list.append(entropy)
            ret_list.append(entropy / v)
            # print "t, v, cum_anon, ptee_pct, pter_pct, cum_ptees, cum_pters, cum_p_anon, pter_actual, time"

            minass = v + 1 #calculation of a.s.s range
            maxass = 0
            for carz in range(v):
                if anonymity[carz] > maxass:
                    maxass = anonymity[carz]
                if anonymity[carz] < minass:
                    minass = anonymity[carz]
                    
            if total_pirates == 0:
                total_pirates = 1
                    
            ret_list.append(v)                                 # active cars at last time step
            ret_list.append(as1 / v)                           # tracking probability
            ret_list.append(entropy / v)                       # entropy
            ret_list.append(cum_anonymity)                              # sum(AS): sum of all anonymity set values
            ret_list.append(float(cum_anonymity+cum_p_anonymity) / float(v))   # average AS size
            ret_list.append(minass)
            ret_list.append(maxass)
            ret_list.append(maxass-minass)
            ret_list.append(normal_sizes/v)
            ret_list.append(pirate_sizes/total_pirates)
            ret_list.append(total_pirates)
            ret_list.append(pirate_entropy/total_pirates)

            print (ret_list)

        print ("TIME" , ti, "COMPLETE")
        
    return ret_list # end of Section 2

# ----------------------------------------------------------------------------- #
#   Main
# ----------------------------------------------------------------------------- #
print (PARROTS(2000,400,100,50))
print ("###############################################")
print (PARROTS(2000,800,100,50))
print ("###############################################")
print (PARROTS(2000,1200,100,50))
print ("###############################################")
print (PARROTS(2000,1600,100,50))
print ("###############################################")
print (PARROTS(2000,2000,100,50))
print ("###############################################")
print (PARROTS(2000,2400,100,50))
print ("###############################################")
print (PARROTS(2000,2800,100,50))
print ("###############################################")
print (PARROTS(2000,3200,100,50))
print ("###############################################")
print (PARROTS(2000,3600,100,50))
print ("###############################################")
print (PARROTS(2000,4000,100,50))
