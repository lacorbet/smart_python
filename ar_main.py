'''
    Solar Monitor Active Region Tracker
    ===================================
    Written by Sophie A. Murray, code originally developed by Paul Higgins (IDL SMART wrapper).
    - Code translated line-by-line and operates as close to IDL code as possible.

    Developed under Python 3 and Sunpy 0.8.3
    - Python 3.6.1 |Anaconda custom (x86_64)| (default, May 11 2017, 13:04:09)

    Steps:
    - Read HMI magnetogram and process it
    - Find 'magnetically interesting regions' and calculate properties of interest
    - Track regions from previous six hours
    - Visualise output for SolarMonitor.org

    Notes:
    - need to finish deprojection code in ar_pslprop.py
'''


from ar_readmag import ar_readmag
from ar_processmag import ar_processmag
from ar_detect import ar_detect
from ar_detect_core import ar_detect_core
from ar_posprop import ar_posprop
from ar_magprop import ar_magprop
from ar_pslprop import ar_pslprop
import astropy.units as u
import sunpy.map
import matplotlib.pylab as plt
import pandas as pd
import datetime
import numpy as np
import json
import time

if __name__ == "__main__":
    # First load the latest HMI data file
    start_time = time.time()
#    thismap, data_dir = ar_readmag()
    # Currently manually loading for testing purposes, rather than using automatic scraping code above.
    print('Loading fits file')
    data_dir = '/Users/sophie/Dropbox/'#'/Users/sophie/data/smart/'
    thismap = sunpy.map.Map(data_dir + 'latest.fits')

    # Need to downsample if 4096x4096
    # (generally shouldnt be if using near-real-time JSOC data)
    if thismap.meta['naxis1'] == 4096:
        thismap = thismap.resample(u.Quantity([1024, 1024], u.pixel))
        thismap.meta['naxis1'] = 1024
        thismap.meta['naxis2'] = 1024

    # Rotate map if necessary
    if (thismap.meta['crota2'] >= 100.):
        data = np.flip(inmap.data, 1)[::-1]
        inmap = sunpy.map.Map(data, inmap.meta)
        inmap.meta['crota2'] = 0.

    # Now process magnetogram
    print('Processing data')
    magproc, cosmap, limbmask = ar_processmag(thismap, medianfilter=False)

    # Create AR masks
    print('Making core detections')
    thissm = ar_detect(magproc, limbmask)
    thisar, pslmap = ar_detect_core(magproc, thissm.data)
    print('SMART detections found: ', np.max(np.unique(thisar.data)))

    # Get properties
    print('Calculating properties')
    posprop = ar_posprop(magproc, thisar.data, cosmap)
    magprop = ar_magprop(magproc, thisar.data, cosmap)
    pslprop = ar_pslprop(magproc, thisar.data, doproj=False, projmaxscale=1024)

    # Output to json
    smartdate = thismap.date.strftime('%Y%m%d_%H%M')
    out = {'meta': {'dateobs': smartdate,
                    'dimension': thismap.dimensions[0].value,
                    'instrument': thismap.instrument}}
    out['posprop'] = posprop
    out['magprop'] = magprop
    out['pslprop'] = pslprop
    out = pd.io.json.dumps(out, data_dir+smartdate+'_properties.json')
    with open(data_dir+smartdate+'_properties.json', 'w') as outfile:
        outfile.write(out)
    # Beautifying it
    with open(data_dir+smartdate+'_properties.json') as infile:
        obj = json.load(infile)
    with open(data_dir+smartdate+'_properties.json', 'w') as outfile:
        json.dump(obj, outfile,
                  sort_keys=True,
                  indent=4, separators=(',', ': '))

    # Visualise
    thismap.plot(vmin=-500, vmax=500)
    thismap.draw_limb()
    plt.colorbar(label='B [G]')
    plt.contour(pslmap.data, origin='lower',
                colors='yellow', linewidths=0.5,
                vmin=0., vmax=np.max(np.unique(thisar.data))+1)
    plt.contour(thisar.data>0., origin='lower',
                colors='blue', linewidths=1.0,
                vmin=0., vmax=np.max(np.unique(thisar.data))+1)
#    thismap.draw_grid(grid_spacing=10 * u.deg)
    plt.savefig(data_dir+smartdate+'_detections.eps')

    # How long did that take?
    print('Runtime:', round(time.time() - start_time),'seconds')

# ======================================
# Some IDL fits files used for testing:
#    thismap_idl = sunpy.map.Map('/Users/sophie/data/smart/latest.fits')
#    magproc_idl = sunpy.map.Map('magproc.fits')
#    thissm_idl = sunpy.map.Map('thissm.fits')
#    thisar_idl = sunpy.map.Map('thisar.fits')
#    thismaskmap_idl = sunpy.map.Map('thismaskmap.fits')
#    thismask_idl = thismaskmap_idl.data
#'/Users/sophie/sunpy/data/hmi_m_45s_2011_10_17_00_01_30_tai_magnetogram.fits'
#'/Users/sophie/Downloads/hmi.M_720s.20140921_120000_TAI.fits'
