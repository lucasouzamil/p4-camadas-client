#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 

from funcao import *
from enlace import *
import time
import numpy as np
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM5"                   # Windows(variacao de)


def main():
    try:
        print('')
        print("Iniciou o main")
        #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
        #para declarar esse objeto é o nome da porta.
        com1 = enlace(serialName)
    
        # Ativa comunicacao. Inicia os threads e a comunicação seiral 
        com1.enable()
        #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
        print("Abriu a comunicação")
        print('')

        #Endereco da imagem a ser transmitida
        imageR = open("img/helloworld.jpg",'rb').read()
        #print(imageR)
        # Carrega imagem
        print("Carregando imagem para transmissão:")
        print(f" - {imageR}")
        print("-"*35)
        #txBuffer = imagem em bytes!
        #pacotes = cria_pacotes(b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef')
        pacotes = cria_pacotes(imageR,'tam_errado')
    
        
        print('Enviando byte de sacrificio')
        com1.sendData(np.asarray(b'x00'))    #enviar byte de lixo
        time.sleep(.05)
        com1.rx.clearBuffer()

        print('Esperando byte de sacrificio')
        rxBuffer, nRx, check = com1.getData_teste(1)
        time.sleep(.05)
        com1.rx.clearBuffer()


        tempo_inicial = time.time()
        duracao_maxima = 5 
        recebeu = False
        transmissao = True
        i = 0
        cn=False
        print('Iniciando transminssão de pacotes')
        while (i < len(pacotes['bytearray'])) and transmissao:
            txBuffer = pacotes['bytearray'][i]
            print(f"Enviou {i}/{len(pacotes['bytearray'])} pacotes")
            com1.sendData(np.asarray(txBuffer)) 
            time.sleep(.05)

            while (time.time() - tempo_inicial < duracao_maxima) and i == 0:
                if com1.rx.getBufferLen() > 0:
                    rxBuffer, nRx, check = com1.getData_teste(15)
                    time.sleep(.05)
                    recebeu = True
                    i += 1
                    break
                print(f'{time.time() - tempo_inicial}s')
                time.sleep(0.1)

            if recebeu == False:
                print("O servidor não estava pronto para começar a transmissão.")
                pergunta = input("Deseja iniciar a comunicação novamente? (S/N)")
                if pergunta.lower() == 's':
                    transmissao = True
                    tempo_inicial = time.time()
                else:
                    transmissao = False

            if (transmissao == True) and (i > 0):
                if recebeu == True and cn: 
                    check = False
                    while not check:
                        rxBuffer, nRx, check = com1.getData_teste(15)
                        if check == False:
                            com1.sendData(np.asarray(txBuffer)) 
                        time.sleep(.05)
                        com1.rx.clearBuffer()
                    print(f'Recebeu  --->   {rxBuffer}')
                    int_list = [int(byte) for byte in rxBuffer]
                    if (int_list[0] == i) and int_list[-3:]==[255]*3:
                        i+=1
                    com1.rx.clearBuffer()
                cn=True

        com1.disable()
        
    except Exception as erro:
        print("ops! :-\\")
        print(erro)
        com1.disable()

    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
