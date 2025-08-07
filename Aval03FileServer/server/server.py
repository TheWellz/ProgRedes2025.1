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
    tamanhoComando = int.from_bytes(sockCon.recv(4), byteorder='big')  # Lê os primeiros 4 bytes (tamanho do comando)
    comando = b''  
    while tamanhoComando > 0:
        leitura = sockCon.recv(tamanhoComando)  
        tamanhoComando -= len(leitura)  
        comando += leitura 
    return comando  #

def adicionaTamanho(dados):
    tamanho = len(dados)  
    return tamanho.to_bytes(4, byteorder='big') + dados  # Retorna dados com cabeçalho de tamanho

def pastaPermitida(caminhoArquivo, pastaBase):
    caminhoRealArquivo = os.path.realpath(caminhoArquivo)  # Caminho absoluto e resolvido do arquivo
    caminhoRealPastaBase = os.path.realpath(pastaBase)  # Caminho absoluto da pasta base
    caminhoRealPastaBase = os.path.join(caminhoRealPastaBase, '')  # Garante que termina com separador
    return caminhoRealArquivo.startswith(caminhoRealPastaBase)  # Verifica se o arquivo está dentro da pasta base

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

    if not pastaPermitida(nomeArquivo, PASTAARQ):  # Verifica se está dentro da pasta permitida
        sockCon.send(adicionaTamanho(b'')) 
        return

    if not os.path.exists(nomeArquivo):  # Verifica se o arquivo existe
        sockCon.send(adicionaTamanho(b''))  
        return

    tamArquivo = os.path.getsize(nomeArquivo)  
    sockCon.send(tamArquivo.to_bytes(4, 'big'))  

    with open(nomeArquivo, "rb") as fd:
        dados = fd.read(8192) 
        while dados:
            sockCon.send(dados)  
            dados = fd.read(8192)  # 

def respondeComandoDMA(sockCon, mascara):
    caminhoMascara = os.path.join(PASTAARQ, mascara)  # Cria o caminho com a máscara
    arquivosEncontrados = glob.glob(caminhoMascara)  # Busca arquivos que correspondem à máscara
    nomesArquivos = []  # Lista de arquivos válidos

    for arquivo in arquivosEncontrados:
        caminhoArquivo = os.path.realpath(arquivo)  # Resolve caminho real
        if pastaPermitida(caminhoArquivo, PASTAARQ):  # Verifica se é permitido
            nomesArquivos.append(os.path.basename(arquivo))  # Adiciona nome do arquivo

    if not nomesArquivos: 
        sockCon.send(adicionaTamanho(b'')) 
        return

    listaNomeArquivos = "\n".join(nomesArquivos).encode()  # Junta todos os nomes em uma string
    sockCon.send(adicionaTamanho(listaNomeArquivos)) 

    for nomeArquivo in nomesArquivos: 
        respostaCliente = leComando(sockCon)  # Espera confirmação do cliente
        if respostaCliente == b"SKIP":  # Cliente optou por pular
            continue
        elif respostaCliente == b"OK":  # Cliente quer baixar
            respondeComandoDow(sockCon, nomeArquivo)  # Envia arquivo

def respondeComandoMd5(sockCon, dados):
    texto = dados.decode() 
    nomeArquivo, posicaoStr = texto.split('|')  
    posicao = int(posicaoStr)  

    caminhoArquivo = os.path.join(PASTAARQ, nomeArquivo) 
    if not pastaPermitida(caminhoArquivo, PASTAARQ):  # Verifica permissão
        sockCon.send(adicionaTamanho(b''))  
        return
            
    if not os.path.exists(caminhoArquivo):  # Verifica existência do arquivo
        sockCon.send(adicionaTamanho(b''))  #
        return

    fd = open(caminhoArquivo, "rb") 
    conteudo = fd.read(posicao)  
    fd.close() 

    md5hash = hashlib.md5(conteudo).hexdigest()  # Gera hash MD5
    sockCon.send(adicionaTamanho(md5hash.encode()))  # Envia hash ao cliente

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
        sockCon.send(adicionaTamanho(b''))  # 

def processaComando(sockCon, comando):
    if comando[:3] == b'DIR':  # Comando de listagem
        respondeComandoDir(sockCon)
    elif comando[:3] == b'DOW':  # Comando de download
        respondeComandoDow(sockCon, comando[3:].decode())
    elif comando[:3] == b'DMA':  # Comando de download com máscara
        respondeComandoDMA(sockCon, comando[3:].decode())
    elif comando[:3] == b'MD5':  # Comando de hash MD5 parcial
        respondeComandoMd5(sockCon, comando[3:])
    elif comando[:3] == b'DRA':  # Comando de retomada de download
        respondeComandoDra(sockCon, comando[3:])
    else:
        respondeComandoNulo(sockCon) 

def trataCliente(sockConexao, cliente):
    print(f"Tratando conexão com {cliente}")  
    allClients.append(sockConexao)  # Adiciona à lista de conexões
    try:
        while True:
            comando = leComando(sockConexao)  # Espera comando do cliente
            if comando:
                processaComando(sockConexao, comando)  # Processa comando
            else:
                allClients.remove(sockConexao)  # Remove da lista
                sockConexao.close()  # Fecha conexão
                print("Fechando conexão porque o cliente fechou.") 
                break
    except Exception as e:
        print(f"[{cliente}] Erro: {e}") 
        if sockConexao in allClients:
            allClients.remove(sockConexao)  # Remove da lista se ainda estiver
        try:
            sockConexao.close()  # Tenta fechar conexão
        except:
            pass
        print(f"[{cliente}] Conexão finalizada com erro.") 

def main():
    escutaPorta()  # Inicia o socket para escutar
    print("Escutando conexões ....") 
    while True:
        sockConexao, cliente = sock.accept()  # Aceita nova conexão
        print("Conexão recebida de", cliente)  
        threading.Thread(target=trataCliente, args=(sockConexao, cliente)).start()  # Inicia nova thread para o cliente

main() 
