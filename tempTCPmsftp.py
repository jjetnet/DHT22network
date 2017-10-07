# class for current climate data hteml generation/update, includines BOM data reading
# relative humidity to water vapour partial pressure conversion, and
# reading from multiple sparkfun thing wifi sensors

import matplotlib
matplotlib.use('Agg')
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen
    
from ftplib import FTP 
import json,math
import serial
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
import gc
import socket
import threading
import sys
import matplotlib.cbook as cbook
from pushetta import Pushetta
# import network configuration etc
from tempTCPconfig import *

#import time
from time import asctime,localtime,time,sleep,strftime,strptime,mktime
import datetime
NaN=float('NaN')

dateconv = np.vectorize(datetime.datetime.fromtimestamp)
class TCPlistener:
    def __init__(self,port,errfilen):
        # initiate TCP listener on port port, log errors on file object errfilen, which must be open
        self.port=port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.errfilen=errfilen;
        #Bind socket to local host and port
        self.exitloop=False
        try:
            self.s.bind(('', port))
        except socket.error as msg:
            self.inflog('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]);
            sys.exit()
            self.exitloop=True

        self.s.listen(5)
        self.TCPlistener()
        
    def _TCPlistener(self):
        # listens to TCP port and start new thread for each connection
        # call through TCPlistener to put this in non blocking thread
        while not self.exitloop:
            # print '.'
            conn, addr = self.s.accept()
            self.inflog('Connected with ' + addr[0] + ':' + str(addr[1]))
            t=threading.Thread(target=self.clientthread ,args=(conn,))
            t.start()
            t.join()

        self.s.close()
        sys.exit()


    def TCPlistener(self):
        threading.Thread(target=self._TCPlistener).start()
        
    def clientthread(self,conn):
    #infinite loop so that function do not terminate and thread do not end. probably not needed with curent exit condition
        while True:
            #Receiving from client
            
            data = conn.recv(1024)
            self.inflog('"'+data.strip()+'"')
            if(data!=''):
                try:
                    sensordata=json.loads(data)
                    self.it=sensordata["T"]
                    self.ih=sensordata["H"]
                    self.sensorID=sensordata["S"]
                    try:
                        self.battery=sensordata["B"]
                    except:
                        self.battery=-1

                    self.itimestamp=localtime(time())
                    self.gotnewdata=True
                    break
                except:
                    self.inflog('json error: "'+str(data)+'"')
                    data=False
                    break

#                conn.send('
            #reply = 'OK...' + data
            if not data: 
                break

            #conn.sendall(reply)

        #came out of loop
        conn.close()
	return 0
    def inflog(self,txt):
        txt=strftime('%d-%m-%Y %H:%M:%S')+': '+txt+'\n'
        self.errfilen.write(txt);
          

class climatehtmlfileTCP:
    def __init__(self,filepath,bomurl,fileradix,port,errfile,lowT,highT):
        self.filename=filepath+fileradix+'.html'
        self.bomurl=bomurl
        self.datalogfile=filepath+fileradix
        self.fileradix=fileradix
        self.filepath=filepath
        self.port=port
        self.errfile=errfile
        self.errfilen=open(errfile,'a',0) # error file in unbuffered
        self.TCPlistener=TCPlistener(port,self.errfilen)
        self.TCPlistener.gotnewdata=False
        self.sensidtable={}
        self.lastUpdate=time()-60 
        self.alertTempLow=lowT
        self.alertTempHigh=highT
        self.sentAlertHigh=False
        self.sentAlertLow=False
        self.inflog('climateHTMLfile class initiated')
        #print 'initiated'
        if(API_KEY):
            self.p=Pushetta(API_KEY)
            self.p.pushMessage(CHANNEL_NAME,"Service started")            
        else:
            self.p=False

    def inflog(self,txt):
        txt=strftime('%d-%m-%Y %H:%M:%S')+': '+txt+'\n'
        self.errfilen.write(txt);
            
    def waterPartialPressure(self,temperature,humidity):
        "Calculates watersaturatiopressure(temperature,humidity) temperautre (C), h (%)"
        # formula for water saturation vapor pressure from
        # http://www.vaisala.com/Vaisala%20Documents/Application%20notes/Humidity_Conversion_Formulas_B210973EN-F.pdf
        Tc = 647.096 
        Pc = 22064000
        C1 = -7.85951783
        C2 = 1.84408259
        C3 = -11.7866497
        C4 = 22.6807411
        C5 = -15.9618719
        C6 = 1.80122502
        t=1-(temperature+273.15)/Tc
        pw=humidity/100*Pc*math.exp(Tc/(temperature+273.15)*(C1*t+C2*math.pow(t,1.5)+C3*math.pow(t,3)+C4*math.pow(t,3.5)+C5*math.pow(t,4)+C6*math.pow(t,7.5)))
        #print pw
        return pw

    def getBomData(self):
        "get BOM observations"
        try:
            response = urlopen(self.bomurl)
            self.bomdata=json.load(response)
            self.ot=float(self.bomdata["observations"]["data"][0]["air_temp"])
            self.oh=float(self.bomdata["observations"]["data"][0]["rel_hum"])
            self.bomdatatime=self.bomdata["observations"]["data"][0]["local_date_time"]
            bomd=self.bomdata["observations"]["data"][0]["local_date_time_full"]
            self.bomdatatimefull=strptime(bomd,"%Y%m%d%H%M%S")
            self.op=self.waterPartialPressure(self.ot,self.oh)
            self.hasbomdata=True
        except:
            self.hasbomdata=False
            self.ot=NaN
            self.op=NaN
            self.oh=NaN
            self.bomdatatime=localtime()
            self.bomdatatimefull=localtime()
            self.inflog("failed to load bom data")
				   

    def getSensorData(self):    
        #data comes from TCP reader - here we just update the vapour pressure based on existing data
        if self.TCPlistener.ih<0:
             self.hasSensorData=False
             self.inflog(asctime()+'Sensor error: '+str(self.TCPlistener.sensorID)+'returned '+str(self.TCPlistener.ih)+'\n')
        else:
            self.addSensorData(self.TCPlistener.it,self.TCPlistener.ih,self.TCPlistener.sensorID,self.TCPlistener.itimestamp, self.TCPlistener.battery)
            self.hasSensorData=True
            
    def addSensorData(self,t,h,sensid,timest,b):
        ip=self.waterPartialPressure(t,h)
        self.sensidtable[sensid]={'T': t,'H': h, 'P': ip, 'Time': timest,'B': b}            
        
    def addlinetotable(self,text):
        self.filen.write("<tr>"+text+"</tr>")

    def begintable(self):
        self.filen.write('<table border CLASS="climatetable">')
                    
    def closetable(self):
        self.filen.write("</table>")
        
    def adddatatologfile(self,sensid):
        it=self.sensidtable[sensid]['T']
        ih=self.sensidtable[sensid]['H']
        ip=self.sensidtable[sensid]['P']
        ib=self.sensidtable[sensid]['B']
        timest=self.sensidtable[sensid]['Time']
        datafilen=open(self.datalogfile+str(sensid)+'.csv','a')
        datafilen.write(str.format('{0:.3f}',mktime(timest))+',')
        datafilen.write(strftime('%d-%m-%Y %H:%M:%S',timest)+",")
        datafilen.write(str.format("{0:.1f}",it)+",")
        datafilen.write(str.format("{0:.0f}",ih)+",")
        datafilen.write(str.format("{0:.0f}",ip)+",")
        datafilen.write(str.format("{0:.0f}",ib)+"\n")
        datafilen.close()

        
    def writeBOMcsv(self):
        if(self.hasbomdata):
            datafilen=open(self.datalogfile+'BOM.csv','a')
            datafilen.write(str.format('{0:.3f}',mktime(self.bomdatatimefull))+',')
            datafilen.write(strftime('%d-%m-%Y %H:%M:%S',self.bomdatatimefull)+",")
            datafilen.write(str.format("{0:.1f}",self.ot)+",")
            datafilen.write(str.format("{0:.0f}",self.oh)+",")
            datafilen.write(str.format("{0:.0f}",self.op)+"\n")
            datafilen.close()

    def ftpcopy(self, name):
        # copies file name to  remote webserver over ftp - without path information
        if(ftpserver): # only if ftpserver is defined
            lf=open(name, 'r') 
            try:
                f=FTP(ftpserver) # defined in config file
                f.login(ftplogin,ftppwd)
                rname=name.split('/')[-1] # remove path
                f.storbinary('STOR ' +rname ,lf)
                f.quit()
            except:
                self.inflog("failed to uplod to ftp")
            
            lf.close()
        
        
    def plotdataday(self,nameext,days=1):        
	#plot data for last days day only, save with nameext.png extension
        data={}
        cols=['r', 'b' ,'g', 'y','c','k']
        #plt.style.use('ggplot')
        plt.rc('lines', linewidth=3)
        f, (ax1, ax2,ax3)= plt.subplots(3,sharex=True,sharey=False)
        f.set_size_inches(5,10)
        # plot BOM data first
        ax1.set_color_cycle(cols)
        ax2.set_color_cycle(cols)
        ax3.set_color_cycle(cols)
        icol=0
        data=np.genfromtxt(self.datalogfile+'BOM.csv',skip_header=0,delimiter=',')
        data=data[~np.isnan(data[:,0])] # remove lines with nan for date
        if data[:,0].size>1: # only plot if more than one data point
            lcol=cols[icol]
            ndates=data[:,0]
            ldates=dateconv(ndates[ndates[:]>=ndates[-1]-24*3600*days])
            ldata=data[ndates[:]>=ndates[-1]-24*3600*days]
            if(ldata[:,0].size>1):
                ax1.plot_date(ldates,ldata[:,2],ls='solid',marker="",color=lcol,label='outside')
                ax2.plot_date(ldates,ldata[:,3],ls='solid',marker="",color=lcol,label='outside')
                ax3.plot_date(ldates,ldata[:,4],ls='solid',marker="",color=lcol,label='outside')

        ax1.set_title('Temperature')
        ax1.set_ylabel('Temp')
        ax2.set_title('Rel humidity')
        ax2.set_ylabel('%')
        ax3.set_title('Vap pressure')
        ax3.set_ylabel('Pa')

        # now add all sensor data
        for sid in self.sensidtable:
            data=np.genfromtxt(self.datalogfile+str(sid)+'.csv',skip_header=0,delimiter=',')
            data=data[~np.isnan(data[:,0])] # remove lines with nan for date
            if(data[:,0].size>1):
                icol=icol+1
                if icol>=len(cols): icol=1
                lcol=cols[icol]                
                ndates=data[:,0]
                ldates=dateconv(ndates[ndates[:]>=ndates[-1]-24*3600*days])
#                ndates=ndates[~np.isnan(data).any(axis=1)] # removs raws with nans
                if len(set(ldates))>1: #only plot if more than one unique timestamp in srlected timeframe
                    ldata=data[ndates[:]>=ndates[-1]-24*3600*days]
                    if(ldata[:,0].size>1):
                        ax1.plot_date(ldates,ldata[:,2],ls='solid',marker="",color=lcol,label=str(sid))
                        ax2.plot_date(ldates,ldata[:,3],ls='solid',marker="",color=lcol,label=str(sid))
                        ax3.plot_date(ldates,ldata[:,4],ls='solid',marker="",color=lcol,label=str(sid))

        f.autofmt_xdate()        
        if days>1:
            xfmt = md.DateFormatter('%Y-%m-%d %H:%M')
        else:
            xfmt = md.DateFormatter('%H:%M')        
        ax3.xaxis.set_major_formatter(xfmt)
        ax1.grid()
        ax2.grid()
        ax3.grid()
        ax1.xaxis_date()
        ax2.xaxis_date()
        ax3.xaxis_date()
        f.subplots_adjust(top=0.85)
        plt.legend(bbox_to_anchor=(0., 0.95, 1., .102),  bbox_transform=plt.gcf().transFigure, loc=3, ncol=3, mode="expand", borderaxespad=0.)
        plt.savefig(self.datalogfile+nameext+'.png',dpi=100)
        self.ftpcopy(self.datalogfile+nameext+'.png')
        f.clf()
        plt.close()
        gc.collect()
        
    def sendAlerts(self):
        if(self.p and self.hasbomdata): #if pushetta service has been enabled, send alerts
            if (self.ot<self.alertTempLow) and not(self.sentAlertLow):
                try:
                    self.p.pushMessage(CHANNEL_NAME,"Temperature alert (" +str(self.ot)+")")
                    self.sentAlertLow=True
                except:
                    self.inflog("puschetta notification failed")
                    
            if (self.ot>self.alertTempHigh) and not(self.sentAlertHigh):
                try:
                    self.p.pushMessage(CHANNEL_NAME,"Temperature alert (" +str(self.ot)+")")
                    self.sentAlertHigh=True
                except:
                    self.inflog("puschetta notification failed")
                                        
    # reset flags            
            if (self.ot>self.alertTempLow+1) and (self.sentAlertLow):
                self.sentAlertLow=False
            if (self.ot<self.alertTempHigh-1) and (self.sentAlertHigh):
                self.sentAlertHigh=False


    def update(self):
        " update webpage, based on it (inside temp), ih (inside rel humidity), ot (outside temp), oh (outside hum)"
       # try:
        self.getSensorData()
        if time()>self.lastUpdate+60: # do not update files more often than once per minute            
            self.TCPlistener.gotnewdata=False
            self.lastUpdate=time()
            self.getBomData()
                
            self.writeBOMcsv()
            self.sendAlerts()

            if self.hasSensorData:
                # first write to NOW file
                datafilen=open(self.datalogfile+'NOW.txt','w')
                datafilen.write('Canterburry: ')
                datafilen.write(str.format(": {0:.1f} C",self.ot)+", ")
                datafilen.write(str.format("{0:.0f} %",self.oh)+", ")
                datafilen.write(str.format("{0:.0f} Pa",self.op)+" (")
                datafilen.write(strftime('%d-%m %H:%M',self.bomdatatimefull)+")\n")

                for sid in self.sensidtable:
                    it=self.sensidtable[sid]['T']
                    ih=self.sensidtable[sid]['H']
                    ip=self.sensidtable[sid]['P']
                    ib=self.sensidtable[sid]['B']
                    its=self.sensidtable[sid]['Time']
                    datafilen.write(str(sid))
                    datafilen.write(str.format(": {0:.1f} C",it)+", ")
                    datafilen.write(str.format("{0:.0f} %",ih)+", ")
                    datafilen.write(str.format("{0:.0f} Pa",ip)+" (")
                    datafilen.write(strftime('%d-%m %H:%M',its)+")\n")
                datafilen.close()
                self.ftpcopy(self.datalogfile+'NOW.txt')
                
                self.filen=open(self.filename,'w')
                self.datafilen=open(self.datalogfile,'a')
                self.filen.write('<html><head><link rel="stylesheet" type="text/css" href="climatetable.css"><meta http-equiv="refresh" content="30"></head><body>\n')
                self.begintable()
                self.addlinetotable("<td> Sensor</td><td>Temperature </td><td>Relative humidity</td><td>Water Vapour Pressure</td><td>time</td><td>Battery level</td>")
                self.addlinetotable("<td>Outside:</td><td>"+str.format("{0:.1f}",self.ot)+"&deg;C</td><td>"+str.format("{0:.1f}",self.oh)+" %</td><td>"+
                                    str.format("{0:.1f}",self.op)+" Pa</td><td>"+strftime('%d-%m-%Y %H:%M:%S',self.bomdatatimefull)+"</td><td></td>")
                for sid in self.sensidtable:
                    it=self.sensidtable[sid]['T']
                    ih=self.sensidtable[sid]['H']
                    ip=self.sensidtable[sid]['P']
                    ib=self.sensidtable[sid]['B']
                    its=self.sensidtable[sid]['Time']
                    if ib<3400:
                        self.addlinetotable("<td>"+str(sid)+":</td><td>"+str.format("{0:.1f}",it)+"&deg;C</td><td>"+str.format("{0:.1f}",ih)+" %</td><td>"+
                                        str.format("{0:.1f}",ip)+" Pa</td><td>"+strftime('%d-%m-%Y %H:%M:%S',its)+'</td><td CLASS="bad">'+str(ib)+"</td>")
                    else:
                        self.addlinetotable("<td>"+str(sid)+":</td><td>"+str.format("{0:.1f}",it)+"&deg;C</td><td>"+str.format("{0:.1f}",ih)+" %</td><td>"+
                                        str.format("{0:.1f}",ip)+" Pa</td><td>"+strftime('%d-%m-%Y %H:%M:%S',its)+'</td><td CLASS="good">'+str(ib)+"</td>")
                    self.adddatatologfile(sid) #having this here writes one line on csv file each time 
                                               # any sensor sends data, ending up with as many repeat lines as there are sensors

                self.closetable()
                self.filen.write("<p><img src="+self.fileradix+"day.png></p>")
                self.filen.write("<p><img src="+self.fileradix+".png></p>")


                self.filen.write("</body></html>")
                self.filen.close()
                self.ftpcopy(self.filename)
                self.plotdataday('',30)
                self.plotdataday('day',1)



# main code begings here

# for rasp pi
climatefile=climatehtmlfileTCP(wpath,BOMpath,fradix,TCPport,errfilename,AlertLowT,AlertHighT)

#climatefile.update()        
#climatefile.ser.close()


try:
    # update pltos first - useful for debug
   # climatefile.plotdataday()
    pass
except:
    climatefile.inflog('error while plotting')

try:
    while 1:
        if climatefile.TCPlistener.gotnewdata:
            #print 'gotnewdata'
            climatefile.update()        


        for lti in range(1): # update no faster than every 1 seconds
            sleep(1)
        
except KeyboardInterrupt:
    climatefile.TCPlistener.s.close()
    climatefile.errfilen.close()
    climatefile.TCPlistener.exitloop=True
    
    
finally:
    climatefile.TCPlistener.s.close()
    climatefile.errfilen.close()
    climatefile.TCPlistener.exitloop=True
    climatefile.p.pushMessage(CHANNEL_NAME,"Service terminated")
    
