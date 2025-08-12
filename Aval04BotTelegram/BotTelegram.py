import socket, ssl, json, time, subprocess  

TOKEN = "8416741635:AAEOghTs5tZT3hfeuixeAa-I9VqDv2k7x5Q" 
HOST  = "api.telegram.org" 
PORT  = 443  

def conn_to(): # 
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
    sock_tcp.connect((HOST, PORT))
    purpose = ssl.Purpose.SERVER_AUTH  # Define propósito do SSL (autenticação do servidor)
    context = ssl.create_default_context(purpose)  # Cria contexto SSL padrão
    return context.wrap_socket(sock_tcp, server_hostname=HOST)  # Envolve socket em SSL e retorna

def send_get (sock_tcp, cmd): 
    resource = "/bot"+TOKEN+"/"+cmd  
    sock_tcp.send (("GET "+resource+" HTTP/1.1\r\n"+ 
                    "Host: "+HOST+"\r\n"+
                    "Connection: close\r\n"+
                    "\r\n").encode("utf-8"))

def get_response(sock_tcp): # Recebe e processa a resposta HTTP, retornando o status, cabeçalhos e JSON decodificado
    answer = sock_tcp.recv(4096) 
    header_body = answer.split(b"\r\n\r\n")  
    headers, body = header_body[0].decode().split("\r\n"), header_body[1]  

    status_line = headers[0]  
    if status_line.split()[1] == "200": 
        for header in headers[1:]:
            field_value = header.split(":")  
            if field_value[0] == "Content-Length":  
                to_read = int (field_value[1])  
                break
    
        to_read -= len(body)  
        while to_read > 0:  
            segment = sock_tcp.recv(4096)
            body += segment  
            to_read -= len(segment)  
    
        return (status_line, headers[1:], json.loads(body.decode()))  # Retorna status, cabeçalhos e JSON
    return (None, None, None)

def get_updates(offset = 0): # Solicita updates (mensagens novas) do Telegram a partir de um offset
    sock_tcp = conn_to()  # Abre conexão SSL
    send_get(sock_tcp, f"getUpdates?offset={offset}")  # Envia requisição GET com offset
    status_line, headers, body = get_response(sock_tcp) 
    try:
        result = body["result"] if body else []  # Pega lista de updates ou lista vazia
    except Exception:
        result = []
    sock_tcp.close() 
    return result  # Retorna lista de updates

def show_update(update): # Imprime no console o nome do usuário e a mensagem recebida
    print (update["message"]["chat"]["first_name"], "->", update["message"]["text"])

def rodaCmd(comando): # Executa comando do sistema e retorna saída como string
    return subprocess.check_output(comando, shell=True, text=True)

comandos = {  # Dicionário com comandos aceitos e seus comandos de sistema correspondentes
    "/ping": "ping google.com -n 4",
    "/nslookup": "nslookup google.com",
    "/getmac": "getmac",
    "/netsh": "netsh interface show interface",
    "/netstat": "netstat -ano | findstr :80"
}

usuariosCadastrados = {}  # Dicionário para armazenar usuários cadastrados (chatId -> nome)

def enviaMensagem(chatId, texto):
    sock_tcp = conn_to()  
    payload = {"chat_id": chatId, "text": texto}  # Prepara payload JSON
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")  # Codifica JSON em bytes
    resource = "/bot"+TOKEN+"/sendMessage"  # Define recurso URI para enviar mensagem
    headers = (f"POST {resource} HTTP/1.1\r\n"
               f"Host: {HOST}\r\n"
               "Content-Type: application/json\r\n"
               f"Content-Length: {len(payload_bytes)}\r\n"
               "Connection: close\r\n"
               "\r\n")  
    sock_tcp.send(headers.encode("utf-8") + payload_bytes)  
    try:
        get_response(sock_tcp) 
    except Exception:
        pass
    sock_tcp.close()  

def enviaMensagemLonga(chatId, texto, tamanhoBloco=4000): # Divide mensagens longas em blocos menores e envia sequencialmente para evitar limite
    for inicioDoBloco in range(0, len(texto), tamanhoBloco):  # Percorre texto em blocos
        enviaMensagem(chatId, texto[inicioDoBloco:inicioDoBloco+tamanhoBloco])  # Envia bloco atual
        time.sleep(0.1)

def respondeUpdate(update): # Processa cada update recebido e responde conforme texto da mensagem
    chat = update["message"]["chat"] 
    chatId  = chat["id"] 
    firstName = chat.get("first_name", "Usuário")  
    texto = update["message"].get("text", "").strip() 

    if chatId not in usuariosCadastrados:  # Se usuário ainda não cadastrado
        usuariosCadastrados[chatId] = firstName  # Adiciona usuário
        lista = (f"Olá, {firstName}! Você foi cadastrado.\n"
                 "Escolha um serviço enviando um dos comandos abaixo:\n"
                 "/ping - testa a conexão com google.com enviando 4 pacotes\n"
                 "/nslookup - consulta DNS para google.com, mostrando detalhes do servidor\n"
                 "/getmac - exibe os endereços MAC das interfaces de rede do computador\n"
                 "/netsh - mostra o status e tipos das interfaces de rede disponíveis\n"
                 "/netstat - lista conexões TCP ativas na porta 80 (HTTP), mostrando PID dos processos\n")
        enviaMensagem(chatId, lista)  # Envia lista de comandos
        return update["update_id"]  # Retorna id do update processado

    if texto in comandos:  
        try:
            resultado = rodaCmd(comandos[texto])  # Executa comando do sistema
            full = f"{texto}:\n{resultado}"  # Monta resposta completa
            enviaMensagemLonga(chatId, full)  # Envia resposta dividida em blocos, se necessário
        except Exception as e:
            enviaMensagem(chatId, f"Erro ao executar comando: {e}")
        return update["update_id"]

    if texto == "/start":  # Se comando /start recebido após cadastro
        lista = (f"Olá novamente, {firstName}! \nEscolha um serviço enviando um dos comandos abaixo:\n"
                 "/ping - testa a conexão com google.com enviando 4 pacotes\n"
                 "/nslookup - consulta DNS para google.com, mostrando detalhes do servidor\n"
                 "/getmac - exibe os endereços MAC das interfaces de rede do computador\n"
                 "/netsh - mostra o status e tipos das interfaces de rede disponíveis\n"
                 "/netstat - lista conexões TCP ativas na porta 80 (HTTP), mostrando PID dos processos\n")
        enviaMensagem(chatId, lista) 
        return update["update_id"]

    enviaMensagem(chatId, "Comando inválido. Envie /start para ver a lista de serviços.") 
    return update["update_id"]

def main():

    print ("Aceitando updates ....")
    last_update = 0  
    while True:
        updates = get_updates(last_update+1)  # Busca novos updates a partir do último
        for update in updates:
            show_update(update)  
            last_update = respondeUpdate(update)  # Processa update e atualiza último id
        print ("-------------")
        time.sleep(2)  

main()  