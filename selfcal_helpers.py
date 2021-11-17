import numpy as np
import numpy 
import math
def tclean_wrapper(vis, imagename, scales,telescope='undefined', smallscalebias = 0.6, mask = '', nsigma=5.0, imsize = None, cellsize = None, interactive = False, robust = 0.5, gain = 0.1, niter = 50000, cycleniter = 300, uvtaper = [], savemodel = 'none', sidelobethreshold=3.0,smoothfactor=1.0,noisethreshold=5.0,lownoisethreshold=1.5,parallel=False,nterms=1,
cyclefactor=3,uvrange='',threshold='0.0Jy',phasecenter='',startmodel='',pblimit=0.1,pbmask=0.1,field='',datacolumn='',spw=''):
    """
    Wrapper for tclean with keywords set to values desired for the Large Program imaging
    See the CASA 6.1.1 documentation for tclean to get the definitions of all the parameters
    """
    if mask == '':
       usemask='auto-multithresh'
    else:
       usemask='user'
    if threshold != '0.0Jy':
       nsigma=0.0
    if telescope=='ALMA':
       sidelobethreshold=3.0
       smoothfactor=1.0
       noisethreshold=5.0
       lownoisethreshold=1.5
       nsigma=0.0
    elif 'VLA' in telescope:
       sidelobethreshold=2.0
       smoothfactor=1.0
       noisethreshold=5.0
       lownoisethreshold=1.5    
       threshold = '0.0Jy'
    for ext in ['.image*', '.mask', '.model*', '.pb*', '.psf*', '.residual*', '.sumwt*','.gridwt*']:
        os.system('rm -rf '+ imagename + ext)
    tclean(vis= vis, 
           imagename = imagename, 
           field=field,
           specmode = 'mfs', 
           deconvolver = 'mtmfs',
           scales = scales, 
           weighting='briggs', 
           robust = robust,
           gain = gain,
           imsize = imsize,
           cell = cellsize, 
           smallscalebias = smallscalebias, #set to CASA's default of 0.6 unless manually changed
           niter = niter, #we want to end on the threshold
           interactive = interactive,
           nsigma=nsigma,    
           cycleniter = cycleniter,
           cyclefactor = cyclefactor, 
           uvtaper = uvtaper, 
           savemodel = 'none',
           mask=mask,
           usemask=usemask,
           sidelobethreshold=sidelobethreshold,
           smoothfactor=smoothfactor,
           pbmask=pbmask,
           pblimit=pblimit,
           nterms = nterms,
           uvrange=uvrange,
           threshold=threshold,
           parallel=parallel,
           phasecenter=phasecenter,
           startmodel=startmodel,
           datacolumn=datacolumn,spw=spw)
     #this step is a workaround a bug in tclean that doesn't always save the model during multiscale clean. See the "Known Issues" section for CASA 5.1.1 on NRAO's website
    if savemodel=='modelcolumn':
          print("")
          print("Running tclean a second time to save the model...")
          tclean(vis= vis, 
                 imagename = imagename, 
                 field=field,
                 specmode = 'mfs', 
                 deconvolver = 'mtmfs',
                 scales = scales, 
                 weighting='briggs', 
                 robust = robust,
                 gain = gain,
                 imsize = imsize,
                 cell = cellsize, 
                 smallscalebias = smallscalebias, #set to CASA's default of 0.6 unless manually changed
                 niter = 0, 
                 interactive = False,
                 nsigma=0.0, 
                 cycleniter = cycleniter,
                 cyclefactor = cyclefactor, 
                 uvtaper = uvtaper, 
                 usemask='user',
                 savemodel = savemodel,
                 sidelobethreshold=sidelobethreshold,
                 smoothfactor=smoothfactor,
                 pbmask=pbmask,
                 pblimit=pblimit,
                 calcres = False,
                 calcpsf = False,
                 nterms = nterms,
                 uvrange=uvrange,
                 threshold=threshold,
                 parallel=False,
                 phasecenter=phasecenter,spw=spw)
    

