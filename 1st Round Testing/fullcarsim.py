# ---------------------------------------------------------------------------- #
# othermodels.py
#
# A simulation model built off of the PARROTS archetecture to simulate other
# trace models.
#
# See the "Main" section at the bottom of this file to change parameters.
# This simulation assumes a grid of roads 100m apart on a 3000mx3000m area
# ---------------------------------------------------------------------------- #

def MODEL(parrotee_percent, parroter_percent, time_start, time_end, com_range, seed):
    # Function arguments ----------------------------------------------------- #
    # t is number of time slices. Each time slice is: comfreq = 300 ms
    # v is number of vehicles in simulation
    # parrotee_percent is the ratio of vehicles that wish to request parroting
    # parroter_percent is the ratio of vehicles that volunteer to be parrots

    max_count = 9999 #depreciated
    
    ret_list = list()
    # ret_list is the list of integers output
    
    # ------------------------------------------------------------------------ #
    # SECTION 0: DECLARATIONS
    # ------------------------------------------------------------------------ #

    #PD (sections in which I work goes until /PD)
    #need all the characteristics to read in from the file
    times = [] #times in which the states change
    cid = [] #car's id
    curx = [] #starting position on car appearence
    cury = []
    finx = [] #end position after block
    finy = []
    elapsed = [] #time steps from start to end

    import csv

    f = open('rural.csv', 'r')
    counter = 7

    for line in f: #reads in data from csv and seperates it into stats
        for word in line.split():
            counter = counter + 1
            if counter == 8:
                counter = 1
            if counter == 1:
                stamp = float(word)
                if stamp == 0:
                    times.append(0)
                else:
                    if stamp > int(stamp): #round up timestamps to keep time consistently
                        times.append((int(stamp)+1))
                    else:
                        times.append((int(stamp)))
                        
            if counter == 2:
                cid.append(int(word))           
            if counter == 3:
                curx.append(float(word))
            if counter == 4:
                cury.append(float(word))
            if counter == 5:
                finx.append(float(word))           
            if counter == 6:
                finy.append(float(word))
            if counter == 7:
                elapsed.append(float(word))

    f.close()

    #/PD

    #t and v are defined by the file, do this here, not in the function call

    
    # ----- General Declarations --------------------------------------------- #
    import time # for timestamp
    import decimal # needed for Decimal() function
    import math # needed for sqrt() function
    import random # needed for pseudo random numbers
    random.seed(seed) # initialize pseudo random number generator
    topspeed = 30 # meters per second: 30 m/s ~= 108 kph ~= 67 mph
    comfreq = 300 # milliseconds between time intervals
    comrange = com_range # meters: max range of wireless communications
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

    vmax = max(cid); #number of spots to allocate, from 0 to v-1
    v = vmax #explicit declaration
    t = max(times) + 1; #amount of time steps, from 0 to t-1


    targetx = list() #where the car wants to go
    targety = list()
    startingx = list() #where it started
    startingy = list()
    timetotarget = list() #how long it takes
    startingtime = list() #start of this leg
    isactive = list() #results of random formations, active cars at 1

    loopcount = 0 #how many cars in this iteration of the loop - PD
    #if you input invalid times, this will be fixed (if you only want data from certain times)    
    if time_start < 0 or time_start >= t:
        print ("Invalid start time, defaulted to 0")
        time_start = 0

    if time_end < 1 or time_end <= time_start or time_end >= t:
        print ("Invalid end time, defaulted to last time step")
        time_end = t-1
    # works in the steps in the program runtime, 0 to t-1
    # valid times are from t_start to t_end - 1, or t_s <= t < t_e
    #/PD


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

    lineno = 0 # 0 to maxlines-1
    maxlines = len(times)

    # ------------------------------------------------------------------------ #
    # SECTION 1: INITIALIZATION
    # ------------------------------------------------------------------------ #
    # Assume 15 city blocks per mile, 30 blocks per 2 miles ~= 10000 ft ~= 3000m
    # below: assume roads between blocks at 0, 100, 200, ..., 3000 for xmax=3000m
    # Each car starts at a random intersection on the road grid
    # ------------------------------------------------------------------------ #
    # Step 1.a. Initialize vehicle locations
    # ------------------------------------------------------------------------ #
    
    for ti in range(1): # initialize vehicles
        for vi in range(v):
            
            # ----- Vehicles, Groups and Leaders ----------------------------- #
            
            x.append(-9999)
            y.append(-9999)
            curx.append(-9999)
            cury.append(-9999)
            targetx.append(-9999)
            targety.append(-9999)
            startingx.append(-9999)
            startingy.append(-9999)
            timetotarget.append(-9999)
            elapsed.append(-9999)
            startingtime.append(-9999)
            isactive.append(0)

            xprior.append(-9999)
            yprior.append(-9999)
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
        

    #only loads when the line numbers are the same (pre t=0)
            
                
    # ------------------------------------------------------------------------ #
    # Step 1.b. Initialize group leader for each vehicle
    # ------------------------------------------------------------------------ #

    #should not be done. cars don't start on map and that would mess thing sup
    
