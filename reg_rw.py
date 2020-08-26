#!/usr/bin/python

import mmap
import os
import sys
import time
import datetime
from optparse import OptionParser


def chars_to_vals(chars):
	vals = 0
	for c in chars:
		vals = (vals << 8) | ord(c)
	return vals

def vals_to_chars(vals,num):
	chars = ""
	for i in range(num):
		chars = chr((vals >> (8*i))&0xFF) + chars
	return chars

class phy_mem_access(object):
	def __init__(self):
		self.is_opened = False

	def open(self,base_addr, psize=mmap.PAGESIZE):
		self.fd        = os.open("/dev/mem", os.O_RDWR)
		self.base_addr = base_addr
		gpio_addr      = base_addr
		page_size      = psize
		page_addr	   = (gpio_addr & (~(page_size-1)))
		page_offset    = gpio_addr - page_addr
		self.rdptr     = mmap.mmap(fileno=self.fd,length=page_size,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=page_addr)
		self.wrptr     = mmap.mmap(fileno=self.fd,length=page_size,flags=mmap.MAP_SHARED,prot=mmap.PROT_WRITE,offset=page_addr)
		self.is_opened = True
		
	def close(self):
		if (not self.is_opened):
			return
		self.is_opened = False
		self.rdptr.close()
		self.wrptr.close()
		os.close(self.fd)
		
	def __getitem__(self, index):
		return self.rdptr[index]
		
	def __setitem__(self, index, value):
		self.wrptr[index] = value
		
	def __getslice__(self,a,b):
		return self.rdptr[a:b][::-1]
		
	def __setslice__(self, a, b, value):
		if (len(value) != (b-a)):
			raise ValueError('Slice length does not equal actual length')
		self.wrptr[a:b] = value[::-1]
	
	def write32(self,addr,val):
		x[addr:addr+4] = vals_to_chars(val,4)
	def read32(self,addr):
		return chars_to_vals(x[addr:addr+4])
	def write64(self,addr,val):
		x[addr:addr+8] = vals_to_chars(val,8)
	def read64(self,addr):
		return chars_to_vals(x[addr:addr+8])

def find_pcie_dev(vendor_id,device_id):
	pcie_device_list = [x[1] for x in os.walk("/sys/bus/pci/devices")][0]
	for dev in pcie_device_list:
		devpath = "/sys/bus/pci/devices/" + dev
		x = open(devpath + "/vendor")
		vendor = x.read()
		x.close()
		x = open(devpath + "/device")
		device = x.read()
		x.close()
		if ((vendor_id == int(vendor.strip(),16)) and (device_id == int(device.strip(),16))):
			return devpath
	return ""
	
def get_dcp_base_addr(bar=0):
	devpath = find_pcie_dev(0x10ee, 0x8038)
	if devpath == '':
		print "Error: No PCIe device found"
		exit(1)
	f = open(devpath+"/resource" , 'r')
	desc = f.read()
	f.close()
	desc = desc.split('\n')
	BAR0 = int(desc[0].split()[0],16)
	BAR1 = int(desc[1].split()[0],16)
	BAR2 = int(desc[2].split()[0],16)
	BAR3 = int(desc[3].split()[0],16)
	BAR4 = int(desc[4].split()[0],16)
	BAR5 = int(desc[5].split()[0],16)
	if bar == 0: return BAR0
	if bar == 1: return BAR1
	if bar == 2: return BAR2
	if bar == 3: return BAR3
	if bar == 4: return BAR4
	if bar == 5: return BAR5
	return -1
	
if __name__ == '__main__':
	import sys
	bar_id = 0
	x = phy_mem_access()
	x.open(get_dcp_base_addr(bar_id), 0x400000)

        # first read 0x10000(valid address) should get the right value (not 0xffffffff)
        print("read 0x10000")
        temp=x.read32(0x10000)
        print(hex(temp))
        print("end read 0x10000")
        print("")

        # read 0x0(a invalid adress) will cause the AXI err, the read value is 0xffffffff
        print ("read 0x0000")
        temp=x.read32(0x0)
        print(hex(temp))
        print ("end write 0x0")
        print("")

        # the AXI err will cause the second 0x10000 read get the wrong value
        print("read 0x10000")
        temp=x.read32(0x10000)
        print(hex(temp))
        print("end read 0x10000")
        print("")

        # the AXI err cause other read get the wrong value, the error can not recover, execept reboot the system
        print("")
	for i in range(0x00000, 0x30):
		#x.write32(i, i)
	        temp = x.read32(i)
                print(hex(i), hex(temp))
		#x.write64(i,i)
                #temp = x.read64(i)
		#print hex(i)
                #print(hex(i), hex(temp))

	x.close()