def fetch_scan_times(vislist,targets):
   listdict={}
   scantimesdict={}
   integrationsdict={}
   integrationtimesdict={}
   integrationtime=np.array([])
   n_spws=np.array([])
   min_spws=np.array([])
   spwslist=np.array([])
   for vis in vislist:
      listdict[vis]=listobs(vis)
      scantimesdict[vis]={}
      integrationsdict[vis]={}
      integrationtimesdict[vis]={}
      keylist=list(listdict[vis].keys())  
      for target in targets:
         countscans=0
         scantimes=np.array([])
         integrations=np.array([])
         for key in keylist:
            if 'scan' in key and listdict[vis][key]['0']['FieldName']==target:
               countscans+=1
               scantime=(listdict[vis][key]['0']['EndTime']- listdict[vis][key]['0']['BeginTime'])*86400.0
               ints_per_scan=np.round(scantime/listdict[vis][key]['0']['IntegrationTime'])
               integrationtime=np.append(integrationtime,np.array([listdict[vis][key]['0']['IntegrationTime']]))
               #print('Key:', key,scantime)
               scantimes=np.append(scantimes,np.array([scantime]))
               integrations=np.append(integrations,np.array([ints_per_scan]))
               n_spws=np.append(len(listdict[vis][key]['0']['SpwIds']),n_spws)
               min_spws=np.append(np.min(listdict[vis][key]['0']['SpwIds']),min_spws)
               spwslist=np.append(listdict[vis][key]['0']['SpwIds'],spwslist)
               #print(scantimes)

         scantimesdict[vis][target]=scantimes.copy()
         #assume each band only has a single integration time
         integrationtimesdict[vis][target]=np.median(integrationtime)
         integrationsdict[vis][target]=integrations.copy()
   if np.mean(n_spws) != np.max(n_spws):
      print('WARNING, INCONSISTENT NUMBER OF SPWS IN SCANS/MSes')
   if np.max(min_spws) != np.min(min_spws):
      print('WARNING, INCONSISTENT MINIMUM SPW IN SCANS/MSes')
   spwslist=np.unique(spwslist).astype(int)
   return listdict,scantimesdict,integrationsdict,integrationtimesdict, integrationtime,np.max(n_spws),np.min(min_spws),spwslist

def fetch_scan_times_band_aware(vislist,targets,band_properties,band):
   listdict={}
   scantimesdict={}
   integrationsdict={}
   integrationtimesdict={}
   integrationtime=np.array([])
   n_spws=np.array([])
   min_spws=np.array([])
   spwslist=np.array([])
   for vis in vislist:
      listdict[vis]=listobs(vis)
      scantimesdict[vis]={}
      integrationsdict[vis]={}
      integrationtimesdict[vis]={}
      keylist=list(listdict[vis].keys())  
      for target in targets:
         countscans=0
         scantimes=np.array([])
         integrations=np.array([])
         for key in keylist:
            if ('scan' in key) and (listdict[vis][key]['0']['FieldName']==target) and np.all(listdict[vis][key]['0']['SpwIds']==band_properties[vis][band]['spwarray']):
               countscans+=1
               scantime=(listdict[vis][key]['0']['EndTime']- listdict[vis][key]['0']['BeginTime'])*86400.0
               ints_per_scan=np.round(scantime/listdict[vis][key]['0']['IntegrationTime'])
               integrationtime=np.append(integrationtime,np.array([listdict[vis][key]['0']['IntegrationTime']]))
               #print('Key:', key,scantime)
               scantimes=np.append(scantimes,np.array([scantime]))
               integrations=np.append(integrations,np.array([ints_per_scan]))
               n_spws=np.append(len(listdict[vis][key]['0']['SpwIds']),n_spws)
               min_spws=np.append(np.min(listdict[vis][key]['0']['SpwIds']),min_spws)
               spwslist=np.append(listdict[vis][key]['0']['SpwIds'],spwslist)
               #print(scantimes)

         scantimesdict[vis][target]=scantimes.copy()
         #assume each band only has a single integration time
         integrationtimesdict[vis][target]=np.median(integrationtime)
         integrationsdict[vis][target]=integrations.copy()
   if np.mean(n_spws) != np.max(n_spws):
      print('WARNING, INCONSISTENT NUMBER OF SPWS IN SCANS/MSes')
   if np.max(min_spws) != np.min(min_spws):
      print('WARNING, INCONSISTENT MINIMUM SPW IN SCANS/MSes')
   spwslist=np.unique(spwslist).astype(int)
   return listdict,scantimesdict,integrationsdict,integrationtimesdict, integrationtime,np.max(n_spws),np.min(min_spws),spwslist


def fetch_spws(vislist,targets):
   listdict={}
   scantimesdict={}
   n_spws=np.array([])
   min_spws=np.array([])
   spwslist=np.array([])
   for vis in vislist:
      listdict[vis]=listobs(vis)
      keylist=list(listdict[vis].keys())  
      for target in targets:
         countscans=0
         for key in keylist:
            if 'scan' in key and listdict[vis][key]['0']['FieldName']==target:
               countscans+=1
               n_spws=np.append(len(listdict[vis][key]['0']['SpwIds']),n_spws)
               min_spws=np.append(np.min(listdict[vis][key]['0']['SpwIds']),min_spws)
               spwslist=np.append(listdict[vis][key]['0']['SpwIds'],spwslist)
               #print(scantimes)
   if len(n_spws) > 1:
      if np.mean(n_spws) != np.max(n_spws):
         print('WARNING, INCONSISTENT NUMBER OF SPWS IN SCANS/MSes')
      if np.max(min_spws) != np.min(min_spws):
         print('WARNING, INCONSISTENT MINIMUM SPW IN SCANS/MSes')
   spwslist=np.unique(spwslist).astype(int)
   if len(n_spws) == 1:
      return listdict,n_spws,min_spws,spwslist
   else:
      return listdict,np.max(n_spws),np.min(min_spws),spwslist


