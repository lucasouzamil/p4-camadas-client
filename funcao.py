from enlace import *
import numpy as np
import time
import crcmod

def cria_pacotes(arquivo, simulado='a'):

    payloads=[]
    num_tot_pacotes=len(str(arquivo).lower().split("x"))//50
    for i in list(range(0, num_tot_pacotes)):
        payloads.append(arquivo[i*50:(i+1)*50])
    payloads.append(arquivo[num_tot_pacotes*50:])

    qntdpayloads = len(payloads)
    pacotes = {'bytearray':[],'inteiro':[]}
    pacotes['inteiro'].append([[0,num_tot_pacotes+1,12+3+len(payloads[1]),0,0,0,0,0,0,0,0,0],[],[255,255,255]])
    pacotes['bytearray'].append(bytes([0,num_tot_pacotes+1,12+3+len(payloads[1]),0,0,0,0,0,0,0,0,0])+bytes([255,255,255]))
    for n in range(0, qntdpayloads):
        head = [0]*12
        if simulado == "indice_errado" and n == qntdpayloads/2: 
            head[0]=6
        else:
            head[0]=n+1
        head[1]=num_tot_pacotes+1

        try:
            if simulado == "tam_errado" and n == qntdpayloads/2: 
                head[2]=10
            else:
                head[2]=12+3+len(payloads[n+1])
        except:
            head[2]=0

        head[3]=12+3+len(payloads[n])

        if simulado == "eop_errado" and n == qntdpayloads/2: 
            eop=[0,255,255]
        else:
            eop=[255,255,255]
        payload=payloads[n]
        pacotes['bytearray'].append(bytes(head)+payload+bytes(eop))
        pacotes['inteiro'].append([head,payload,eop])
    
    return pacotes

