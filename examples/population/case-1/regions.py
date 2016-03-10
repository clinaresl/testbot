# imports
# -----------------------------------------------------------------------------
import math                             # floor and ceil

# global variables
# -----------------------------------------------------------------------------
northernEurope = ['Channel-Islands', 'Denmark', 'Estonia'       , 'Finland',
                  'Iceland'        , 'Ireland', 'Latvia'        ,  'Lithuania',
                  'Norway'         , 'Sweden' , 'United-Kingdom']

westernEurope = ['Austria'      , 'Belgium'   , 'France', 'Germany'    ,
                 'Liechtenstein', 'Luxembourg', 'Monaco', 'Netherlands',
                 'Switzerland']

easternEurope = ['Belarus' , 'Bulgaria', 'Czech-Republic', 'Hungary',
                 'Moldova' , 'Poland'  , 'Romania'       , 'Russia',
                 'Slovakia', 'Ukraine']

southernEurope = ['Albania', 'Andorra'   , 'Bosnia-Herzegovina', 'Croatia'   ,
                  'Greece' , 'Italy'     , 'Kosovo'            , 'Macedonia' ,
                  'Malta'  , 'Montenegro', 'Portugal'          , 'San-Marino',
                  'Serbia' , 'Slovenia'  , 'Spain']

# create a global list that stores at different locations the
# accumulated population of each region
rpopulation = [0]*4

# computes the percentile (specified as a value p between 0 and 1) of
# a list of numbers in L which has to be previously sorted
# -----------------------------------------------------------------------------
def percentile(L, p):
    """
    computes the percentile (specified as a value p between 0 and 1) of
    a list of numbers in L which has to be previously sorted
    """

    # in case the given list is empty, return None
    if not L:
        return None

    # compute the position in the list corresponding to the percentile
    # p
    k = (len(L)-1) * p
    f = math.floor(k)
    c = math.ceil(k)

    # in case it falls over an existing item, return it
    if f == c:
        return L[int(k)]

    # otherwise, interpolate between the floor and ceil
    d0 = L[int(f)] * (c-k)
    d1 = L[int(c)] * (k-f)

    # and return the value computed so far
    return d0+d1

# -----------------------------------------------------------------------------
if __name__ == '__builtin__':

    # welcome message - it is placed here just to show that snippets can
    # produce side effects if needed
    print " --- Talking from a snippet --------------------------------------------"

    # compute the population of every region and store it in a separate
    # list. All lists are stored together in another list called 'regions'
    regions = [[], [], [], []]
    for index, country in zip(range(0, len(countries)), countries):

        # autobot guarantees that items are given in the same order they
        # are matched. We exploit here this fact by adding the i-th item
        # in the population whose corresponding country is the i-th item
        # in countries
        if country in northernEurope:
            regions[0].append(population [index])
        elif country in westernEurope:
            regions[1].append(population[index])
        elif country in easternEurope:
            regions[2].append(population[index])
        elif country in southernEurope:
            regions[3].append(population[index])
        else:
            raise ValueError(" Unknown country '%s'" % country)

    # now, sort all lists
    for index in range(0, len(regions)):
        regions[index] = sorted(regions[index])

    # and now, compute different statistics:
    #
    #    acc: accumulated population within the same region
    #    min, max: minimum/maximum population in the same region
    #    median: median of the population in the same region
    #    p25, p75: 0.25/0.75 percentiles in the same region
    acc     = list()
    minimum = list()
    maximum = list()
    median  = list()
    p25     = list()
    p75     = list()
    for region in regions:
        acc.append(reduce(lambda x,y:x+y, region))
        minimum.append(min(region))
        maximum.append(max(region))
        median.append(percentile(region, 0.5))
        p25.append(percentile(region, 0.25))
        p75.append(percentile(region, 0.75))

    # Return also a list with the regions processed so far
    names = ['Northern Europe', 'Western Europe', 'Eastern Europe', 'Southern Europe']


if __name__ == '__main__':

    print "\n Warning - I'm just a snippet of Python code to be executed from 'autobot'\n"
    

# Local Variables:
# mode:python
# fill-column:80
# End:
