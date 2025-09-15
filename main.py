# import itertools
# from time import sleep
#
# import rarfile
#
# def gerar_combinacoes_hex(min_len, max_len):
#     # hex_chars = '0123456789abcdef'
#     hex_chars = [chr(i) for i in range(0x21, 0x7e)]
#     retorno = False
#     for tamanho in range(min_len, max_len + 1):
#         print(f"\n Gerando palavras de tamanho {tamanho}...")
#         for combinacao in itertools.product(hex_chars, repeat=tamanho):
#             palavra = ''.join(combinacao)
#             print(palavra)  # ou armazene em uma lista se preferir
#             # sleep(1)
#             retorno = extrair_arquivo_com_senha(
#                 caminho_rar='C:/Users/Raphael/Downloads/blaaa.rar',
#                 nome_arquivo_desejado='blaaa.camproj',
#                 senha=palavra,
#                 destino='C:/Users/Raphael/Downloads/extraido'
#             )
#             if retorno == True:
#                 print("Saindo da função")
#                 return
#
#
#
#
#
# def extrair_arquivo_com_senha(caminho_rar, nome_arquivo_desejado, senha, destino='.'):
#     try:
#         rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe" #setando o path (pra não setar na variavel de ambiente)
#         rf = rarfile.RarFile(caminho_rar)
#
#         if nome_arquivo_desejado not in rf.namelist():
#             print(f"❌ Arquivo '{nome_arquivo_desejado}' não encontrado no .rar.")
#             return
#
#         rf.extract(nome_arquivo_desejado, path=destino, pwd=senha)
#         print(f"✅ Arquivo '{nome_arquivo_desejado}' extraído com sucesso para '{destino}'.")
#         return True
#     except rarfile.BadRarFile:
#         print("❌ Arquivo .rar inválido ou corrompido.")
#     except rarfile.RarWrongPassword:
#         print("🔐 Senha incorreta.")
#     except Exception as e:
#         print(f"⚠️ Erro inesperado: {e}")
#     return False
#
#
# # Exemplo de uso:
# minimo = 5
# maximo = 14
#
# gerar_combinacoes_hex(minimo, maximo)


# retorno = extrair_arquivo_com_senha(
#     caminho_rar='C:/Users/Raphael/Downloads/teste.rar',
#     nome_arquivo_desejado='oi.txt',
#     senha="ola",
#     destino='C:/Users/Raphael/Downloads/extraido'
# )

import itertools
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import rarfile
from collections import Counter


rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"

def extrair_arquivo_com_senha(caminho_rar, nome_arquivo_desejado, senha, destino='.'):
    try:
        rf = rarfile.RarFile(caminho_rar)
        if nome_arquivo_desejado not in rf.namelist():
            return False
        rf.extract(nome_arquivo_desejado, path=destino, pwd=senha)
        print(f"✅ Senha correta: {senha}")
        return True
    except rarfile.RarWrongPassword:
        return False
    except:
        return False

def tem_tres_iguais_em_sequencia(palavra):
    for i in range(len(palavra) - 2):
        if palavra[i] == palavra[i+1] == palavra[i+2]:
            # print(palavra + " Ignorado 3 iguais")
            return True
    return False

def tem_quatro_iguais_em_qualquer_posicao(palavra):
    contagem = Counter(palavra)
    result = any(valor >= 4 for valor in contagem.values())
    # if result:
    #     print(palavra + " Ignorado > 4 iguais")

    return result

def testar_combinacoes_por_tamanho(tamanho):
    hex_chars = ([chr(0x20), chr(0x5f)] + #espaço e underscore
                 [chr(j) for j in range(0x30, 0x3A)] + #números
                 [chr(j) for j in range(0x40, 0x5A)] + #letras maiúsculas
                 [chr(j) for j in range(0x61, 0x7B)]) #letras minúsculas
    # print(hex_chars)
    total = len(hex_chars) ** tamanho
    barra = tqdm(total=total, desc=f"Tamanho {tamanho}", position=tamanho-5, leave=True)

    for combinacao in itertools.product(hex_chars, repeat=tamanho):
        palavra = ''.join(combinacao)
        barra.update(1)

        if tem_tres_iguais_em_sequencia(palavra):
            continue  # pula essa senha

        if tem_quatro_iguais_em_qualquer_posicao(palavra):
            continue  # pula essa senha

        print("Testando: " + palavra)
        sucesso = extrair_arquivo_com_senha(
            caminho_rar='C:/Users/Raphael/Downloads/blaaa.rar',
            nome_arquivo_desejado='blaaa.camproj',
            senha=palavra,
            destino='C:/Users/Raphael/Downloads/extraido'
        )

        if sucesso:
            barra.close()
            print(f"🔓 Senha encontrada: {palavra}")
            return palavra
    barra.close()
    return None

def gerar_combinacoes_em_threads(min_len, max_len):
    with ThreadPoolExecutor(max_workers=(max_len - min_len + 1)) as executor:
        futuros = [executor.submit(testar_combinacoes_por_tamanho, tamanho) for tamanho in range(min_len, max_len + 1)]
        for futuro in futuros:
            resultado = futuro.result()
            if resultado:
                print(f"✅ Interrompendo todas as threads. Senha correta: {resultado}")
                break

# Executa
gerar_combinacoes_em_threads(min_len=6, max_len=12)


