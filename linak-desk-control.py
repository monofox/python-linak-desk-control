# Application to let your desk dance.
# Copyright (C) 2018 Lukas Schreiner <dev@lschreiner.de>
# 
# This program is free software: you can redistribute it and/or modify it under 
# the terms of the GNU General Public License as published by the Free Software 
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY 
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A 
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this 
# program. If not, see <https://www.gnu.org/licenses/>. 

from ctypes import sizeof
import sys
import time
import usb1

REQ_INIT = 0x0303
REQ_GET_STATUS = 0x0304
REQ_MOVE = 0x0305
REQ_GET_EXT = 0x0309

TYPE_SET_CI = 0x21
TYPE_GET_CI = 0xA1

HID_REPORT_GET = 0x01
HID_REPORT_SET = 0x09

CMD_STATUS_REPORT = 4
LEN_STATUS_REPORT = 64
NRB_STATUS_REPORT = 56

CMD_MODE_OF_OPERATION = 3
CMD_GET_LIN_DATA = 4
CMD_CONTROL_CBC = 5
CMD_CONTROL_TD = 6
CMD_CONTROL_CBD_TD = 8
CMD_GET_LIN_DATA_EXT = 9

DEF_MODE_OF_OPERATION = 4

LINAK_TIMEOUT = 1000

HEIGHT_MOVE_DOWNWARDS = 32767
HEIGHT_MOVE_UPWARDS = 32768
HEIGHT_MOVE_END = 32769

class Status(object):
	positionLost = True
	antiColision = True
	overloadDown = True
	overloadUp = True
	unknown = 4

	@classmethod
	def fromBuf(sr, buf):
		self = sr()
		attr = ['positionLost', 'antiColision', 'overloadDown', 'overloadUp']
		bitlist = '{:0>8s}'.format(bin(int(buf, base=16)).lstrip('0b'))
		for i in range(0, 4):
			setattr(self, attr[i], True if bitlist[i] == '1' else False)
		# set unknown
		self.unkown = int(buf[1:], 16)

		return self

class StatusPositionSpeed(object):
	pos = None
	status = None
	speed = 0

	@classmethod
	def fromBuf(sr, buf):
		self = sr()
		self.pos = int(buf[2:4] + buf[:2], 16)
		self.status = Status.fromBuf(buf[4:6])
		self.speed = int(buf[6:8], 16)

		return self

class ValidFlags(object):
	ID00_Ref1_pos_stat_speed = True
	ID01_Ref2_pos_stat_speed = True
	ID02_Ref3_pos_stat_speed = True
	ID03_Ref4_pos_stat_speed = True
	ID10_Ref1_controlInput = True
	ID11_Ref2_controlInput = True
	ID12_Ref3_controlInput = True
	ID13_Ref4_controlInput = True
	ID04_Ref5_pos_stat_speed = True
	ID28_Diagnostic = True
	ID05_Ref6_pos_stat_speed = True
	ID37_Handset1command = True
	ID38_Handset2command = True
	ID06_Ref7_pos_stat_speed = True
	ID07_Ref8_pos_stat_speed = True
	unknown = True

	@classmethod
	def fromBuf(sr, buf):
		self = sr()
		attr = ['ID00_Ref1_pos_stat_speed',	'ID01_Ref2_pos_stat_speed',	'ID02_Ref3_pos_stat_speed',	'ID03_Ref4_pos_stat_speed',	'ID10_Ref1_controlInput',	'ID11_Ref2_controlInput',	'ID12_Ref3_controlInput',	'ID13_Ref4_controlInput',	'ID04_Ref5_pos_stat_speed',	'ID28_Diagnostic',	'ID05_Ref6_pos_stat_speed',	'ID37_Handset1command',	'ID38_Handset2command',	'ID06_Ref7_pos_stat_speed',	'ID07_Ref8_pos_stat_speed',	'unknown']
		bitlist = '{:0>16s}'.format(bin(int(buf, base=16)).lstrip('0b'))
		for i in range(0, len(bitlist)):
			setattr(self, attr[i], True if bitlist[i] == '1' else False)

		return self

