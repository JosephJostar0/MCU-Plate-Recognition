from time import sleep
from datetime import datetime
import serial
import serial.tools.list_ports
import numpy as np
from PIL import Image
import threading
import pathlib
import queue
from yoloPre import YoloPredictor, waitQueue, runFlag


class PicTools:
    @staticmethod
    def getInt(data: bytes, start: int, end: int) -> int:
        try:
            return int.from_bytes(data[start:end], byteorder='little')
        except Exception as e:
            raise e


class Answer:
    def __init__(self, head, addr, length, cmd, code, crc):
        self.head = head
        self.addr = addr
        self.length = length
        self.cmd = cmd
        self.code = code
        self.crc = crc

    def pack(self) -> bytes:
        return self.head.to_bytes(4, byteorder='little') + self.addr.to_bytes(1, byteorder='little') + self.length.to_bytes(4, byteorder='little') + self.cmd.to_bytes(1, byteorder='little') + self.code.to_bytes(1, byteorder='little') + self.crc.to_bytes(2, byteorder='little')


class PicInfo:
    def __init__(self, addr, picType, width, length):
        self.addr = addr
        self.picType = picType
        self.width = width
        self.length = length

    def show(self):
        print("addr: ", self.addr, end=', ')
        print("picType: ", self.picType, end=', ')
        print("wid: ", self.width, end=', ')
        print("len: ", self.length)


class ReceiveData:
    def __init__(self, head: str, addr, length: int, cmd: str, data: bytes):
        self.head = head
        self.addr = addr
        self.length = length
        self.cmd = cmd
        self.data = data

    @staticmethod
    def fromBytes(data: bytes):
        head = data[0:4]
        addr = data[4]
        length = PicTools.getInt(data, 5, 9)
        cmd = data[9]

        return ReceiveData(head, addr, length, cmd, data)


class ReceivePic:
    global waitQueue, runFlag

    def __init__(self, com: str, baudrate: int, timeout: float, picDir: str, sign: bytes = b'SZHY'):
        self.com = com
        self.baudrate = baudrate
        self.timeout = timeout

        self.picDir = picDir
        self.picIndex = 0

        self.cache = b''
        self.cacheSize = 307201
        self.sign = sign

        self.lock = threading.Lock()

    def getReceiveData(self) -> ReceiveData:
        while True:
            self.cache += self.ser.read_all()
            data: bytes = self.cache
            if self.sign not in data:
                continue
            startIndex = data.index(self.sign)
            if len(data) < startIndex + 10:
                continue
            length = PicTools.getInt(data, startIndex + 5, startIndex + 9)
            if len(data) < startIndex + length:
                continue
            self.cache = data[startIndex + length:]
            if len(self.cache) > self.cacheSize:
                self.cache = self.cache[-18:]
            return ReceiveData.fromBytes(data[startIndex:startIndex + length])

    def sendAnswer(self):
        answer = Answer(
            head=0x59485a53, addr=0x00, length=13,
            cmd=0x00, code=0x00, crc=0x0000,
        )
        self.ser.write(answer.pack())

    def getPicInfo(self):
        while True:
            receiveData = self.getReceiveData()
            if receiveData.cmd == 0x01 and receiveData.length == 18:
                break
        data = receiveData.data
        addr = data[-14]
        picType = data[-8]
        width = PicTools.getInt(data, -7, -5)
        length = PicTools.getInt(data, -5, -3)
        self.sendAnswer()
        self.picInfo = PicInfo(addr, picType, width, length)

    def getPicDataOnce(self):
        picSize = self.picInfo.length * self.picInfo.width * 2
        while True:
            receiveData = self.getReceiveData()
            if receiveData.cmd == 0x02 and receiveData.length == picSize + 12:
                break
        data = receiveData.data
        imgArr = np.frombuffer(data[10:-2], dtype=np.uint8)

        # print(len(data), len(data[10:-2]), imgArr.shape)

        imgArr = imgArr.reshape((self.picInfo.length, self.picInfo.width, 2))
        imgArr888 = np.zeros(
            (self.picInfo.length, self.picInfo.width, 3), dtype=np.uint8)
        imgArr888[:, :, 0] = (imgArr[:, :, 1] & 0xF8)  # 红色部分
        imgArr888[:, :, 1] = ((imgArr[:, :, 1] & 0x07) << 5) | (
            imgArr[:, :, 0] >> 3)  # 绿色部分
        imgArr888[:, :, 2] = (imgArr[:, :, 0] & 0x1F) << 3  # 蓝色部分

        self.msgQueue.put(imgArr888)

    def getPicData(self):
        global runFlag
        while runFlag:
            try:
                self.getPicDataOnce()
            except Exception as e:
                print(e)
                runFlag = False
                break

    def savePic(self):
        global runFlag
        while runFlag:
            try:
                imgArr = self.msgQueue.get(timeout=5)
                # pname = self.picDir + datetime.now().strftime("%y%m%d_%H%M%S") + ".png"
                pname = self.picDir + 'pic' + str(self.picDir) + '.png'
                self.picDir = (self.picDir + 1) % 10

                # cnt = 0
                # temp = pname
                # while pathlib.Path(pname).exists():
                    # pname = temp[:-4] + "(" + str(cnt) + ").png"
                    # cnt += 1

                Image.fromarray(imgArr).save(pname)
                waitQueue.put(pname)
            except queue.Empty:
                runFlag = False
                print("savePic timeout")
                break
            except Exception as e:
                print(e)
                runFlag = False
                break

    def run(self):
        global runFlag, waitQueue
        self.msgQueue = queue.Queue()
        try:  # 打开串口
            self.ser = serial.Serial(
                self.com, baudrate=self.baudrate, timeout=self.timeout)
            self.ser.bytesize = serial.EIGHTBITS  # 8位字符
            self.ser.stopbits = serial.STOPBITS_ONE  # 1位停止位
        except Exception as e:
            runFlag = False
            print(e)
            return

        # print("Waiting data from:"+self.ser.name)

        if not pathlib.Path(self.picDir).exists():
            pathlib.Path(self.picDir).mkdir(parents=True)

        try:  # 接收数据
            self.getPicInfo()
            self.picInfo.show()

            getPicThread = threading.Thread(target=self.getPicData)
            savePicThread = threading.Thread(target=self.savePic)
            getPicThread.start()
            savePicThread.start()
            getPicThread.join()
            savePicThread.join()
        except Exception as e:
            print(e)
        finally:
            self.ser.close()


def main():
    global runFlag
    receivePic = ReceivePic("COM5", 1500000, 1.5, r"./runs/saveImg/")
    yolo = YoloPredictor()
    yolo.beforeRun(r'./models/car.pt')
    print("start")
    try:
        receiveThread = threading.Thread(target=receivePic.run)
        yoloThread = threading.Thread(target=yolo.run)
        receiveThread.start()
        yoloThread.start()
        receiveThread.join()
        yoloThread.join()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except Exception as e:
        print(e)
    finally:
        runFlag = False
        print("all threads end")


if __name__ == '__main__':
    main()
