from funcao import *
from enlace import *
import numpy as np
import time

def cria_pacotes(arquivo, simulado='a'):

    payloads=[]
    num_tot_pacotes=len(str(arquivo).lower().split("x"))//114
    for i in list(range(0, num_tot_pacotes)):
        payloads.append(arquivo[i*114:(i+1)*114])
    payloads.append(arquivo[num_tot_pacotes*114:])

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
#pacotes = cria_pacotes(b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef')

class Client:

    def __init__(self, porta: str) -> None:
        self.porta         = porta
        self.arquivo       = None
        self.datagramas    = []
        self.PACOTE_ESTRUT = {
            'head':   [0]*10,
            'payload':[],
            'eop':    b'\xAA\xBB\xCC\xDD',
            }
        
        """ try:
            self.com1 = enlace(self.porta)
            self.enable()
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.com1.disable() """

    def criaDatagrama(self, arquivo: bytearray, id_arquivo: int, id_servidor: int, tam_paylaod: int) -> None:
        pacote  = self.PACOTE_ESTRUT
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
            
            pacote['head'][n]=bytes(pacote['head'][n])
            datagrama.append(pacote['head'][n]+(pacote['payload'][n]+pacote['eop'][n]))

        self.datagramas.append(datagrama)
        #print(self.datagramas)
       

    def enviaByteSacrificio(self) -> None:
        print('Enviando byte de sacrificio')
        try:
            self.com1.sendData(np.asarray(b'x00'))    #enviar byte de lixo
            time.sleep(.05)
            self.com1.rx.clearBuffer()
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.com1.disable()
    
    def recebeByteSacrificio(self) -> None:
        print('Esperando byte de sacrificio')
        try:
            check = False
            while not check:
                rxBuffer, nRx, check = self.com1.getData_teste(1)
                time.sleep(.05)
                self.com1.rx.clearBuffer()
            return None
        except Exception as erro:
            print("ops! :-\\")
            print(erro)
            self.com1.disable()

   # def enviaDatagrama(self, id_arquivo: int):
        


    def getFeedback(self, n: int):
        rxBuffer, nRx, check = self.com1.getData_teste(n)
        return rxBuffer, nRx, check
            


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

cliente = Client('COM3')
arquivo = b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef'*4
cliente.criaDatagrama(arquivo,1,1,114)
print(cliente.datagramas[-1])



#cria_pacotes_4(b'\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef'*10)
