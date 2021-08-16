from bluepy.btle import Scanner, DefaultDelegate
from datetime import timedelta, datetime
from typing import NamedTuple
import os.path

from colorama import Fore, Style

fileName = 'tlm.csv'
fileWritePeriod = 36 #seconds

class DeviceAttr(NamedTuple):
    addr:str
    rssi:int
    bat:int
    sec:int
    cnt:int
    tmp:float
    
eddyDevices = {}
startTime = datetime.now()
currentTime = datetime.now()

class ScanDelegate(DefaultDelegate):
  def __init__(self):
    DefaultDelegate.__init__(self)

  def handleDiscovery(self, dev, isNewDev, isNewData):
    if not dev.connectable:
      dtScanData = dev.getScanData()
      if type(dtScanData)!=list or len(dtScanData)!=3: return

      dtScanTuple = dtScanData[2]
      if type(dtScanTuple)!=tuple or len(dtScanTuple)!=3: return

      dt = dtScanTuple[2]
      #check AAFE=eddystone, 20=TLM
      if len(dt)!=32 or dt[:6]!="aafe20": return

      # https://github.com/google/eddystone/blob/master/eddystone-tlm/tlm-plain.md
      ba = bytes.fromhex( dt[4:] )

      bat = int.from_bytes(ba[2:4], byteorder='big')
      tmp = int.from_bytes(ba[4:5], byteorder='big', signed=True)
      tmpf = ba[5] / 256
      tmp = tmp + (tmpf if tmp > 0 else -tmpf)
      cnt = int.from_bytes(ba[6 :10], byteorder='big')
      sec = int.from_bytes(ba[10:14], byteorder='big')//10

      eddyDevices.update({dev.addr : DeviceAttr(dev.addr, dev.rssi, bat, sec, cnt, tmp)})
      print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | '\
      f'{dev.addr} | bat {Fore.GREEN}{bat}mV{Style.RESET_ALL} | tmp {Fore.YELLOW}{tmp:3.1f}°C{Style.RESET_ALL} | rssi {Fore.MAGENTA}{dev.rssi}dB{Style.RESET_ALL} | time {Fore.CYAN}{str(timedelta(seconds=sec))}{Style.RESET_ALL} ')

print("Scan... (Press Ctrl+C to terminate)")

bExit = False
while bExit == False:
  try:
    scanner = Scanner().withDelegate(ScanDelegate())    
    devices = scanner.scan(1) #10 s by default   
    
    currentTime = datetime.now()
    if (currentTime - startTime).total_seconds() > fileWritePeriod:
        # title of table
        if not os.path.isfile(fileName):
            with open(fileName, 'a') as outfile:
                outfile.write('time;addr;rssi;bat;sec;cnt;tmp\n')
        # data
        with open(fileName, 'a') as outfile:
            for addr in eddyDevices:
                s = '{addr};{rssi};{bat};{sec};{cnt};{tmp}\n'
                
                outfile.write(currentTime.strftime("%Y-%m-%d %H:%M:%S")+';'+\
                s.format(**eddyDevices[addr]._asdict()).replace('.',','))
                
        startTime = currentTime
        eddyDevices.clear()
    
  except KeyboardInterrupt:
    bExit = True
