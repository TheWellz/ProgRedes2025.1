import hashlib, struct, time

def calcularHash(nonce, dataToHash):  # Função para calcular o hash
	m = hashlib.sha256() # Cria um objeto hash SHA-256
	m.update(struct.pack(">I", nonce))  # Adiciona o nonce convertido (4 Bytes, Big Endian)
	m.update(dataToHash.encode('utf-8'))  # Adiciona os dados convertidos
	return m.digest()

def findNonce(dataToHash, bitsToBeZero): # Função para encontrar o nonce
	nonce = 0
	prefixoZero = 0
	tempoInicio = time.time()

	while True:
		hash = calcularHash(nonce, dataToHash)

        # Converte os 4 primeiros bytes do hash em inteiro
		fourBytes = struct.unpack(">I", hash[0:4])[0] 

        # Verifica se os bits mais significativos estão zerados
		if (fourBytes >> (32 - bitsToBeZero)) == prefixoZero:
			tempoFim = time.time() - tempoInicio
			return nonce, hash, tempoFim

		nonce += 1


dados = [
    ("Esse um texto elementar", [8, 10, 15]),
    ("Textinho", [8, 18, 22]),
    ("Meu texto médio", [18, 19, 20])
]

print(f"{'Texto a validar':<25} {'Bits em zero':<15} {'Nonce':<15} {'Hash (bits)':<30} {'Tempo (s)':<10}")
print("-" * 100)

for texto, listaBits in dados:
    for bitsToBeZero in listaBits:
        nonce, hash, tempo = findNonce(texto, bitsToBeZero)

        hashBin = ''
        for byte in hash: # Converte cada byte do hash em binário
            hashBin += f"{byte:08b}"

        hashBin25 = hashBin[:25] # Pega os 25 primeiros bits do hash
        print(f"{texto:<25} {bitsToBeZero:<15} {nonce:<15} {hashBin25:<30} {tempo:.4f}")