def fetch_scan_times_target(vislist,target):
   listdict={}
   scantimesdict={}
   integrationsdict={}
   integrationtimesdict={}
   integrationtime=np.array([])
   n_spws=np.array([])
   min_spws=np.array([])
   spwslist=np.array([])
   allscantimes=np.array([])
   for vis in vislist:
      listdict[vis]=listobs(vis)
      keylist=list(listdict[vis].keys())       
      countscans=0
      scantimes=np.array([])
      integrations=np.array([])
      for key in keylist:
         if 'scan' in key:
            if listdict[vis][key]['0']['FieldName'] == target:
               countscans+=1
               scantime=(listdict[vis][key]['0']['EndTime']- listdict[vis][key]['0']['BeginTime'])*86400.0
               scantimes=np.append(scantimes,np.array([scantime]))

      allscantimes=np.append(allscantimes,scantimes)

   return allscantimes


def get_common_intervals(vis,integrationsdict,integrationtime):
   allintegrations=np.array([])

   #for vis in vislist:
   allintegrations=np.append(allintegrations,integrationsdict)

   unique_integrations=np.unique(allintegrations)
   common_multiples=np.array([])
   common_multiple=True
   for i in range(1,int(np.max(unique_integrations))):
      for number in unique_integrations:
         multiple=number/i
         #print(multiple,number ,i,multiple.is_integer())
         if multiple.is_integer():
            common_multiple=True
         else:
            common_multiple=False
            break
      if common_multiple:
         common_multiples=np.append(common_multiples,np.array([i]))
      common_multiple=True
   solints=[]
   for multiple in common_multiples:
      solint='{:0.2f}s'.format(multiple*integrationtime)
      solints.append(solint)
   return common_multiples,solints


def get_solints_vla(vis,scantimesdict,integrationtime):
   allscantimes=np.array([])

   #for vis in vislist: # use if we put all scan times from all MSes into single array
   #mix of short and long baseline data could have differing integration times and hence solints
   allscantimes=np.append(allscantimes,scantimesdict)

   medianscantime=np.median(allscantimes)
   integrations_per_scan=np.round(medianscantime/integrationtime)
   non_integer_multiple=True
   i=0
   while non_integer_multiple:
      integrations_per_scan=integrations_per_scan+i
      integrations_per_scan_div4=integrations_per_scan/4.0
      print(integrations_per_scan,integrations_per_scan_div4,i)
      if integrations_per_scan_div4.is_integer():
         non_integer_multiple=False
         n_ints_increment=i
      else:
         i+=1

   max_integrations_per_sol=integrations_per_scan
   print('Max integrations per solution',max_integrations_per_sol,n_ints_increment)
   common_multiples=np.array([])

   for i in range(1,int(max_integrations_per_sol)):
         multiple=max_integrations_per_sol/i
         #print(multiple,number ,i,multiple.is_integer())
         if multiple.is_integer():
            common_multiple=True
         else:
            common_multiple=False
         if common_multiple:
            common_multiples=np.append(common_multiples,np.array([i]))

   solints=[]
   for multiple in common_multiples:
      solint='{:0.2f}s'.format(multiple*integrationtime)
      solints.append(solint)

   return solints

    


def get_solints_simple(vislist,scantimesdict,integrationtimes):
   all_integrations=np.array([])
   for vis in vislist:
      targets=integrationtimes[vis].keys()
      for target in targets:
         all_integrations=np.append(all_integrations,integrationtimes[vis][target])
   integration_time=np.max(all_integrations) # use the longest integration time from all MS files

   allscantimes=np.array([])
   for vis in vislist: # use if we put all scan times from all MSes into single array
      targets=scantimesdict[vis].keys()
      for target in targets:
         allscantimes=np.append(allscantimes,scantimesdict[vis][target])
      #mix of short and long baseline data could have differing integration times and hence solints

   max_scantime=np.median(allscantimes)
   median_scantime=np.max(allscantimes)
   min_scantime=np.min(allscantimes)
   
   solints=np.array([])
   solint=max_scantime/2.0
   n_scans=len(allscantimes)
   while solint > 1.90*integration_time:      #1.1*integration_time will ensure that a single int will not be returned such that solint='int' can be appended to the final list.
      ints_per_solint=solint/integration_time
      if ints_per_solint.is_integer():
         solint=solint
      else:
         remainder=ints_per_solint-float(int(ints_per_solint))     # calculate delta_T greater than an a fixed multile of integrations
         solint=solint-remainder*integration_time # add remainder to make solint a fixed number of integrations

      ints_per_solint=float(int(ints_per_solint))
      #print('Checking solint = ',ints_per_solint*integration_time)
      delta=test_truncated_scans(ints_per_solint, allscantimes,integration_time) 
      solint=(ints_per_solint+delta)*integration_time
      
      solints=np.append(solints,[solint])                       # add solint to list of solints now that it is an integer number of integrations
      solint = solint/2.0  
      #print('Next solint: ',solint)                                        #divide solint by 2.0 for next solint

   solints_list=[]
   for solint in solints:
      solint_string='{:0.2f}s'.format(solint)
      solints_list.append(solint_string)
   solints_list.insert(0,'inf')
   solints_list.append('int')
   return solints_list