class Client:

    def __init__(self, porta: str) -> None:
        self.porta         = porta
        self.datagramas    = []
        self.PACOTE_ESTRUT = {
            'head':   [0]*10,
            'payload':[],
            'eop':    b'\xAA\xBB\xCC\xDD',
            }
        
        try:
            self.com=enlace(porta)
            self.com.enable()
            time.sleep(1)
            self.__enviaByteSacrificio()

        except Exception as erro:
            print("Erro ao iniciar cliente! :-\\")
            print(erro)
            self.com.disable()

    def __enviaByteSacrificio(self) -> None:
        print('Enviando byte de sacrificio')
        self.com.sendData(np.asarray(b'x00'))    #enviar byte de lixo
        #self.com.rx.clearBuffer()
        time.sleep(.05)
    
    def __criaDatagrama(self, arquivo: bytearray, id_arquivo: int, id_servidor: int, tam_paylaod: int) -> list:
        pacote  = {
                'head':   [0]*10,
                'payload':[],
                'eop':    b'\xAA\xBB\xCC\xDD',
                }
        datagrama = []

        #Separa arquivo em payloads
        num_tot_pacotes=len(str(arquivo).lower().split("x"))//tam_paylaod
        for i in list(range(0, num_tot_pacotes)):
            pacote['payload'].append(arquivo[i*tam_paylaod:(i+1)*tam_paylaod])
        if (len(str(arquivo).lower().split("x"))%tam_paylaod > 0):
            pacote['payload'].append(arquivo[num_tot_pacotes*tam_paylaod:])
        pacote['payload'].insert(0,b'')

        #Criando pacotes:
        QNTD_PACOTES=len(pacote['payload'])
        pacote['head']=[pacote['head']]*QNTD_PACOTES
        pacote['eop']=[pacote['eop']]*QNTD_PACOTES
        for n in range(0, len(pacote['payload'])):
            # HANDSHAKE
            # TIPO 1 – Esta mensagem representa um chamado do cliente enviado ao servidor convidando-o 
            # para a transmissão. Nesse caso, o head deve conter o byte h0 com o número 1, indicando 
            # mensagem tipo 1, e o segundo byte com um identificador. O identificador é o número do 
            # servidor, sendo que quando este receber uma mensagem tipo 1, verifica se é para ele mesmo
            # o envio. A mensagem tipo 1 já deve conter o número total de pacotes que se pretende enviar!
            if n == 0:
                pacote['head'][n][0]=1 #TIPO handshake
                pacote['head'][n][1]=id_servidor
                pacote['head'][n][3]=QNTD_PACOTES-1 #A quantidade de payloads é uma a menos que quantidade de pacotes, já que no handshake o payload é vazio.
                pacote['head'][n][5]=id_arquivo # Se tipo for handshake: id do arquivo 

            # DADOS
            # TIPO 3 – A mensagem tipo 3 é a mensagem de dados. Este tipo de mensagem contém de fato um
            # bloco do dado a ser enviado (payload). Deve conter o número 3 no byte reservado ao tipo 
            # de mensagem. Essa mensagem deve conter também o número do pacote que envia (começando do 1)
            # e o total de pacotes a serem enviados. 
            else:
                pacote['head'][n][0]=3 #TIPO dados
                pacote['head'][n][1]=0
                pacote['head'][n][3]=QNTD_PACOTES-1
                pacote['head'][n][4]=n
                pacote['head'][n][5]=len(pacote['payload'][n]) # Se tipo for dados: tamanho do payload.
                crc = self.__criaCRC(pacote['payload'][n])
                pacote['head'][n][8]=crc[0]
                pacote['head'][n][9]= crc[1]

            
            #print(pacote['head'][n],pacote['payload'][n],pacote['eop'][n])
            #print('')
            pacote['head'][n]=bytes(pacote['head'][n])
            datagrama.append(pacote['head'][n]+(pacote['payload'][n]+pacote['eop'][n]))

        return datagrama
    
    def enviaDatagrama(self, arquivo: bytearray, id_arquivo: int, id_servidor: int, tam_paylaod: int):
        datagrama = self.__criaDatagrama(arquivo, id_arquivo, id_servidor, tam_paylaod)
        for d in datagrama:
            print(d)
            print('')

        inicia = False
        cont = 0
        while not(inicia):
            print('')
            print('Envia handshake')
            self.com.sendData(np.asarray(datagrama[0]))    #enviar byte de lixo
            time.sleep(.05)
            if self.getFeedback()[0] == 2:
                print('[HANDSHAKE EFETUADO]: Inicia transmissão de pacotes')
                inicia = True
                cont   = 1
                break
            time.sleep(4.95)
        
        num_pacotes = datagrama[0][3]
        while (cont <= num_pacotes) and inicia:
            print(f'Pacote [{cont}/{num_pacotes}] enviado')
            self.com.sendData(np.asarray(datagrama[cont])) 
            time.sleep(.05)
            timer1 = time.time()
            timer2 = timer1

            feedback, check = self.com.rx.getNData_timer(14,10)
            if not check:
                print('[ERRO] Tempo de espera excedido')
                break
            else:
                feedback = [int(byte) for byte in feedback]

            tipo = feedback[0]

            if tipo == 5:
                break

            if tipo == 4:
                cont = feedback[7]+1
            else:
                if ((time.time()-timer1) > 5):
                    self.com.sendData(np.asarray(datagrama[cont]))
                    time.sleep(.05)
                    timer1 = time.time()
                print(time.time()-timer2)
                if ((time.time()-timer2) > 20):
                    self.com.sendData(np.asarray(b'\x05\x00\x00\x00\x00\x00\x00\x00\x00\x00\xAA\xBB\xCC\xDD'))
                    time.sleep(.05)
                    break

                else:
                    if tipo == 6:
                        cont = feedback[6]
                        self.com.sendData(np.asarray(datagrama[cont]))
                        time.sleep(.05)
                        timer1 = time.time()
                        timer2 = timer1

        if cont > num_pacotes:
            print('[SUCESSO] Todos pacotes foram enviados')
        else:
            print('[ERRO] Falha na comunicação')
    
    def __criaCRC(self, payload: bytearray):
        crc16 = crcmod.predefined.Crc('crc-16') 
        crc16.update(bytes(payload))
        crc_value = crc16.crcValue
        byte_array = int.to_bytes(crc_value, 2, byteorder='big')
        return byte_array

    def getFeedback(self):
        rxBuffer, nRx = self.com.getData(14)
        return [int(byte) for byte in rxBuffer]

    def off(self):
        self.com.disable()
        self=None


