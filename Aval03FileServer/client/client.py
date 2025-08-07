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
    return tamanho.to_bytes(4, byteorder='big') + dados  # Adiciona os 4 bytes de tamanho no início

def listaArquivos():
    comando = b"DIR" 
    sock.send(adicionaTamanho(comando)) 

    tamanhoListagem = int.from_bytes(sock.recv(4), byteorder='big')  # Recebe tamanho da resposta
    while tamanhoListagem > 0:
        resposta = sock.recv(tamanhoListagem)  # Recebe a resposta
        tamanhoListagem -= len(resposta)  # Atualiza o restante a receber
        print(resposta.decode()) 

def obterArquivo(nomeArquivo):
    os.makedirs("downloads", exist_ok=True)  # Cria pasta 'downloads' se não existir
    caminhoArquivo = os.path.join("downloads", nomeArquivo) 

    if os.path.exists(caminhoArquivo):  # Verifica se o arquivo já existe
        resposta = input(f"O arquivo '{nomeArquivo}' já existe. Sobrescrever? (s/n): ").lower()
        if resposta != 's':
            sock.send(adicionaTamanho(b"SKIP"))  # Informa que não deve baixar novamente
            print(f"Pulando o arquivo '{nomeArquivo}'.")
            return
        else:
            sock.send(adicionaTamanho(b"OK"))  # Confirma que pode sobrescrever
    else:
        sock.send(adicionaTamanho(b"OK"))  # Confirma que pode baixar o arquivo

    tamanhoArquivo = int.from_bytes(sock.recv(4), byteorder='big')  # Recebe tamanho do arquivo
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
    comando = b"DMA"  #
    mascara = input("Digite a máscara de arquivos (ex: *.jpg): ")  
    sock.send(adicionaTamanho(comando + mascara.encode()))  

    tamanhoLista = int.from_bytes(sock.recv(4), byteorder='big')  # Recebe tamanho da lista
    if tamanhoLista == 0:
        print("Nenhum arquivo encontrado.")  
        return
    
    dadosRecebidos = b"" 
    while tamanhoLista > 0:
        data = sock.recv(4096)  
        dadosRecebidos += data
        tamanhoLista -= len(data)

    listaArquivos = dadosRecebidos.decode().split('\n')  # Converte e separa arquivos

    arquivosValidos = []  # Lista final de arquivos
    for arquivo in listaArquivos: 
        if arquivo.strip(): arquivosValidos.append(arquivo)  # Ignora vazios

    for nomeArquivo in arquivosValidos:
        obterArquivo(nomeArquivo)  # Realiza o download

def obterMd5():
    nomeArquivo = input("Digite o nome do arquivo para MD5: ")
    posicao = input("Digite a última posição do arquivo para calcular MD5 (número): ") 

    if not posicao.isdigit():  
        print("Entrada inválida. Digite um número.") 
        return

    comando = b"MD5"  
    sock.send(adicionaTamanho(comando + f"{nomeArquivo}|{posicao}".encode()))  

    tamanhoHash = int.from_bytes(sock.recv(4), byteorder='big')  # Recebe tamanho do hash
    if tamanhoHash == 0:
        print("ERRO: Arquivo não encontrado ou acesso negado a pasta.") 
        return

    dadosRecebidos = b"" 
    while tamanhoHash > 0:
        parte = sock.recv(tamanhoHash)  #
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

    arquivoFinal = open(caminhoArquivo, "ab")  # Abre arquivo para append binário
    arquivoFinal.write(dadosRecebidos)  
    arquivoFinal.close()

    print(f"Download retomado e concluído: {nomeArquivo}")  

def main():
    conectaAoServidor()
    while True:
        opcao = mostraOpcoes()  
        if opcao == 1:
            listaArquivos()  # Lista arquivos
        elif opcao == 2:
            downloadArquivo()  # Download simples por nome
        elif opcao == 3:
            downloadMascara()  # Download por máscara
        elif opcao == 4:
            obterMd5()  # Hash MD5 parcial
        elif opcao == 5:
            retomarDownload()  # Retomar download
        elif opcao == 6:
            sock.close()  # Encerra conexão
            return
        else:
            print("Opção inválida!") 

main()  