##    # No parroting on initialization
##    for ti in range(1): 
##        for vi in range(v):
##            cur_dist = comrange + 1 # no distance set yet
##            
##            if leader[vi] > -1: # if this vehicle already has a group leader
##                # check if group leader in still in communications range
##                cur_dist = math.sqrt((x[leader[vi]]-x[vi])**2+(y[leader[vi]]-y[vi])**2)
##                # if leader is still in commuications range, do nothing for this vi
##                if cur_dist > comrange: # if group leader is out of range
##                    anonymity[leader[vi]] -= 1 # decrement anonymity set for leader
##                    leader[vi] = -1 # establish that vi has no leader
##                    anonymity[vi] = 0
##                    
##            if leader[vi] == -1: # if vi has no leader
##                leader[vi] = vi # if no leader found, leader defaults to self
##                anonymity[vi] = 1 # if self is leader then anonymity set = 1 (assume anon set = size of group)
##                for di in range (vi): # find lowest-numbered vehicle di < vi that is already a group leader
##                    if leader[di] == di: # if lower numbered vehicle is already a group leader (leads itself)
##                        cur_dist = math.sqrt((x[di]-x[vi])**2+(y[di]-y[vi])**2) # compute euclidean distance
##                        if cur_dist < comrange: # if in comrange
##                            leader[vi] = di # set leader
##                            anonymity[leader[vi]] += 1 # increment anonymity set of leader
##                            # anonymity set of this follower will be updated later, in Step 1.c.
##                            break # break out of "for" loop: stop looking for more leaders for this vi
##            if spcp == 1:
##                if leader[vi] == vi:
##                    g_timeout.append(1+random.randint(1,1000)) # set group timeout
##                else:
##                    g_timeout.append(0) # set group timeout 0 for non-leaders
##                v_timeout[vi] = g_timeout[leader[vi]]
                        
    # ------------------------------------------------------------------------ #
    # Step 1.c. Initialize anonymity set values for all vehicles
    # ------------------------------------------------------------------------ #
    for ti in range(1): 
        for vi in range(v):
            if leader[vi] == -1:
                anonymity[vi] = -1 #if the car isn't there
            else:
                anonymity[vi] = anonymity[leader[vi]] # vehicle's anonymity set size equals leader's group size


    # ------------------------------------------------------------------------ #
    # Step 1.d. Initialize group of active vehicles
    # ------------------------------------------------------------------------ #

    for ac in range(vmax): #PD
        isactive[ac] = 1 #PD
            

    # ------------------------------------------------------------------------ #
    # SECTION 2: VEHICLE MOVEMENTS -- INCLUDES GROUP LEADER CHANGES, TIMEOUTS,
    # ANONYMITY SET (A.S.) CHANGES, PARROTING CHANGES, AND PARROT A.S. CHANGES
    # ------------------------------------------------------------------------ #

    carsonroad = 0 #PD

    for ti in range(t): # move vehicles to nearby coordinates on road grid
        
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

        #PD

        #need to read all of the points in the file up to this time first
        #needs to be before the cars are checked (ie: here)
        while lineno < maxlines and times[lineno] == ti:
            success = 0
            if carsonroad < max_count:
                success = 1
                carsonroad += 1
            if ti > 0 and x[(cid[lineno]-1)] > -9999: #note that technically, we don't worry about the max anymore because we're not testing it (due to not being realistic)
                success = 1
            if success == 1: #if the car is to be added or its direction changes, update its info
                x[(cid[lineno]-1)] = curx[lineno]
                y[(cid[lineno]-1)] = cury[lineno]
                targetx[(cid[lineno]-1)] = finx[lineno] #where the car wants to go
                targety[(cid[lineno]-1)] = finy[lineno]
                startingx[(cid[lineno]-1)] = curx[lineno] #where it started
                startingy[(cid[lineno]-1)] = cury[lineno]
                timetotarget[(cid[lineno]-1)] = elapsed[lineno] #how long it takes
                startingtime[(cid[lineno]-1)] = ti

            lineno += 1

        #checks the times for changes that occur at that time
        #lines correspond to changes in that time, cid[lineno] is the car
        #in question in that line

        #array goes from 0 to v-1
        #car ids go from 1 to v, need to offset by one to compensate

        # -------------------------------------------------------------------- #
        # Set inactive cars to -9999
        # -------------------------------------------------------------------- #

        if ti >= 0:
            for c in range(v): #All inactive cars get moved to the dead zone
                if isactive[c] == 0:
                    x[c] = -9999
                    y[c] = -9999
                    targetx[c] = -9999
                    targety[c] = -9999
                    startingx[c] = -9999
                    startingy[c] = -9999

        # -------------------------------------------------------------------- #
        # Step 2.a. Vehicle movements
        # -------------------------------------------------------------------- #

        carsonroad = 0
        for vi in range(v):
            if x[vi] > -9999:
                carsonroad += 1 #counts active carsS

        #/PD

        #print "carsonroad", carsonroad, "t=", ti
        
        for vi in range(v):
            new_group_leader = 0
            xprior[vi] = x[vi]
            yprior[vi] = y[vi]

            #increment by time step - PD
            if x[vi] > -9999: #off cars shouldn't move, t0 places them all, not moves
            #that's how it appears in the original sim, anyway
                
                #we need to check if the car has stopped or disappeared
                #this will occur if the car reached or overstepped its bounds
                #if it is referenced again in the file, it is still active
                #otherwise, it goes away

                #vars which count which direction it moves
                isleft = 0
                isup = 0
                
                isdone = 0 #any more moves to make?

                overlr = 0 #made it to destination on each axis?
                overud = 0
                
                #isleft = 1 for left, 0 for right, isup = 1 for up, 0 for down

                #direction determination
                if targetx[vi] - startingx[vi] < 0:
                    isleft = 1
                if targety[vi] - startingy[vi] < 0:
                    isup = 1

                #determination if complete in those directions
                if ((float(x[vi]) <= float(targetx[vi]) and isleft == 1) or (float(x[vi]) >= float(targetx[vi]) and isleft == 0)):
                    overlr = 1 
                if ((float(y[vi]) <= float(targety[vi]) and isup == 1) or (float(y[vi]) >= float(targety[vi]) and isup == 0)):
                    overud = 1

                if overlr == 1 and overud == 1:
                    #check if there are still moves left for this guy
                    #targets would have been set for this time range, so
                    #we can look after lineno to the end of the file
                    #if found, set starting and target to this spot (waiting)
                    #else, zero it out
                    hasmove = 0
                    linecheck = lineno
                    while linecheck < maxlines and hasmove == 0:
                        if vi == cid[linecheck]-1: #if there is another move, car is waiting
                            hasmove = 1
                            targetx[vi] = x[vi]
                            targety[vi] = y[vi]
                        else:
                            linecheck += 1

                    if hasmove == 0: # if no move, kick the vehicle out
                        x[vi] = -9999
                        y[vi] = -9999
                        targetx[vi] = -9999
                        targety[vi] = -9999
                        startingx[vi] = -9999
                        startingy[vi] = -9999
                    else: #keep it going otherwise
                        targetx[vi] = x[vi]
                        targety[vi] = y[vi]
                        startingx[vi] = x[vi]
                        startingy[vi] = y[vi]                       

                #move normally (check for if it was moved)
                if x[vi] >= 0 and y[vi] >= 0 and x[vi] <= xmax and y[vi] <= ymax and ti != 0:
                    x[vi] = x[vi] + ((targetx[vi] - startingx[vi])/timetotarget[vi])
                    y[vi] = y[vi] + ((targety[vi] - startingy[vi])/timetotarget[vi])

                #if out of bounds, take completely off the map
                #not using <= and the like anymore, top section should catch it    
                if x[vi] < 0 or y[vi] < 0 or x[vi] > xmax or y[vi] > ymax:
                    x[vi] = -9999
                    y[vi] = -9999
                    targetx[vi] = -9999
                    targety[vi] = -9999
                    startingx[vi] = -9999
                    startingy[vi] = -9999

                    #print "car left", vi
                    #carsonroad -= 1
                    #print "cars on road:", carsonroad
                    
                    #lose leader status (does this need to happen or is it intrinsic?
                    #probably not - once the car teleports in the cancel zone, nothing is in range anymore

                    #of note - if a car runs off its time but it is still on the map, it will keep going
                    #the good news is that this will only happen on a badly made trace

                    #/PD
                            
            # ---------------------------------------------------------------- #
            # Step 2.b. Group Leader updates - vehicles change group leaders
            # depending on transmission range (default comrange = 300m)
            # ---------------------------------------------------------------- #

            
            #cars that just went inactive need to have all of their followers
            #dropped if they were a leader
            if x[vi] == -9999:
                anonymity[vi] = 0
                parroted_id[vi] = -1
                for cars in range(v):
                    if leader[cars] == vi:
                        leader[cars] = -1
                        
            cur_dist = comrange + 1 # no distance set yet

            #We must be sure to leave "off" cars inactive

            if leader[vi] > -1 and x[vi] > -9999: # if this vehicle already has a group leader AND is active
                # check if group leader in still in communications range
                cur_dist = math.sqrt((x[leader[vi]]-x[vi])**2+(y[leader[vi]]-y[vi])**2)
                # if leader is still in commuications range, do nothing for this vi
                if cur_dist > comrange: # if group leader is out of range
                    anonymity[leader[vi]] -= 1 # decrement anonymity set for leader
                    leader[vi] = -1 # establish that vi has no leader
                    anonymity[vi] = 0
                    if spcp == 1:
                        g_timeout[vi] = 1+random.randint(1,1000) # set group timeout for spcp
                    
            if leader[vi] == -1 and x[vi] > -9999: # if vi has no leader AND is active
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
                if leader[vi] == vi and x[vi] > -9999: # if vi has no leader AND is active
                    g_timeout[vi] -= g_timeout[vi] # set group timeout
                    if g_timeout < 0:
                        print ("error: negative g_timeout")
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
            if x[vi] > -9999: #only need to parrot if on map
                for pi in range (v): # search all vehicles
                    if leader[pi] == leader[vi]:       # find vehicle in same group, if active
                        if pi != vi:                   # but not self same vehicle
                            if parrotee[pi] == 1:      # pi wants a parrot
                                if parroter[vi] == 1:  # vi wants to be a parrot
                                    if parroted_id[vi] == -1: # no parrot set yet
                                        #print (vi, "parrots for", pi)
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
            if x[vi] > -9999 and ti >= time_start and ti < time_end: #only if car is active and in recoding times

                entropy = entropy + math.log(anonymity[vi]+p_anonymity[vi],2) # see eq p.101
                if anonymity[vi] + p_anonymity[vi] == 1: # as1 ia number of cars with as=1
                   as1 = as1 + 1
                cum_anonymity += anonymity[vi]    # add this vi's A. S. to the total A. S.
                cum_parrotees += parrotee[vi]
                cum_parroters += parroter[vi]
                cum_p_anonymity += p_anonymity[vi]
                if parroted_id[vi] > -1:
                    parrot_counter += 1

            #now only iterates in the specified time frame

            
        #if ti == time_end - 1:                # on last iteration print output
        if ((ti+1) % 100) == 0: #print every 100 time steps (PD)
            print ("t, v, pep, prp, sum(pe), sum(pr), sum(pas), count(pas), ts, count(as1), ent, active cars, as1/v, ent/v, sum(as), as/v")
            print ("time:", ti)
            ret_list = list()
            ret_list.append(t)                # total time slices
            ret_list.append(v)                # total vehicles  
            ret_list.append(parrotee_percent) # PEP: parrotee percent
            ret_list.append(parroter_percent) # PRP: parroter percent
            ret_list.append(cum_parrotees)    # sum(PR): number of potetial parrotees
            ret_list.append(cum_parroters)    # sum(PR): number of potetial parroters
            ret_list.append(cum_p_anonymity)  # sum(PAS): sum of AS's of active parroters
            ret_list.append(parrot_counter)   # count(PAS): number of active parroters
            ret_list.append(time.clock())     # timestamp
            ret_list.append(as1)              # count of vehicles with as size = 1
            ret_list.append(entropy)          # total entropy 

            #need to count active cars - PD
            carcounter = 0
            for vi in range(v):
                if x[vi] > -9999:
                    carcounter += 1

            #carcounter = min(carcounter,max_count) #if we were limited, use the limited value
                    
            ret_list.append(carcounter)                                 # active cars at last time step
            ret_list.append(as1 / carcounter)                           # tracking probability
            ret_list.append(entropy / carcounter)                       # entropy
            ret_list.append(cum_anonymity)                              # sum(AS): sum of all anonymity set values
            ret_list.append(float(cum_anonymity+cum_p_anonymity) / float(carcounter))   # average AS size

            print (ret_list)
            
            #last 5 are the critical stats
            #/PD

        print ("TIME" , ti, "COMPLETE")

        #Prints every car if you want that - PD
        #print ("t, car, x[car], y[car], vx[car], vy[car]")
        #car = 0
        #while car < v:
        #    if x[car] > -9999: #might want to change this baack for the real deal
        #        print (ti, car, x[car], y[car], ((targetx[car] - startingx[car])/timetotarget[car]), (targety[car] - startingy[car])/timetotarget[car])
        #        print (leader[car], anonymity[vi], p_anonymity[vi], parroter[car], parrotee[car])

        #    car = car + 1
               
    return ret_list # end of Section 2

# ----------------------------------------------------------------------------- #
#   Main
# ----------------------------------------------------------------------------- #
print (MODEL(0,0,0,2000,300,6762))
#parrotee_percent, parroter_percent, time_start, time_end, com_range, seed
#defaults, at least for us, to 0,0,0,2000,300,9999
#keep in mind, times go from 0 to t (2000) - 1

