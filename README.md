parrots-and-things
==================

Created to store information in regards to the PARROTS group of the 2013 UnCoRe REU.

Updated when new research is desired.

Different functions made in different files to facilitate easier testing in multiple machines.

==================

Code and functions thereof:

In 1st Round:

fullcarsim.py - runs using trace data, which can be replaced in the "f = open('rural.csv', 'r')" line with the name of the file.
Timestart and timeend should be left at 0 and 2000 to track for all times.
com_range is usually 300.
parrotee_percent and parroter_percent can add parroting

parrots - uses time, car, and parroting percentages

In 2nd Round:

parrots.py - exactly the same as parrots.py in /project (for python 3) (7-12 2nd fix)

expparrots.py - runs with the same parameters as parrots.py, but the roads are distributed exponentially:
roads gradually become further spaced out throughout the 3000x3000 area

parrots - replace.py - runs with the same parameters as parrots.py, but cars that reach the end of the map are cleared
and replaced with new cars starting at random locations.

expparrots - replace.py - runs with the same parameters as expparrots.py, but cars that reach the end of the map are cleared
and replaced with new cars starting at random locations.

parrots - multiparrots.py - runs with the same parameters as parrots.py, but a parrot can parrot two pirates

expparrots - multiparrots.py - runs with the same parameters as expparrots.py, but a parrot can parrot two pirates

parrots - piratesets.py - tracks the average set size of pirates

expparrots - piratesets.py - tracks the average set size of pirates
