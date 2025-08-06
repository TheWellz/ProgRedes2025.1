import socket, os

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
            print("4 - Fim")
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
        print(f"Arquivo '{nomeArquivo}' não encontrado no servidor.")
        return

    dadosRecebidos = b""
    while tamanhoArquivo > 0:
        data = sock.recv(4096)
        dadosRecebidos += data
        tamanhoArquivo -= len(data)

    with open(caminhoArquivo, "wb") as arquivo:
        arquivo.write(dadosRecebidos)

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

    for nomeArquivo in listaArquivos:
        obterArquivo(nomeArquivo)

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
            sock.close()
            return
        else:
            print("Opção inválida!")

main()
