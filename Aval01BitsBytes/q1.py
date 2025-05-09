ipStr = input('Digite o endereço IP (formato IPv4): ')
mascaraCidr = int(input('Digite a máscara de rede (CIDR): '))
bitsHost = 32 - mascaraCidr
ipInt = 0

# Converte o IP (string) em inteiro de 32 bits
for octeto in ipStr.split('.'):
	ipInt = (ipInt << 8) | int(octeto)

# Calcula o endereço de rede
ipRede = (ipInt >> bitsHost) << bitsHost

# Calcula o endereço de broadcast
ipBroad = ipRede | ((1 << bitsHost) - 1)

# calcula o gateway
ipGW = ipBroad - 1

# Calcula o número de hosts válidos
hostsValidos = (2 ** bitsHost) - 2

# Converte um inteiro para string no formato IPv4
def intToIp(ipInt):
    return f'{(ipInt >> 24) & 0xFF}.{(ipInt >> 16) & 0xFF}.{(ipInt >> 8) & 0xFF}.{ipInt & 0xFF}'

print('\nEndereco da Rede:', intToIp(ipRede))
print('Endereço de Broadcast:', intToIp(ipBroad))
print('Endereco do Gateway:', intToIp(ipGW))
print('Número de Hosts Válidos:', hostsValidos)