def test_truncated_scans(ints_per_solint, allscantimes,integration_time ):
   delta_ints_per_solint=[0 , -1, 1,-2,2]
   n_truncated_scans=np.zeros(len(delta_ints_per_solint))
   n_remaining_ints=np.zeros(len(delta_ints_per_solint))
   min_index=0
   for i in range(len(delta_ints_per_solint)):
      diff_ints_per_scan=((allscantimes-((ints_per_solint+delta_ints_per_solint[i])*integration_time))/integration_time)+0.5
      diff_ints_per_scan=diff_ints_per_scan.astype(int)
      trimmed_scans=( (diff_ints_per_scan > 0.0)  & (diff_ints_per_scan < ints_per_solint+delta_ints_per_solint[i])).nonzero()
      if len(trimmed_scans[0]) >0:
         n_remaining_ints[i]=np.max(diff_ints_per_scan[trimmed_scans[0]])
      else:
         n_remaining_ints[i]=0.0
      #print((ints_per_solint+delta_ints_per_solint[i])*integration_time,ints_per_solint+delta_ints_per_solint[i],  diff_ints_per_scan)
      
      #print('Max ints remaining: ', n_remaining_ints[i])
      #print('N truncated scans: ', len(trimmed_scans[0]))
      n_truncated_scans[i]=len(trimmed_scans[0])
      # check if there are fewer truncated scans in the current trial and if
      # if one trial has more scans left off or fewer. Favor more left off, such that remainder might be able to 
      # find a solution
      # if ((i > 0) and (n_truncated_scans[i] <= n_truncated_scans[min_index]):   # if we don't care about the amount of 
      #if ((i > 0) and (n_truncated_scans[i] <= n_truncated_scans[min_index]) and (n_remaining_ints[i] > n_remaining_ints[min_index])):
      if ((i > 0) and (n_truncated_scans[i] <= n_truncated_scans[min_index]) and (n_remaining_ints[i] < n_remaining_ints[min_index])):
         min_index=i
      #print(delta_ints_per_solint[min_index])
   return delta_ints_per_solint[min_index]
   
def fetch_targets(vis):
      fields=[]
      listdict=listobs(vis)
      listobskeylist=listdict.keys()
      for listobskey in listobskeylist:
         if 'field_' in listobskey:
            fields.append(listdict[listobskey]['name'])
      return fields





def estimate_SNR(imagename):
    headerlist = imhead(imagename, mode = 'list')
    beammajor = headerlist['beammajor']['value']
    beamminor = headerlist['beamminor']['value']
    beampa = headerlist['beampa']['value']
    print("#%s" % imagename)
    print("#Beam %.3f arcsec x %.3f arcsec (%.2f deg)" % (beammajor, beamminor, beampa))
    image_stats= imstat(imagename = imagename)
    residual_stats=imstat(imagename=imagename.replace('image','residual'))
    peak_intensity = image_stats['max'][0]
    print("#Peak intensity of source: %.2f mJy/beam" % (peak_intensity*1000,))
    rms = residual_stats['rms'][0]
    print("#rms: %.2e mJy/beam" % (rms*1000,))
    SNR = peak_intensity/rms
    print("#Peak SNR: %.2f" % (SNR,))
    return SNR,rms


def get_n_ants(vislist):
   #Examines number of antennas in each ms file and returns the minimum number of antennas
   msmd = casatools.msmetadata()
   tb = casatools.table()
   n_ants=50.0
   for vis in vislist:
      msmd.open(vis)
      names = msmd.antennanames()
      msmd.close()
      n_ant_vis=len(names)
      if n_ant_vis < n_ants:
         n_ants=n_ant_vis
   return n_ants
    