class StatusReport(object):
	featureRaportID = 0
	numberOfBytes = 0
	validFlag = None
	ref1 = None
	ref2 = None
	ref3 = None
	ref4 = None
	ref1cnt = 0
	ref2cnt = 0
	ref3cnt = 0
	ref4cnt = 0
	ref5 = None
	diagnostic = None
	undefined1 = None
	handset1 = 0
	handset2 = 0
	ref6 = None
	ref7 = None
	ref8 = None
	undefined2 = None

	@classmethod
	def fromBuf(sr, buf):
		self = sr()
		raw = buf.hex()
		self.featureRaportID = buf[0]
		self.numberOfBytes = buf[1]
		self.validFlag = ValidFlags.fromBuf(raw[4:8])
		self.ref1 = StatusPositionSpeed.fromBuf(raw[8:8+8])
		self.ref2 = StatusPositionSpeed.fromBuf(raw[16:16+8])
		self.ref3 = StatusPositionSpeed.fromBuf(raw[24:24+8])
		self.ref4 = StatusPositionSpeed.fromBuf(raw[32:32+8])
		self.ref1cnt = int(raw[42:44] + raw[40:42], 16)
		self.ref2cnt = int(raw[46:48] + raw[44:46], 16)
		self.ref3cnt = int(raw[50:52] + raw[48:50], 16)
		self.ref4cnt = int(raw[54:56] + raw[52:54], 16)
		self.ref5 = StatusPositionSpeed.fromBuf(raw[56:56+8])
		self.diagnostic = raw[64:64+16]
		self.undefined1 = raw[80:84]
		self.handset1 = int(raw[86:88] + raw[84:86], 16)
		self.handset2 = int(raw[88:90] + raw[86:88], 16)
		self.ref6 = StatusPositionSpeed.fromBuf(raw[90:90+8])
		self.ref7 = StatusPositionSpeed.fromBuf(raw[98:98+8])
		self.ref8 = StatusPositionSpeed.fromBuf(raw[106:106+8])
		self.undefined2 = raw[114:]

		return self

