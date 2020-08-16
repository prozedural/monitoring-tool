import config
import tisgrabber as IC



#prüfe Status der Kamera

def status(Camera):

    if Camera.openVideoCaptureDevice(config.DEVICE) == 1:
        print(config.DEVICE, 'ist aktiv')
    else:
        print(config.DEVICE, 'ist inaktiv')