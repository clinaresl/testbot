#!/usr/bin/gnuplot

# this script produces various figures with demographic data of
# european countries. The first file contains information about
# countries with more than 40 million inhabitants; the second one
# considers countries with less than 10 million inhabitants

# FIRST MULTIPLOT
# =============================================================================

# set the terminal type and the output file
set terminal png
set output "population-large.png"

# get ready to create a multi-plot
set multiplot title "Demographic data of European Countries" layout 1, 2 scale 0.9, 1.0

# First plot
# -----------------------------------------------------------------------------

# set data relative to the canvas
set auto x
set yrange [0:150]
set grid y

# set the xtics aspect and the location of the legends
set xtics font "Arial, 8"
set xtic rotate by -45 scale 0
set key under right nobox font "Arial, 8"

# set style of data
set style data histogram
set style histogram cluster gap 1
set style fill solid border -1
set boxwidth 0.9

# note that in the following picture:
#
# 1. We are just retrieving info from a few countries (those whose
#    population exceeds 40 Million). This is one of the advantages of
#    using sqlite3: it is feasible to focus on specific groups of data
#
# 2. The sql statement retrieves a whole row from data_all which is
#    known to have 5 items. Gnuplot automatically selects those of
#    interest to appear on the picture
plot "< sqlite3 ./population.db 'select * from data_all where data_all.population > 40' --separator ' '" using 2:xtic(1) ti 'Population (in Millions)', '' u 3 ti 'Birth rate (per 1,000)', '' u 4 ti 'Deaths (per 1,000)'

# Second plot
# -----------------------------------------------------------------------------

# set data relative to the canvas
set auto x
set yrange [-0.5:1.2]
set grid y

# set the xtics aspect and the location of the legends
set xtics font "Arial, 8"
set xtic rotate by -45 scale 0
set key under right nobox font "Arial, 8"

# set style of data
set style data linespoints

plot "< sqlite3 ./population.db 'select * from data_all where data_all.population > 40' --separator ' '" using 5:xtic(1) ti 'Rate of natural increase'


# exit from multiplot mode
unset multiplot


# SECOND MULTIPLOT
# =============================================================================

# set the terminal type and the output file
set terminal png
set output "population-short.png"

# get ready to create a multi-plot
set multiplot title "Demographic data of European Countries" layout 1, 2 scale 0.9, 1.0

# First plot
# -----------------------------------------------------------------------------

# set data relative to the canvas
set auto x
set yrange [0:20]
set grid y

# set the xtics aspect and the location of the legends
set xtics font "Arial, 8"
set xtic rotate by -45 scale 0
set key under right nobox font "Arial, 8"

# set style of data
set style data histogram
set style histogram cluster gap 1
set style fill solid border -1
set boxwidth 0.9

# note that in the following picture:
#
# 1. We are just retrieving info from a few countries (those whose
#    population exceeds 40 Million). This is one of the advantages of
#    using sqlite3: it is feasible to focus on specific groups of data
#
# 2. The sql statement retrieves a whole row from data_all which is
#    known to have 5 items. Gnuplot automatically selects those of
#    interest to appear on the picture
plot "< sqlite3 ./population.db 'select * from data_all where data_all.population < 2' --separator ' '" using 2:xtic(1) ti 'Population (in Millions)', '' u 3 ti 'Birth rate (per 1,000)', '' u 4 ti 'Deaths (per 1,000)'

# Second plot
# -----------------------------------------------------------------------------

# set data relative to the canvas
set auto x
set yrange [-0.5:1.2]
set grid y

# set the xtics aspect and the location of the legends
set xtics font "Arial, 8"
set xtic rotate by -45 scale 0
set key under right nobox font "Arial, 8"

# set style of data
set style data linespoints

plot "< sqlite3 ./population.db 'select * from data_all where data_all.population < 2' --separator ' '" using 5:xtic(1) ti 'Rate of natural increase'


# exit from multiplot mode
unset multiplot