class LinakController(object):
	_handle = None
	_ctx = None

	def __init__(self, vendor_id=0x12d3, product_id=0x0002):
		self._ctx =usb1.USBContext() 
		#self._ctx.setDebug(4)
		self._handle = self._ctx.openByVendorIDAndProductID(
			vendor_id,
			product_id,
			skip_on_error=True,
		)
		if not self._handle:
			raise Exception('Could not connect to usb device')

		if self._handle.kernelDriverActive(0):
			print("Detaching kernel driver")
			self._handle.detachKernelDriver(0)

		self._handle.claimInterface(0)
		self._initDevice()

	def close(self):
		if self._handle:
			self._handle.releaseInterface(0)

		del(self._handle)
		del(self._ctx)

	def _controlWriteRead(self, request_type, request, value, index, data, timeout=0):
		data, data_buffer = usb1.create_initialised_buffer(data)
		transferred = self._handle._controlTransfer(request_type, request, value, index, data,
									 sizeof(data), timeout)
		return transferred, data_buffer[:transferred]

	def _getStatusReport(self):
		buf = bytearray(b'\x00'*LEN_STATUS_REPORT)
		buf[0] = CMD_STATUS_REPORT
		#print('> {:s}'.format(buf.hex()))
		x, buf = self._controlWriteRead(
			TYPE_GET_CI, 
			HID_REPORT_GET, 
			REQ_GET_STATUS, 
			0, 
			buf, 
			LINAK_TIMEOUT
		)

		# check if the response match to request!
		if buf[0] != CMD_STATUS_REPORT:
			raise Exception('Invalid status report received!')

		return buf

	def _setStatusReport(self):
		buf = bytearray(b'\x00'*LEN_STATUS_REPORT)
		buf[0] = CMD_MODE_OF_OPERATION
		buf[1] = DEF_MODE_OF_OPERATION
		buf[2] = 0
		buf[3] = 251

		x, buf = self._controlWriteRead(
			TYPE_SET_CI, 
			HID_REPORT_SET, 
			REQ_INIT, 
			0, 
			buf, 
			LINAK_TIMEOUT
		)

		if x != LEN_STATUS_REPORT:
			raise Exception('Device is not ready yet. Initialization failed in step 1.')

	def _move(self, height):
		buf = bytearray(b'\x00' * LEN_STATUS_REPORT)
		buf[0] = CMD_CONTROL_CBC

		hHex = '{:04x}'.format(height)
		hHigh = int(hHex[2:], 16)
		hLow = int(hHex[:2], 16)

		buf[1] = hHigh
		buf[2] = hLow
		buf[3] = hHigh
		buf[4] = hLow
		buf[5] = hHigh
		buf[6] = hLow
		buf[7] = hHigh
		buf[8] = hLow

		x, buf = self._controlWriteRead(
			TYPE_SET_CI, 
			HID_REPORT_SET, 
			REQ_MOVE, 
			0, 
			buf, 
			LINAK_TIMEOUT
		)
		return x == LEN_STATUS_REPORT

	def _moveDown(self):
		return self._move(HEIGHT_MOVE_DOWNWARDS)

	def _moveUp(self):
		return self._move(HEIGHT_MOVE_UPWARDS)

	def _moveEnd(self):
		return self._move(HEIGHT_MOVE_END)

	def _isStatusReportNotReady(self, buf):
		if buf[0] != CMD_STATUS_REPORT or buf[1] != NRB_STATUS_REPORT:
			return False

		for i in range(2, LEN_STATUS_REPORT - 5):
			if buf[i] != 0:
				return False

		return True

	def _initDevice(self):
		buf = self._getStatusReport()
		if not self._isStatusReportNotReady(buf):
			return
		else:
			print('Device not ready!')

		self._setStatusReport()
		time.sleep(1000/1000000.0)
		if not self._moveEnd():
			raise Exception('Device not ready - initialization failed on step 2 (moveEnd)')

		time.sleep(100000/1000000.0)

	def move(self, target):
		a = max_a = 3
		epsilon = 13
		oldH = 0

		while True:
			self._move(target)
			time.sleep(200000/1000000.0)

			buf = self._getStatusReport()
			r = StatusReport.fromBuf(buf)
			distance = r.ref1cnt - r.ref1.pos
			delta = oldH-r.ref1.pos
			if abs(distance) <= epsilon or abs(delta) <= epsilon or oldH == r.ref1.pos:
				a -= 1
			else:
				a = max_a

			print(
				'Current height: {:d}; target height: {:d}; distance: {:d}'.format(
					r.ref1.pos,
					target,
					distance
				)
			)

			if a == 0:
				break
			oldH = r.ref1.pos

		return abs(r.ref1.pos - target) <= epsilon

	def getHeight(self):
		buf = self._getStatusReport()
		r = StatusReport.fromBuf(buf)

		return r.ref1.pos, r.ref1.pos/98.0

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='Get the control on your desk!')
	parser.add_argument('command', choices=['move', 'height'], help='Command to execute.')
	parser.add_argument('height', type=int, nargs='?', help='For command "move", give the destination height.')

	args = parser.parse_args()
	if args.command == 'move' and not args.height:
		sys.stderr.write('Height missing in case of move!\n')
		parser.print_help()
		sys.exit(1)

	co = LinakController()
	try:
		if args.command == 'move':
			r = co.move(args.height)
			if r:
				print('Command executed successfuly')
			else:
				print('Command failed')
		elif args.command == 'height':
			h, hcm = co.getHeight()
			print('Current height is: {:d} / {:.2f} cm'.format(h, hcm))
	except Exception as e:
		co.close()
		raise e
	finally:
		co.close()
