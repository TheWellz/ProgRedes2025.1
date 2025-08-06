import socket, os, threading, glob

SERVIDOR = ""
PORTA = 2121
PASTAARQ = "arquivos"
allClients = []

def escutaPorta():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVIDOR, PORTA))
    sock.listen(5)

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

def respondeComandoDow(nomeArquivo):
    nomeArquivo = os.path.join(PASTAARQ, nomeArquivo)
    if not os.path.exists(nomeArquivo):
        sockCon.send((0).to_bytes(4, 'big'))
        return

    tamArquivo = os.path.getsize(nomeArquivo)
    sockCon.send(tamArquivo.to_bytes(4, 'big'))

    with open(nomeArquivo, "rb") as fd:
        dados = fd.read(8192)
        while dados:
            sockCon.send(dados)
            dados = fd.read(8192)

def respondeComandoDMA(mascara):
    caminhoMascara = os.path.join(PASTAARQ, mascara)
    arquivosEncontrados = glob.glob(caminhoMascara)
    nomesArquivos = [os.path.basename(arquivo) for arquivo in arquivosEncontrados]

    if not nomesArquivos:
        sockCon.send(adicionaTamanho(b''))
        return

    listaNomeArquivos = "\n".join(nomesArquivos).encode()
    sockCon.send(adicionaTamanho(listaNomeArquivos))

    for nomeArquivo in nomesArquivos:
        respostaCliente = leComando()
        if respostaCliente == b"SKIP":
            continue
        elif respostaCliente == b"OK":
            respondeComandoDow(nomeArquivo)

def processaComando(comando):
    if comando[:3] == b'DIR':
        respondeComandoDir()
    elif comando[:3] == b'DOW':
        respondeComandoDow(comando[3:].decode()) 
    elif comando[:3] == b'DMA':
        respondeComandoDMA(comando[3:].decode())
    else:
        respondeComandoNulo()

def trataCliente(sockConexao, cliente):
    global sockCon
    sockCon = sockConexao
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
    escutaPorta()
    print("Escutando conexões ....")
    while True:
        sockConexao, cliente = sock.accept()
        print("Conexão recebida de", cliente)
        threading.Thread(target=trataCliente, args=(sockConexao, cliente)).start()

main()