def criaDatagrama(arquivo: bytearray, id_arquivo: int, id_servidor: int, tam_paylaod: int) -> list:
    pacote  = {
            'head':   [0]*10,
            'payload':[],
            'eop':    b'\xAA\xBB\xCC\xDD',
            }
    datagrama = []

    #Separa arquivo em payloads
    num_tot_pacotes=len(str(arquivo).lower().split("x"))//tam_paylaod
    for i in list(range(0, num_tot_pacotes)):
        pacote['payload'].append(arquivo[i*tam_paylaod:(i+1)*tam_paylaod])
    if (len(str(arquivo).lower().split("x"))%tam_paylaod > 0):
        pacote['payload'].append(arquivo[num_tot_pacotes*tam_paylaod:])
    pacote['payload'].insert(0,b'')

    #Criando pacotes:
    QNTD_PACOTES=len(pacote['payload'])
    pacote['head']=[pacote['head']]*QNTD_PACOTES
    pacote['eop']=[pacote['eop']]*QNTD_PACOTES
    for n in range(0, len(pacote['payload'])):
        # HANDSHAKE
        # TIPO 1 – Esta mensagem representa um chamado do cliente enviado ao servidor convidando-o 
        # para a transmissão. Nesse caso, o head deve conter o byte h0 com o número 1, indicando 
        # mensagem tipo 1, e o segundo byte com um identificador. O identificador é o número do 
        # servidor, sendo que quando este receber uma mensagem tipo 1, verifica se é para ele mesmo
        # o envio. A mensagem tipo 1 já deve conter o número total de pacotes que se pretende enviar!
        if n == 0:
            pacote['head'][n][0]=1 #TIPO handshake
            pacote['head'][n][1]=id_servidor
            pacote['head'][n][3]=QNTD_PACOTES-1 #A quantidade de payloads é uma a menos que quantidade de pacotes, já que no handshake o payload é vazio.
            pacote['head'][n][5]=id_arquivo # Se tipo for handshake: id do arquivo 

        # DADOS
        # TIPO 3 – A mensagem tipo 3 é a mensagem de dados. Este tipo de mensagem contém de fato um
        # bloco do dado a ser enviado (payload). Deve conter o número 3 no byte reservado ao tipo 
        # de mensagem. Essa mensagem deve conter também o número do pacote que envia (começando do 1)
        # e o total de pacotes a serem enviados. 
        else:
            pacote['head'][n][0]=3 #TIPO dados
            pacote['head'][n][1]=0
            pacote['head'][n][3]=QNTD_PACOTES-1
            pacote['head'][n][4]=n
            pacote['head'][n][5]=len(pacote['payload'][n]) # Se tipo for dados: tamanho do payload.
        
        #print(pacote['head'][n],pacote['payload'][n],pacote['eop'][n])
        #print('')
        pacote['head'][n]=bytes(pacote['head'][n])
        datagrama.append(pacote['head'][n]+(pacote['payload'][n]+pacote['eop'][n]))

    return datagrama


#   h0 – Tipo de mensagem.
#   h1 – Se tipo for 1: número do servidor. Qualquer outro tipo: livre
#   h2 – Livre.
#   h3 – Número total de pacotes do arquivo.
#   h4 – Número do pacote sendo enviado.
#   h5 – Se tipo for handshake: id do arquivo (crie um para cada arquivo). Se tipo for dados: tamanho do payload.
#   h6 – Pacote solicitado para recomeço quando a erro no envio.
#   h7 – Ùltimo pacote recebido com sucesso.
#   h8 – h9 – CRC (Por ora deixe em branco. Fará parte do projeto 5).
#   PAYLOAD – variável entre 0 e 114 bytes. Reservado à transmissão dos arquivos.
#   EOP – 4 bytes: 0xAA 0xBB 0xCC 0xDD.

#cliente = Client('COM3')
#arquivo = b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef'*4
#cliente.criaDatagrama(arquivo,1,1,114)


#cria_pacotes_4(b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef'*10)

