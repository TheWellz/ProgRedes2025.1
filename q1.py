import sys, struct

# Dicionário para descrever operações ARP/RARP
codOperacaoArp = {
    1: "ARP Request",
    2: "ARP Reply",
    3: "RARP Request",
    4: "RARP Reply"
}

# Dicionário para descrever tipos ICMP
tiposPacoteIcmp = {
    0: "Echo Reply",
    3: "Destination Unreachable",
    5: "Redirect",
    8: "Echo Request",
    11: "Time Exceeded"
}

# Formata MAC em string hexadecimal
def formatarMac(mac):
    return ':'.join(f'{byte:02x}' for byte in mac)

# Formata IP em string IPv4
def formatarIp(ip):
    return '.'.join(str(byte) for byte in ip)

if len(sys.argv) < 2:
    print(f"uso: {sys.argv[0]} arquivo.pcap")
    sys.exit(1)

fd = open(sys.argv[1], "rb")  
fd.seek(24)  
cabecalhoPacote = fd.read(16) 

numPacote = 1 

while len(cabecalhoPacote) == 16:
    ts, ms, lenCap, lenPacket = struct.unpack("<IIII", cabecalhoPacote)
    cabecalhoEthernet = fd.read(14)  # Lê cabeçalho Ethernet (14 bytes)

    macDestino = cabecalhoEthernet[0:6]  
    macOrigem = cabecalhoEthernet[6:12] 
    protoEthernet = int.from_bytes(
        cabecalhoEthernet[12:14], 'big')

    print(70 * '-')
    print(f"Pacote {numPacote}:")
    print("  MAC de destino (frame Ethernet):", formatarMac(macDestino))
    print("  MAC de origem  (frame Ethernet):", formatarMac(macOrigem))

    if protoEthernet == 0x0806:  # Se for ARP ou RARP
        dadosArp = fd.read(28)  # Lê dados ARP (28 bytes)

        protoRede = struct.unpack(">H", dadosArp[2:4])[0] 
        if protoRede == 0x0800:  
            opCode = struct.unpack(">H", dadosArp[6:8])[0]  
            macRemetente = dadosArp[8:14] 
            ipRemetente = dadosArp[14:18]  
            macDestinatario = dadosArp[18:24] 
            ipDestinatario = dadosArp[24:28]  

            descOperacao = codOperacaoArp.get(opCode, f"Desconhecido ({opCode})")  # Descrição da operação
            print("\n[PROTOCOLO ARP/RARP]")
            print(f" Código da operação: {descOperacao}")
            print("  MAC remetente (ARP):", formatarMac(macRemetente))
            print("  MAC destinatário (ARP):", formatarMac(macDestinatario))
            print("  IPv4 remetente (ARP):", formatarIp(ipRemetente))
            print("  IPv4 destinatário (ARP):", formatarIp(ipDestinatario))
        else:
            print("[Ignorado: protocolo de rede não é IPv4 no ARP]")

        fd.seek(lenCap - 42, 1)  # Pula o resto do pacote ARP (42 = 14+28)

    elif protoEthernet == 0x0800:  # Se for IPv4
        cabecalhoIp = fd.read(20)  # Lê cabeçalho IPv4 (20 bytes)

        totalLength = struct.unpack(">H", cabecalhoIp[2:4])[0] 
        identification = struct.unpack(">H", cabecalhoIp[4:6])[0]
        ttl = cabecalhoIp[8] 
        protocol = cabecalhoIp[9]  
        ipOrigem = cabecalhoIp[12:16]  
        ipDestino = cabecalhoIp[16:20]  

        print("\n[PROTOCOLO IPv4]")
        print("  Total Length:", totalLength)
        print("  Identification:", identification)
        print("  TTL:", ttl)
        print("  Protocolo de transporte:", protocol)
        print("  IP de origem:", formatarIp(ipOrigem))
        print("  IP de destino:", formatarIp(ipDestino))

        # Pula o restante dos dados do pacote IPv4
        fd.seek(lenCap - 14 - 20, 1)

    else:
        # Pula dados restantes do pacote Ethernet desconhecido
        fd.seek(lenCap - 14, 1)

    cabecalhoPacote = fd.read(16)  # Lê próximo cabeçalho do pacote
    numPacote += 1  # Incrementa contador de pacotes

fd.close()
