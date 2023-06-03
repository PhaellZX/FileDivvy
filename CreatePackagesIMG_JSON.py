import os
import shutil

def separar_imagens_e_jsons(pasta_origem, pasta_destino, imagens_por_pacote):
    # Certifique-se de que a pasta de destino existe
    if not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino)

    # Obtenha a lista de arquivos na pasta de origem
    arquivos = os.listdir(pasta_origem)
    total_imagens = len(arquivos)

    # Crie pacotes separados
    for i in range(0, total_imagens, imagens_por_pacote):
        # Crie uma nova pasta para o pacote
        nome_pacote = f'CEMIG-EPIS_{i // imagens_por_pacote}'
        pasta_pacote = os.path.join(pasta_destino, nome_pacote)
        os.makedirs(pasta_pacote)

        # Copie as imagens e arquivos JSON para o pacote
        for j in range(i, min(i + imagens_por_pacote, total_imagens)):
            nome_arquivo_imagem = arquivos[j]
            nome_arquivo_json = nome_arquivo_imagem.replace('.jpg', '.json')
            caminho_arquivo_imagem = os.path.join(pasta_origem, nome_arquivo_imagem)
            caminho_arquivo_json = os.path.join(pasta_origem, nome_arquivo_json)
            caminho_destino_imagem = os.path.join(pasta_pacote, nome_arquivo_imagem)
            caminho_destino_json = os.path.join(pasta_pacote, nome_arquivo_json)

            if os.path.exists(caminho_arquivo_json):
                shutil.copy(caminho_arquivo_imagem, caminho_destino_imagem)
                shutil.copy(caminho_arquivo_json, caminho_destino_json)
            else:
                shutil.copy(caminho_arquivo_imagem, caminho_destino_imagem)

        print(f'Pacote {nome_pacote} criado com sucesso!')

# Execução do programa
pasta_origem = 'C:/Users/Rapha/Desktop/EPIs_Oculos'
pasta_destino = 'C:/Users/Rapha/Desktop/CEMIG-EPIS'
imagens_por_pacote = 100

separar_imagens_e_jsons(pasta_origem, pasta_destino, imagens_por_pacote)
