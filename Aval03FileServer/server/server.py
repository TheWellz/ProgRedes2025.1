import socket, os, threading, glob, hashlib

SERVIDOR = ""
PORTA = 2121
PASTAARQ = "arquivos"
allClients = []

def escutaPorta():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVIDOR, PORTA))
    sock.listen(5)

def leComando(sockCon):
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

def pastaPermitida(caminhoArquivo, pastaBase):
    caminhoRealArquivo = os.path.realpath(caminhoArquivo)
    caminhoRealPastaBase = os.path.realpath(pastaBase)
    caminhoRealPastaBase = os.path.join(caminhoRealPastaBase, '')
    return caminhoRealArquivo.startswith(caminhoRealPastaBase)

def respondeComandoNulo(sockCon):
    sockCon.send(adicionaTamanho(b''))

def respondeComandoDir(sockCon):
    listaArquivos = os.listdir(PASTAARQ)
    resposta = ""
    for nomeArquivo in listaArquivos:
        caminhoCompleto = os.path.join(PASTAARQ, nomeArquivo)
        if os.path.isfile(caminhoCompleto):
            tamanhoArquivo = os.path.getsize(caminhoCompleto)
            resposta += f"{nomeArquivo} - {tamanhoArquivo} bytes\r\n"
    sockCon.send(adicionaTamanho(resposta.encode()))

def respondeComandoDow(sockCon, nomeArquivo):
    nomeArquivo = os.path.join(PASTAARQ, nomeArquivo)

    if not pastaPermitida(nomeArquivo, PASTAARQ):
        sockCon.send(adicionaTamanho(b''))
        return

    if not os.path.exists(nomeArquivo):
        sockCon.send(adicionaTamanho(b''))
        return

    tamArquivo = os.path.getsize(nomeArquivo)
    sockCon.send(tamArquivo.to_bytes(4, 'big'))

    with open(nomeArquivo, "rb") as fd:
        dados = fd.read(8192)
        while dados:
            sockCon.send(dados)
            dados = fd.read(8192)

def respondeComandoDMA(sockCon, mascara):
    caminhoMascara = os.path.join(PASTAARQ, mascara)
    arquivosEncontrados = glob.glob(caminhoMascara)
    nomesArquivos = []

    for arquivo in arquivosEncontrados:
        caminhoArquivo = os.path.realpath(arquivo)
        if pastaPermitida(caminhoArquivo, PASTAARQ):
            nomesArquivos.append(os.path.basename(arquivo))

    if not nomesArquivos:
        sockCon.send(adicionaTamanho(b''))
        return

    listaNomeArquivos = "\n".join(nomesArquivos).encode()
    sockCon.send(adicionaTamanho(listaNomeArquivos))

    for nomeArquivo in nomesArquivos:
        respostaCliente = leComando(sockCon)
        if respostaCliente == b"SKIP":
            continue
        elif respostaCliente == b"OK":
            respondeComandoDow(sockCon, nomeArquivo)

def respondeComandoMd5(sockCon, dados):
    texto = dados.decode()
    nomeArquivo, posicaoStr = texto.split('|')
    posicao = int(posicaoStr)

    caminhoArquivo = os.path.join(PASTAARQ, nomeArquivo)
    if not pastaPermitida(caminhoArquivo, PASTAARQ):
        sockCon.send(adicionaTamanho(b''))
        return
            
    if not os.path.exists(caminhoArquivo):
        sockCon.send(adicionaTamanho(b''))
        return

    fd = open(caminhoArquivo, "rb")
    conteudo = fd.read(posicao)
    fd.close()

    md5hash = hashlib.md5(conteudo).hexdigest()
    sockCon.send(adicionaTamanho(md5hash.encode()))

def respondeComandoDra(sockCon, dados):
    try:
        texto = dados.decode()
        nomeArquivo, posicaoStr, hashCliente = texto.split('|')
        posicao = int(posicaoStr)

        caminhoArquivo = os.path.join(PASTAARQ, nomeArquivo)

        if not pastaPermitida(caminhoArquivo, PASTAARQ):
            sockCon.send(adicionaTamanho(b''))
            return

        if not os.path.exists(caminhoArquivo):
            sockCon.send(adicionaTamanho(b''))
            return
        
        fd = open(caminhoArquivo, "rb")
        bytesIniciais = fd.read(posicao)

        if hashlib.md5(bytesIniciais).hexdigest() != hashCliente:
            fd.close()
            sockCon.send(adicionaTamanho(b''))
            return
        
        bytesRestantes = fd.read()
        fd.close()

        sockCon.send(adicionaTamanho(bytesRestantes))

    except:
        sockCon.send(adicionaTamanho(b''))

def processaComando(sockCon, comando):
    if comando[:3] == b'DIR':
        respondeComandoDir(sockCon)
    elif comando[:3] == b'DOW':
        respondeComandoDow(sockCon, comando[3:].decode())
    elif comando[:3] == b'DMA':
        respondeComandoDMA(sockCon, comando[3:].decode())
    elif comando[:3] == b'MD5':
        respondeComandoMd5(sockCon, comando[3:])
    elif comando[:3] == b'DRA':
        respondeComandoDra(sockCon, comando[3:])
    else:
        respondeComandoNulo(sockCon)

def trataCliente(sockConexao, cliente):
    print(f"Tratando conexão com {cliente}")
    allClients.append(sockConexao)
    try:
        while True:
            comando = leComando(sockConexao)
            if comando:
                processaComando(sockConexao, comando)
            else:
                allClients.remove(sockConexao)
                sockConexao.close()
                print("Fechando conexão porque o cliente fechou.")
                break
    except Exception as e:
        print(f"[{cliente}] Erro: {e}") 
        if sockConexao in allClients:
            allClients.remove(sockConexao)
        try:
            sockConexao.close()
        except:
            pass
        print(f"[{cliente}] Conexão finalizada com erro.")

def main():
    escutaPorta()
    print("Escutando conexões ....")
    while True:
        sockConexao, cliente = sock.accept()
        print("Conexão recebida de", cliente)
        threading.Thread(target=trataCliente, args=(sockConexao, cliente)).start()

main()