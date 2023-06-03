import os
import shutil

def separar_imagens(pasta_origem, pasta_destino, imagens_por_pacote):
    # Verifica se a pasta existe 
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Obter a lista de arquivos na pasta de origem
    arquivos = os.listdir(pasta_origem)
    total_imagens = len(arquivos)

    # Cria pacotes separados
    for i in range(0, total_imagens, imagens_por_pacote):
        # Cria uma nova pasta para o pacote
        nome_pacote = f'Petrobras-EPIS_{i // imagens_por_pacote}'
        pasta_pacote = os.path.join(pasta_destino, nome_pacote)
        os.makedirs(pasta_pacote)

        # Copie as imagens para o pacote
        for j in range(i, min(i + imagens_por_pacote, total_imagens)):
            imagem_origem = os.path.join(pasta_origem, arquivos[j])
            imagem_destino = os.path.join(pasta_pacote, arquivos[j])
            shutil.copy(imagem_origem, imagem_destino)

        print(f'Pacote {nome_pacote} criado com sucesso!')

# Execução do programa
pasta_origem = 'C:/Users/Rapha/Desktop/TesteImg/images'
pasta_destino = 'C:/Users/Rapha/Desktop/pacotes'
imagens_por_pacote = 50 # define quantas imagens um pacote vai ter

separar_imagens(pasta_origem, pasta_destino, imagens_por_pacote)