def rank_refants(vis):
     # Get the antenna names and offsets.

     msmd = casatools.msmetadata()
     tb = casatools.table()

     msmd.open(vis)
     names = msmd.antennanames()
     offset = [msmd.antennaoffset(name) for name in names]
     msmd.close()

     # Calculate the mean longitude and latitude.

     mean_longitude = numpy.mean([offset[i]["longitude offset"]\
             ['value'] for i in range(len(names))])
     mean_latitude = numpy.mean([offset[i]["latitude offset"]\
             ['value'] for i in range(len(names))])

     # Calculate the offsets from the center.

     offsets = [numpy.sqrt((offset[i]["longitude offset"]['value'] -\
             mean_longitude)**2 + (offset[i]["latitude offset"]\
             ['value'] - mean_latitude)**2) for i in \
             range(len(names))]

     # Calculate the number of flags for each antenna.

     nflags = [tb.calc('[select from '+vis+' where ANTENNA1=='+\
             str(i)+' giving  [ntrue(FLAG)]]')['0'].sum() for i in \
             range(len(names))]

     # Calculate a score based on those two.

     score = [offsets[i] / max(offsets) + nflags[i] / max(nflags) \
             for i in range(len(names))]

     # Print out the antenna scores.

     print("Scores for "+vis)
     for i in numpy.argsort(score):
         print(names[i], score[i])

     # Return the antenna names sorted by score.

     return ','.join(numpy.array(names)[numpy.argsort(score)])


def get_SNR_self(all_targets,bands,vislist,selfcal_library,n_ant):
   for target in all_targets:
    for band in bands:
      SNR_self_EB=np.zeros(len(vislist))
      for i in range(len(vislist)):
         SNR_self_EB[i]=selfcal_library[target][band]['SNR_orig']/((n_ant)**0.5*(selfcal_library[target][band]['Total_TOS']/selfcal_library[target][band][vislist[i]]['TOS'])**0.5)
      selfcal_library[target][band]['per_EB_SNR']=np.mean(SNR_self_EB)
     
      selfcal_library[target][band]['per_scan_SNR']=selfcal_library[target][band]['SNR_orig']/((n_ant)**0.5*(selfcal_library[target][band]['Total_TOS']/selfcal_library[target][band]['Median_scan_time'])**0.5)


def get_sensitivity(vislist,specmode='mfs',spwstring='',spw=[],chan=0,cellsize='0.025arcsec',imsize=1600,robust=0.5,uvtaper=''):
   sensitivities=np.zeros(len(vislist))
   counter=0
   scalefactor=2.5
   for vis in vislist:
      im.open(vis)
      im.selectvis(field='',spw=spwstring)
      im.defineimage(mode=specmode,stokes='I',spw=spw,cellx=cellsize,celly=cellsize,nx=imsize,ny=imsize)  
      im.weight(type='briggs',robust=robust)  
      if uvtaper != '':
         if 'klambda' in uvtaper:
            uvtaper=uvtaper.replace('klambda','')
            uvtaperflt=float(uvtaper)
            bmaj=str(206.0/uvtaperflt)+'arcsec'
            bmin=bmaj
            bpa='0.0deg'
         if 'arcsec' in uvtaper:
            bmaj=uvtaper
            bmin=uvtaper
            bpa='0.0deg'
         print('uvtaper: '+bmaj+' '+bmin+' '+bpa)
         im.filter(type='gaussian', bmaj=bmaj, bmin=bmin, bpa=bpa)
      try:
          sens=im.apparentsens()
      except:
          print('#')
          print('# Sensisitivity Calculation failed for '+vis)
          print('# Continuing to next MS') 
          print('# Data in this spw/MS may be flagged')
          print('#')
          continue
      #print(vis,'Briggs Sensitivity = ', sens[1])
      #print(vis,'Relative to Natural Weighting = ', sens[2])  
      sensitivities[counter]=sens[1]*scalefactor
      counter+=1
   estsens=np.sum(sensitivities)/float(counter)/(float(counter))**0.5
   return estsens

