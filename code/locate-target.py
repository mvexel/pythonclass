import csv
import requests
from bs4 import BeautifulSoup as bs
import re 
import states
import os
import sys

datapath = 'c:\\Users\\mvexel\\class\\data\\'
gnisnames = []
ponames = []
statecnt = 0
totalcnt = 0
totalmatchcnt = 0

# PART 1: Load GNIS populated places
with open(os.path.join(datapath, 'POP_PLACES_20121001.txt'), 'r') as gnisfile:
    gnisreader = csv.reader(gnisfile,  delimiter='|')
    for row in gnisreader:
        gnisnames.append(row)
        
print len(gnisnames)

# PART 2: Get PO locations state by state and match

# Open file to write Target locations to
csvwriter = csv.writer(open(os.path.join(datapath, 'target.csv'), 'wb'))
csvwriter.writerow(('placename','statecode','lat','lon'))

# Iterate over all states
for code, state in sorted(states.states.iteritems()):
    # reset counters and coordinate
    cnt = 0
    matchcnt = 0
    lat = 0
    lon = 0
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
    # find all table cells that have store locations
    table = soup.find('table')
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        if len(cols) == 7:
            cell = cols[3]
            # Add place name string and state code to the names array
            placename = cell.string.split(',')[0]
            record = [placename, code]
            # match with gnis
            gnismatches = [m for m in gnisnames if (m[3].upper() == code.upper() and m[1].upper() == placename.upper())]
            if len(gnismatches):
                lat = gnismatches[0][9]
                lon = gnismatches[0][10]
                matchcnt += 1
            record += (lat,lon)
            ponames.append(record)
            cnt += 1
            sys.stdout.write('%i matches /%i total (%.1f%% success)\r' % (matchcnt, cnt, (float(matchcnt) / float(cnt))*100))
            # ..and also write these to our file
            csvwriter.writerow(record)
    print 'found %i Target locations for %s, %i matched with GNIS names' % (cnt, state, matchcnt)
    totalcnt += cnt
    totalmatchcnt += matchcnt
    statecnt += 1
print 'done. %i states scraped, %i total Target locations found, %i matched to GNIS populated place.' % (statecnt, totalcnt, totalmatchcnt)