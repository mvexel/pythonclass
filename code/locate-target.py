import csv
import requests
from bs4 import BeautifulSoup as bs
import states
import os
import sys

# set the data path relative to the script
datapath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# initialize the lists and variables we will use
gnisnames = []
statecnt = 0
totalcnt = 0
totalmatchcnt = 0

# PART 1: Load GNIS populated places
# ----------------------------------
print 'loading GNIS data...'
with open(os.path.join(datapath, 'POP_PLACES_20121001.txt'), 'r') as gnisfile:
    gnisreader = csv.reader(gnisfile,  delimiter='|')
    for row in gnisreader:
        gnisnames.append(row)
print 'done. %i GNIS populated places in memory.' % (len(gnisnames))

# PART 2: Get locations state by state and match
# ----------------------------------------------

# Open file to write Target locations to
csvwriter = csv.writer(open(os.path.join(datapath, 'target.csv'), 'wb'))
csvwriter.writerow(('placename','statecode','lat','lon'))

# Iterate over all states
for code, state in sorted(states.states.iteritems()):
    # reset counters and coordinate
    cnt = 0
    matchcnt = 0
    print 'getting Target locations for %s...' % state
    # fire the Target store locator request for one state
    # URL format is http://www.target.com/store-locator/state-result?stateCode=UT
    payload = {'stateCode':code}
#    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4'}
    r = requests.get('http://www.target.com/store-locator/state-result', params=payload)
    # check for valid (200) response
    if r.status_code <> 200:
        print 'we did not get a valid response...'
        print r.text
        r.raise_for_status()
    print 'parsing Target locations for %s...' %  state
    # load the mess into BeautifulSoup
    soup = bs(r.text)
    # find the table element (and children) on the page and store in a soup
    table = soup.find('table')
    # get all table rows and store them in a list
    rows = table.find_all('tr')
    # iterate over all the table rows
    for row in rows:
        lat = -9999 # nodata value
        lon = -9999 # nodata value
        # get all table cells in this row and store them in a list
        cols = row.find_all('td')
        # check that we're dealing with a content row which in the case of Target has 7 columns
        if len(cols) == 7:
            # the data we want (the place name) is in the fourth column
            cell = cols[3]
            # The data is in the form 'Salt Lake City, UT 84113. We want only the part before the comma.
            placename = cell.string.split(',')[0]
            # store the found placename and the state code in a record list.
            record = [placename, code]
            # match the place, state combo with what we have in the gnis dictionary.
            gnismatches = [m for m in gnisnames if (m[3].upper() == code.upper() and m[1].upper() == placename.upper())]
            # if there's a match, get the coordinates from the GNIS directory
            if len(gnismatches):
                # lat and lon are in the 10th and 11th columns, see http://geonames.usgs.gov/domestic/states_fileformat.htm
                lat = gnismatches[0][9]
                lon = gnismatches[0][10]
                # increase the match counter
                matchcnt += 1
            # add the found (or nodata if we didn't find a match) coordinate to the record
            record += (lat,lon)
            cnt += 1
            sys.stdout.write('%i matches /%i total (%.1f%% success)\r' % (matchcnt, cnt, (float(matchcnt) / float(cnt))*100))
            # ..and also write these to our file
            csvwriter.writerow(record)
    print 'found %i Target locations for %s, %i matched with GNIS names' % (cnt, state, matchcnt)
    totalcnt += cnt
    totalmatchcnt += matchcnt
    statecnt += 1
print 'done. %i states scraped, %i total Target locations found, %i matched to GNIS populated place.' % (statecnt, totalcnt, totalmatchcnt)