def LSRKfreq_to_chan(msfile, field, spw, LSRKfreq,spwsarray):
    """
    Identifies the channel(s) corresponding to input LSRK frequencies. 
    Useful for choosing which channels to split out or flag if a line has been identified by the pipeline.

    Parameters
    ==========
    msfile: Name of measurement set (string)
    spw: Spectral window number (int)
    obsid: Observation ID corresponding to the selected spectral window 
    restfreq: Rest frequency in Hz (float)
    LSRKvelocity: input velocity in LSRK frame in km/s (float or array of floats)

    Returns
    =======
    Channel number most closely corresponding to input LSRK frequency.
    """
    tb.open(msfile)
    spw_col = tb.getcol('DATA_DESC_ID')
    obs_col = tb.getcol('OBSERVATION_ID')
    #work around the fact that spws in DATA_DESC_ID don't match listobs
    uniquespws=np.unique(spw_col)
    matching_index=np.where(spw==spwsarray)
    alt_spw=uniquespws[matching_index[0]]
    tb.close()
    obsid = np.unique(obs_col[np.where(spw_col==alt_spw)]) 
    
    tb.open(msfile+'/SPECTRAL_WINDOW')
    chanfreqs = tb.getcol('CHAN_FREQ', startrow = spw, nrow = 1)
    tb.close()
    tb.open(msfile+'/FIELD')
    fieldnames = tb.getcol('NAME')
    tb.close()
    tb.open(msfile+'/OBSERVATION')
    obstime = np.squeeze(tb.getcol('TIME_RANGE', startrow = obsid, nrow = 1))[0]
    tb.close()
    nchan = len(chanfreqs)
    ms.open(msfile)
    
    lsrkfreqs = ms.cvelfreqs(spwids = [spw], fieldids = int(np.where(fieldnames==field)[0][0]), mode = 'channel', nchan = nchan, \
            obstime = str(obstime)+'s', start = 0, outframe = 'LSRK') / 1e9
    ms.close()

    if type(LSRKfreq)==np.ndarray:
        outchans = np.zeros_like(LSRKfreq)
        for i in range(len(LSRKfreq)):
            outchans[i] = np.argmin(np.abs(lsrkfreqs - LSRKfreq[i]))
        return outchans
    else:
        return np.argmin(np.abs(lsrkfreqs - LSRKfreq))

def parse_contdotdat(contdotdat_file,target):
    """
    Parses the cont.dat file that includes line emission automatically identified by the ALMA pipeline.

    Parameters
    ==========
    msfile: Name of the cont.dat file (string)

    Returns
    =======
    Dictionary with the boundaries of the frequency range including line emission. The dictionary keys correspond to the spectral windows identified 
    in the cont.dat file, and the entries include numpy arrays with shape (nline, 2), with the 2 corresponding to min and max frequencies identified.
    """
    f = open(contdotdat_file,'r')
    lines = f.readlines()
    f.close()

    while '\n' in lines:
        lines.remove('\n')

    contdotdat = {}
    desiredTarget=False
    for i, line in enumerate(lines):
        if 'Field' in line:
            field=line.split()[-1]
            if field == target:
               desiredTarget=True
               continue
            else:
               desiredTarget=False
               continue
        if desiredTarget==True:
           if 'SpectralWindow' in line:
              spw = int(line.split()[-1])
              contdotdat[spw] = []
           else:
              contdotdat[spw] += [line.split()[0].split("G")[0].split("~")]

    for spw in contdotdat:
        contdotdat[spw] = np.array(contdotdat[spw], dtype=float)

    return contdotdat

def flagchannels_from_contdotdat(vis,target,spwsarray):
    """
    Generates a string with the list of lines identified by the cont.dat file from the ALMA pipeline, that need to be flagged.

    Parameters
    ==========
    ms_dict: Dictionary of information about measurement set

    Returns
    =======
    String of channels to be flagged, in a format that can be passed to the spw parameter in CASA's flagdata task. 
    """
    contdotdat = parse_contdotdat('cont.dat',target)

    flagchannels_string = ''
    for j,spw in enumerate(contdotdat):
        flagchannels_string += '%d:' % (spw)

        tb.open(vis+'/SPECTRAL_WINDOW')
        nchan = tb.getcol('CHAN_FREQ', startrow = spw, nrow = 1).size
        tb.close()

        chans = np.array([])
        for k in range(contdotdat[spw].shape[0]):
            print(spw, contdotdat[spw][k])

            chans = np.concatenate((LSRKfreq_to_chan(vis, target, spw, contdotdat[spw][k],spwsarray),chans))

            """
            if flagchannels_string == '':
                flagchannels_string+='%d:%d~%d' % (spw, np.min([chans[0], chans[1]]), np.max([chans[0], chans[1]]))
            else:
                flagchannels_string+=', %d:%d~%d' % (spw, np.min([chans[0], chans[1]]), np.max([chans[0], chans[1]]))
            """

        chans = np.sort(chans)

        flagchannels_string += '0~%d;' % (chans[0])
        for i in range(1,chans.size-1,2):
            flagchannels_string += '%d~%d;' % (chans[i], chans[i+1])
        flagchannels_string += '%d~%d, ' % (chans[-1], nchan-1)

    print("# Flagchannels input string for %s in %s from cont.dat file: \'%s\'" % (target, vis, flagchannels_string))

    return flagchannels_string

def get_spw_chanwidths(vis,spwarray):
   widtharray=np.zeros(len(spwarray))
   for i in range(len(spwarray)):
      tb.open(vis+'/SPECTRAL_WINDOW')
      widtharray[i]=np.abs(np.unique(tb.getcol('CHAN_WIDTH', startrow = spwarray[i], nrow = 1)))
      tb.close()

   return widtharray

