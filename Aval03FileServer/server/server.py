import socket, os, threading

SERVIDOR = ""
PORTA    = 2121
PASTAARQ = "arquivos"
allClients = []

def escutaPorta():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVIDOR, PORTA))
    sock.listen(1)
    
def leComando():
    tamanhoComando = int.from_bytes(sockCon.recv(4), byteorder='big')
    comando = b''
    while tamanhoComando > 0:
        leitura = sockCon.recv(tamanhoComando)
        tamanhoComando -= len(leitura)
        comando += leitura
    return comando

def adicionaTamanho(dados):
    tamanho = len(dados)
    return tamanho.to_bytes(4, byteorder='big') + dados

def respondeComandoNulo():
    sockCon.send(adicionaTamanho(b''))

def respondeComandoDir():
    listaArquivos = os.listdir(PASTAARQ)
    resposta = ""

    for nomeArquivo in listaArquivos:
        caminhoCompleto = os.path.join(PASTAARQ, nomeArquivo)
        if os.path.isfile(caminhoCompleto):
            tamanhoArquivo = os.path.getsize(caminhoCompleto)
            resposta += f"{nomeArquivo} - {tamanhoArquivo} bytes\r\n"

    sockCon.send(adicionaTamanho(resposta.encode()))

def respondeComandoDownload(nomeArquivo):
    nomeArquivo = PASTAARQ + "/" + nomeArquivo
    tamArquivo = os.path.getsize(nomeArquivo)
    sockCon.send(tamArquivo.to_bytes(4, 'big'))

    fd = open(nomeArquivo, "rb")
    dados = fd.read(8192)
    while dados != b'':
        sockCon.send(dados)
        dados = fd.read(8192)
    fd.close()

def processaComando(comando):
    if comando[:3] == b'DIR':
        respondeComandoDir()
    elif comando[:3] == b'DOW':
        respondeComandoDownload(comando[4:].decode())
    else:
        respondeComandoNulo()

def trataCliente(sockCon, cliente):
    print(f"Tratando conexão com {cliente}")
    allClients.append(sockCon)
    try:
        while True:
            comando = leComando()
            if comando:
                processaComando(comando)
            else:
                allClients.remove(sockCon)
                sockCon.close()
                print("Fechando conexão porque o cliente fechou.")
                break
    except:
        allClients.remove(sockCon)
        sockCon.close()
        print("Fechando conexão porque o servidor caiu abruptamente.")

def main():
    global sockCon, cliente

    escutaPorta()
    print("Escutando conexões ....")
    while True:
        sockCon, cliente = sock.accept()
        print("Conexão recebida de", cliente)
        threading.Thread(target=trataCliente, args=(sockCon, cliente)).start()

main()
