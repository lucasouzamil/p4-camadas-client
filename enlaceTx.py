#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
#Carareto
#17/02/2018
#  Camada de Enlace
####################################################

# Importa pacote de tempo
import time

# Threads
import threading

# Class
class TX(object):
 
    def __init__(self, fisica):
        self.fisica      = fisica
        self.buffer      = bytes(bytearray())
        self.transLen    = 0
        self.empty       = True
        self.threadMutex = False
        self.threadStop  = False


    def thread(self):
        while not self.threadStop:
            if(self.threadMutex):
                print('\n\n\n\ AAA \n\n\n')
                self.transLen    = self.fisica.write(self.buffer)
                self.threadMutex = False

    def threadStart(self):
        self.thread = threading.Thread(target=self.thread, args=())
        self.thread.start()

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def sendBuffer(self, data):
        self.transLen   = 0
        self.buffer = data
        self.threadMutex  = True

    def getBufferLen(self):
        return(len(self.buffer))

    def getStatus(self):
        while self.threadMutex == True:
            time.sleep(0.05)
        return(self.transLen) 

    def getIsBussy(self):
        return(self.threadMutex)