def get_spw_chanavg(vis,widtharray,desiredWidth=15.625e6):
   avgarray=np.zeros(len(widtharray))
   for i in range(len(widtharray)):
      avgarray[i]=desiredWidth/widtharray[i]
      if avgarray[i] < 1.0:
         avgarray[i]=1.0
   return avgarray


def get_image_parameters(vislist,telescope,band,band_properties):
   cells=np.zeros(len(vislist))
   for i in range(len(vislist)):
      #im.open(vislist[i])
      im.selectvis(vis=vislist[i],spw=band_properties[vislist[i]][band]['spwarray'])
      adviseparams= im.advise() 
      cells[i]=adviseparams[2]['value']/2.0
      im.close()
   cell=np.mean(cells)
   cellsize='{:0.3f}arcsec'.format(cell)
   nterms=1
   if band_properties[vislist[0]][band]['fracbw'] > 0.1:
      nterms=2
   if 'VLA' in telescope:
      fov=45.0e9/band_properties[vislist[0]][band]['meanfreq']*60.0*1.5
   if telescope=='ALMA':
      fov=63.0*100.0e9/band_properties[vislist[0]][band]['meanfreq']*1.5
   npixels=int(np.ceil(fov/cell / 100.0)) * 100
   if npixels > 16384:
      npixels=16384
   return cellsize,npixels,nterms


def get_mean_freq(vislist,spwsarray):
   tb.open(vislist[0]+'/SPECTRAL_WINDOW')
   freqarray=tb.getcol('REF_FREQUENCY')
   tb.close()
   meanfreq=np.mean(freqarray[spwsarray])
   minfreq=np.min(freqarray[spwsarray])
   maxfreq=np.max(freqarray[spwsarray])
   fracbw=np.abs(maxfreq-minfreq)/meanfreq
   return meanfreq, maxfreq,minfreq,fracbw

def get_desired_width(meanfreq):
   if meanfreq >= 50.0e9:
      desiredWidth=15.625e6
   elif (meanfreq < 50.0e9) and (meanfreq >=40.0e9):
      desiredWidth=16.0e6
   elif (meanfreq < 40.0e9) and (meanfreq >=26.0e9):
      desiredWidth=8.0e6
   elif (meanfreq < 26.0e9) and (meanfreq >=18.0e9):
      desiredWidth=16.0e6
   elif (meanfreq < 18.0e9) and (meanfreq >=8.0e9):
      desiredWidth=8.0e6
   elif (meanfreq < 8.0e9) and (meanfreq >=4.0e9):
      desiredWidth=4.0e6
   elif (meanfreq < 4.0e9) and (meanfreq >=2.0e9):
      desiredWidth=4.0e6
   elif (meanfreq < 4.0e9):
      desiredWidth=2.0e6
   return desiredWidth


def get_ALMA_bands(vislist,spwstring,spwarray):
   meanfreq, maxfreq,minfreq,fracbw=get_mean_freq(vislist,spwarray)
   observed_bands={}
   if (meanfreq < 950.0e9) and (meanfreq >=787.0e9):
      band='Band_10'
   elif (meanfreq < 720.0e9) and (meanfreq >=602.0e9):
      band='Band_9'
   elif (meanfreq < 500.0e9) and (meanfreq >=385.0e9):
      band='Band_8'
   elif (meanfreq < 373.0e9) and (meanfreq >=275.0e9):
      band='Band_7'
   elif (meanfreq < 275.0e9) and (meanfreq >=211.0e9):
      band='Band_6'
   elif (meanfreq < 211.0e9) and (meanfreq >=163.0e9):
      band='Band_5'
   elif (meanfreq < 163.0e9) and (meanfreq >=125.0e9):
      band='Band_4'
   elif (meanfreq < 116.0e9) and (meanfreq >=84.0e9):
      band='Band_3'
   elif (meanfreq < 84.0e9) and (meanfreq >=67.0e9):
      band='Band_2'
   elif (meanfreq < 50.0e9) and (meanfreq >=30.0e9):
      band='Band_1'
   bands=[band]
   for vis in vislist:
      observed_bands[vis]={}
      
      for band in bands:
         observed_bands[vis][band]={}
         observed_bands[vis][band]['spwarray']=spwarray
         observed_bands[vis][band]['spwstring']=spwstring+''
         observed_bands[vis][band]['meanfreq']=meanfreq
         observed_bands[vis][band]['maxfreq']=maxfreq
         observed_bands[vis][band]['minfreq']=minfreq
         observed_bands[vis][band]['fracbw']=fracbw

   return bands,observed_bands


