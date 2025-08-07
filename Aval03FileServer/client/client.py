import socket, os, hashlib

SERVIDOR = "localhost"
PORTA = 2121

def conectaAoServidor():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVIDOR, PORTA))

def mostraOpcoes():
    while True:
        try:
            print("\n1 - Lista arquivos no servidor")
            print("2 - Download de um arquivo")
            print("3 - Download de arquivos com máscara")
            print("4 - Obter hash MD5 parcial de arquivo")
            print("5 - Retomar download de arquivo")
            print("6 - Fim")
            opcao = int(input("Escolha uma opção: "))
            return opcao
        except ValueError:
            print("\nErro: entrada inválida, digite apenas números.")

def adicionaTamanho(dados):
    tamanho = len(dados)
    return tamanho.to_bytes(4, byteorder='big') + dados

def listaArquivos():
    comando = b"DIR"
    sock.send(adicionaTamanho(comando))

    tamanhoListagem = int.from_bytes(sock.recv(4), byteorder='big')
    while tamanhoListagem > 0:
        resposta = sock.recv(tamanhoListagem)
        tamanhoListagem -= len(resposta)
        print(resposta.decode())

def obterArquivo(nomeArquivo):
    os.makedirs("downloads", exist_ok=True)
    caminhoArquivo = os.path.join("downloads", nomeArquivo)

    if os.path.exists(caminhoArquivo):
        resposta = input(f"O arquivo '{nomeArquivo}' já existe. Sobrescrever? (s/n): ").lower()
        if resposta != 's':
            sock.send(adicionaTamanho(b"SKIP"))
            print(f"Pulando o arquivo '{nomeArquivo}'.")
            return
        else:
            sock.send(adicionaTamanho(b"OK"))
    else:
        sock.send(adicionaTamanho(b"OK"))

    tamanhoArquivo = int.from_bytes(sock.recv(4), byteorder='big')
    if tamanhoArquivo == 0:
        print(f"Erro: '{nomeArquivo}' não encontrado ou acesso a pasta negado.")
        return

    dadosRecebidos = b""
    while tamanhoArquivo > 0:
        data = sock.recv(4096)
        dadosRecebidos += data
        tamanhoArquivo -= len(data)

        arquivo = open(caminhoArquivo, "wb")
        arquivo.write(dadosRecebidos)
        arquivo.close()

    print(f"Arquivo '{nomeArquivo}' salvo na pasta 'downloads'.")

def downloadArquivo():
    comando = b"DOW"
    nomeArquivo = input('Digite o nome do arquivo que deseja baixar: ')
    sock.send(adicionaTamanho(comando + nomeArquivo.encode()))

    obterArquivo(nomeArquivo)

def downloadMascara():
    comando = b"DMA"
    mascara = input("Digite a máscara de arquivos (ex: *.jpg): ")
    sock.send(adicionaTamanho(comando + mascara.encode()))

    tamanhoLista = int.from_bytes(sock.recv(4), byteorder='big')
    if tamanhoLista == 0:
        print("Nenhum arquivo encontrado.")
        return
    
    dadosRecebidos = b""
    while tamanhoLista > 0:
        data = sock.recv(4096)
        dadosRecebidos += data
        tamanhoLista -= len(data)

    listaArquivos = dadosRecebidos.decode().split('\n')

    arquivosValidos = []  
    for arquivo in listaArquivos: 
        if arquivo.strip(): arquivosValidos.append(arquivo) 

    for nomeArquivo in arquivosValidos:
        obterArquivo(nomeArquivo)

def obterMd5():
    nomeArquivo = input("Digite o nome do arquivo para MD5: ")
    posicao = input("Digite a última posição do arquivo para calcular MD5 (número): ")

    if not posicao.isdigit():
        print("Entrada inválida. Digite um número.")
        return

    comando = b"MD5"
    sock.send(adicionaTamanho(comando + f"{nomeArquivo}|{posicao}".encode()))

    tamanhoHash = int.from_bytes(sock.recv(4), byteorder='big')
    if tamanhoHash == 0:
        print("ERRO: Arquivo não encontrado ou acesso negado a pasta.")
        return

    dadosRecebidos = b""
    while tamanhoHash > 0:
        parte = sock.recv(tamanhoHash)
        dadosRecebidos += parte
        tamanhoHash -= len(parte)

    print(f'hash MD5 de "{nomeArquivo}": {dadosRecebidos.decode()}')

def retomarDownload():
    os.makedirs("downloads", exist_ok=True)
    nomeArquivo = input("Digite o nome do arquivo para retomar: ")
    caminhoArquivo = os.path.join("downloads", nomeArquivo)

    if not os.path.exists(caminhoArquivo):
        print("Arquivo não existe localmente, use opção a 2 ou 3 para baixar.")
        return
    
    bytesBaixados = os.path.getsize(caminhoArquivo)
    fd = open(caminhoArquivo, "rb")
    arquivoAtual = fd.read()
    fd.close()

    hashAtual = hashlib.md5(arquivoAtual).hexdigest()
    comando = b"DRA"
    sock.send(adicionaTamanho(comando + f"{nomeArquivo}|{bytesBaixados}|{hashAtual}".encode()))
    
    sock.send(adicionaTamanho(b"OK"))
    bytesRecebidos = int.from_bytes(sock.recv(4), byteorder='big')
    if bytesRecebidos == 0:
        print("Erro: hash inválido, pasta negada, arquivo completo ou inexistente.")
        return
    
    dadosRecebidos = b""
    while bytesRecebidos > 0:
        data = sock.recv(4096)
        dadosRecebidos += data
        bytesRecebidos -= len(data)

    arquivoFinal = open(caminhoArquivo, "ab")
    arquivoFinal.write(dadosRecebidos)
    arquivoFinal.close()

    print(f"Download retomado e concluído: {nomeArquivo}")

def main():
    conectaAoServidor()
    while True:
        opcao = mostraOpcoes()
        if opcao == 1:
            listaArquivos()
        elif opcao == 2:
            downloadArquivo()
        elif opcao == 3:
            downloadMascara()
        elif opcao == 4:
            obterMd5()
        elif opcao == 5:
            retomarDownload()
        elif opcao == 6:
            sock.close()
            return
        else:
            print("Opção inválida!")

main()