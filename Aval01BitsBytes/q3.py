with open("IMG_20250509_184205.jpg", "rb") as imagem:
    bytesIniciais = imagem.read(6)

    # Obtem o tamanho do bloco de metadados EXIF 
    app1DataSize = int(bytesIniciais[4:6].hex(), 16)

with open("IMG_20250509_184205.jpg", "rb") as imagem:
    imagem.read(4)
    app1Data = imagem.read(app1DataSize)

    # Obtem a quantidade de metadados na imagem
    metadadoSize = int(app1Data[16:18].hex(), 16)

print(f"O arquivo possui {metadadoSize} metadados")

inicio = 18
for i in range(metadadoSize):
    metadado = app1Data[inicio:inicio + 12] # Obtem o metadado de 12 Bytes
    tag = metadado[:2]
    tipo = metadado[2:4]

    if tipo == b'\x00\x01': # Unsigned Byte
        valor = int(metadado[8:9].hex(), 16)
    elif tipo == b'\x00\x03': # Unsigned short
        valor = int(metadado[8:10].hex(), 16)
    elif tipo == b'\x00\x04': # Unsigned long
        valor = int(metadado[8:12].hex(), 16)

    if tag == b'\x01\x00': # Largura da imagem
        print(f'A largura da imagem é: {valor}')
    elif tag == b'\x01\x01': # Altura da imagem
        print(f'A altura da imagem é: {valor}')

    inicio += 12