def get_VLA_bands(vislist):
   observed_bands={}
   for vis in vislist:
      observed_bands[vis]={}
      #visheader=vishead(vis,mode='list',listitems=[])
      tb.open(vis+'/SPECTRAL_WINDOW') 
      spw_names=tb.getcol('NAME')
      tb.close()
      #spw_names=visheader['spw_name'][0]
      spw_names_band=spw_names.copy()
      spw_names_bb=spw_names.copy()
      spw_names_spw=np.zeros(len(spw_names_band)).astype('int')
      for i in range(len(spw_names)):
         spw_names_band[i]=spw_names[i].split('#')[0]
         spw_names_bb[i]=spw_names[i].split('#')[1]
         spw_names_spw[i]=i
      all_bands=np.unique(spw_names_band)
      observed_bands[vis]['n_bands']=len(all_bands)
      observed_bands[vis]['bands']=all_bands.tolist()
      for band in all_bands:
         index=np.where(spw_names_band==band)
         if (band == 'EVLA_X') and (len(index[0]) == 2): # ignore pointing band
            observed_bands[vis]['n_bands']=observed_bands[vis]['n_bands']-1
            observed_bands[vis]['bands'].remove('EVLA_X')
            continue
         elif (band == 'EVLA_X') and (len(index[0]) > 2): # ignore pointing band
            observed_bands[vis][band]={}
            observed_bands[vis][band]['spwarray']=spw_names_spw[index[0]]
            indices_to_remove=np.array([])
            for i in range(len(observed_bands[vis][band]['spwarray'])):
                meanfreq,maxfreq,minfreq,fracbw=get_mean_freq([vis],np.array([observed_bands[vis][band]['spwarray'][i]]))
                if (meanfreq==8.332e9) or (meanfreq==8.460e9):
                   indices_to_remove=np.append(indices_to_remove,[i])
            observed_bands[vis][band]['spwarray']=np.delete(observed_bands[vis][band]['spwarray'],indices_to_remove)
            spwslist=observed_bands[vis][band]['spwarray'].tolist()
            spwstring=','.join(str(spw) for spw in spwslist)
            observed_bands[vis][band]['spwstring']=spwstring+''
            observed_bands[vis][band]['meanfreq'],observed_bands[vis][band]['maxfreq'],observed_bands[vis][band]['minfreq'],observed_bands[vis][band]['fracbw']=get_mean_freq([vis],observed_bands[vis][band]['spwarray'])
         elif (band == 'EVLA_C') and (len(index[0]) == 2): # ignore pointing band
            observed_bands[vis]['n_bands']=observed_bands[vis]['n_bands']-1
            observed_bands[vis]['bands'].remove('EVLA_C')
            continue
         elif (band == 'EVLA_C') and (len(index[0]) > 2): # ignore pointing band
            observed_bands[vis][band]={}
            observed_bands[vis][band]['spwarray']=spw_names_spw[index[0]]
            indices_to_remove=np.array([])
            for i in range(len(observed_bands[vis][band]['spwarray'])):
                meanfreq,maxfreq,minfreq,fracbw=get_mean_freq([vis],np.array([observed_bands[vis][band]['spwarray'][i]]))
                if (meanfreq==4.832e9) or (meanfreq==4.960e9):
                   indices_to_remove=np.append(indices_to_remove,[i])
            observed_bands[vis][band]['spwarray']=np.delete(observed_bands[vis][band]['spwarray'],indices_to_remove)
            spwslist=observed_bands[vis][band]['spwarray'].tolist()
            spwstring=','.join(str(spw) for spw in spwslist)
            observed_bands[vis][band]['spwstring']=spwstring+''
            observed_bands[vis][band]['meanfreq'],observed_bands[vis][band]['maxfreq'],observed_bands[vis][band]['minfreq'],observed_bands[vis][band]['fracbw']=get_mean_freq([vis],observed_bands[vis][band]['spwarray'])
         else:
            observed_bands[vis][band]={}
            observed_bands[vis][band]['spwarray']=spw_names_spw[index[0]]
            spwslist=observed_bands[vis][band]['spwarray'].tolist()
            spwstring=','.join(str(spw) for spw in spwslist)
            observed_bands[vis][band]['spwstring']=spwstring+''
            observed_bands[vis][band]['meanfreq'],observed_bands[vis][band]['maxfreq'],observed_bands[vis][band]['minfreq'],observed_bands[vis][band]['fracbw']=get_mean_freq([vis],observed_bands[vis][band]['spwarray'])
   bands_match=True
   for i in range(len(vislist)):
      for j in range(i+1,len(vislist)):
         bandlist_match=(observed_bands[vislist[i]]['bands'] ==observed_bands[vislist[i+1]]['bands'])
         if not bandlist_match:
            bands_match=False
   if not bands_match:
     print('WARNING: INCONSISTENT BANDS IN THE MSFILES')
   
   return observed_bands[vislist[0]]['bands'],observed_bands





