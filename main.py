# retorno = extrair_arquivo_com_senha(
#     caminho_rar='C:/Users/Raphael/Downloads/teste.rar',
#     nome_arquivo_desejado='oi.txt',
#     senha="ola",
#     destino='C:/Users/Raphael/Downloads/extraido'
# )

import itertools
import os
import shutil
import subprocess
import tempfile
import time

import rarfile
import platform
import logging
import sys

from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from collections import Counter


#Criando handle para evitar encavalamento dos logs (disputa entre tqdm e loogin)
class TqdmLoggingHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # Usar tqdm.write() para que as mensagens de log não interfiram com a barra de progresso
            # em ambientes interativos. Em ambientes não interativos, onde o tqdm é desabilitado,
            # esta chamada ainda funcionará como um print para sys.stderr.
            tqdm.write(msg, file=sys.stderr)
        except Exception as e:
            self.handleError(f"{e} ao tentar printar: {record}")


def criar_log():
    # Cria o logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formato do log
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Remove handlers antigos (evita duplicação ou conflito)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Handler personalizado do tdqm
    # tqdm_handler = TqdmLoggingHandler()
    # tqdm_handler.setFormatter(formatter)
    # logger.addHandler(tqdm_handler)

    # Handler para terminal (GitHub Actions mostra isso)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Arquivo
    # file_handler = logging.FileHandler(nome_arquivo, mode="w")
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    logger.info("Configuração de Log completada")


def salvar_resultado(senha_encontrada):
    with open("senha_encontrada.txt", "w") as f:
        f.write(f"SENHA ENCONTRADA: {senha_encontrada}\n")


def extrair_arquivo_com_senha(caminho_rar, nome_arquivo_desejado, senha, destino='.'):
    try:
        rf = rarfile.RarFile(caminho_rar)
        # rf.testrar()
        if nome_arquivo_desejado not in rf.namelist():
            logging.warning(f"Arquivo não encontrado {nome_arquivo_desejado}")
            return False
        rf.extract(nome_arquivo_desejado, path=destino, pwd=senha)
        logging.info(f"✅ Senha correta: {senha}")
        salvar_resultado(senha)
        return True
    except rarfile.RarWrongPassword as e:
        # logging.warning(e)
        return False
    except rarfile.BadRarFile as e:
    #     logging.error(f"Arquivo corrompido: {e}")
        return False
    except Exception as e:
        logging.error(str(e) + " \'" + senha + "\' para o arquivo " + caminho_rar)
        return False
    # comando = [
    #     r"C:\Program Files\WinRAR\UnRAR.exe",
    #     "x", "-y", f"-p{senha}", caminho_rar, destino
    # ]
    # resultado = subprocess.run(comando, capture_output=True, text=True)
    #
    # stderr = resultado.stderr.lower()
    # stdout = resultado.stdout.lower()
    #
    # if "crc failed" in stderr or "corrupt" in stderr:
    #     logging.warning(f"❌ Arquivo corrompido com senha '{senha}'")
    #     return False
    # if "wrong password" in stderr or "incorrect password" in stderr:
    #     logging.info(f"❌ Senha incorreta: {senha}")
    #     return False
    # if "extracting" in stdout or "everything is ok" in stdout:
    #     logging.info(f"✅ Senha correta: {senha}")
    #     salvar_resultado(senha)
    #     return True
    #
    # logging.warning(f"⚠️ Resultado inconclusivo com senha '{senha}'")
    # return False


def tem_tres_iguais_em_sequencia(palavra):
    for i in range(len(palavra) - 2):
        if palavra[i] == palavra[i+1] == palavra[i+2]:
            # logging.info(palavra + " Ignorado 3 iguais")
            return True
    return False

def tem_quatro_iguais_em_qualquer_posicao(palavra):
    contagem = Counter(palavra)
    result = any(valor >= 4 for valor in contagem.values())
    # if result:
    #     logging.info(palavra + " Ignorado > 4 iguais")

    return result

def dois_pares_em_qualquer_lugar(palavra):
    pares = set()
    for i in range(len(palavra) - 1):
        if palavra[i] == palavra[i + 1]:
            pares.add(palavra[i] * 2)

    return len(pares) >= 2

def tem_mais_de_4_numeros(palavra):
    import re
    return len(re.findall(r'\d', palavra)) > 4

#as funções estavam cada uma delas percorrendo a palavra, o intuito é ganhar processamento
def palavra_invalida(palavra):
    contagem = {}
    pares = set()
    num_digitos = 0

    for i, char in enumerate(palavra):
        # Verifica se algum caractere aparece 4 vezes
        if char in contagem:
            contagem[char] += 1
            if contagem[char] >= 4:
                return True  # 4 iguais em qualquer posição
        else:
            contagem[char] = 1

        # Conta dígitos
        if char.isdigit():
            num_digitos += 1
            if num_digitos > 4:
                return True  # Mais de 4 números

        # Verifica três iguais em sequência
        if i >= 2 and palavra[i] == palavra[i-1] == palavra[i-2]:
            return True  # Trinca em sequência

        # Verifica pares consecutivos
        if i < len(palavra) - 1 and palavra[i] == palavra[i+1]:
            pares.add(palavra[i])
            if len(pares) >= 2:
                return True  # Dois pares distintos

    return False  # Palavra passou por todos os filtros

def carregar_progresso(tamanho):
    try:
        with open("progresso_global.txt", "r") as f:
            for linha in f:
                if ':' in linha:
                    t, p = linha.strip().split(':', 1)
                    if int(t) == tamanho:
                        return p
    except FileNotFoundError:
        logging.warning("Arquivo não existe")
    return None


from threading import Lock
progresso_lock = Lock()
import signal

# def handle_sigint(signum, frame):
#     logging.warning("Sinal de interrupção recebido. Salvando progresso...")
#     # salvar_progresso(tamanho_global, palavra_global)
#     os.replace("progresso_temp.txt", "progresso_global.txt")
#     exit(0)
#
# signal.signal(signal.SIGINT, handle_sigint)


def salvar_progresso(tamanho, senha):
    progresso = {}
    file = "progresso_global.txt"

    with progresso_lock:
        try:
            with open(file, "r") as f:
                for linha in f:
                    if ':' in linha:
                        t, p = linha.strip().split(':', 1)
                        if t.isdigit():
                            progresso[int(t)] = p
                        else:
                            logging.error("Registro inválido para a senha {}", p)
        except FileNotFoundError:
            pass

        progresso[tamanho] = senha


        with open(file, "w") as f:
            try:
                for t, p in progresso.items():
                    f.write(f"{t}:{p}\n")
            finally:
                f.flush()  # força a gravação no disco
                os.fsync(f.fileno())  # garante que o sistema operacional também grave

def senha_para_indice(senha, hex_chars):
    base = len(hex_chars)
    indice = 0
    for i, char in enumerate(reversed(senha)):
        pos = hex_chars.index(char)
        indice += pos * (base ** i)
    return indice

#COM HISTÓRICO
"""
Suponha:
- hex_chars = ['a', 'b', 'c']
- tamanho = 3
- idx = 5

Conversão:
- temp = 5
- 1ª iteração: 5 % 3 = 2 → 'c'; temp = 5 // 3 = 1
- 2ª iteração: 1 % 3 = 1 → 'b'; temp = 1 // 3 = 0
- 3ª iteração: 0 % 3 = 0 → 'a'; temp = 0 // 3 = 0
combinacao = ['c', 'b', 'a'] → palavra = 'abc' (após reversed)
"""
def testar_combinacoes_por_tamanho(tamanho, tmpfile):
    hex_chars = (#[chr(0x20), chr(0x5f)] + #espaço e underscore
            [j for j in 'raphelgvdnjulisoRAPHELGVDNJULISO@_!'] +
            [chr(j) for j in range(0x30, 0x3A)] #números
        #[chr(j) for j in range(0x40, 0x5A)] + #letras maiúsculas
        #[chr(j) for j in range(0x61, 0x7B)] #letras minúsculas
    )
    logging.info(hex_chars)
    # logging.info(hex_chars)
    total = len(hex_chars) ** tamanho
    barra = tqdm(total=total, desc=f"Tamanho {tamanho}", position=tamanho-5, leave=True, mininterval=5) #mininterval é para logar de 5s em 5s

    senha_inicial = carregar_progresso(tamanho)
    start_index = senha_para_indice(senha_inicial, hex_chars) if senha_inicial else 0
    barra.update(start_index)

    for idx in range(start_index, total):
        combinacao = []
        temp = idx
        for _ in range(tamanho):
            combinacao.append(hex_chars[temp % len(hex_chars)]) # <-- ordem natural, da direita pra esquerda

            temp //= len(hex_chars)

        palavra = ''.join(reversed(combinacao))  # <-- inverte para que o caractere menos significativo fique à direita
        barra.update(1)

        if palavra_invalida(palavra):
            if (idx % 10000000 == 0):
                salvar_progresso(tamanho, palavra)
            continue # pula essa senha
        else:
            if (idx % 501 == 0):
                salvar_progresso(tamanho, palavra)

        logging.info("Testando \'" + palavra + "\' para o arquivo " + tmpfile + " do posicionamento " + str(tamanho))
        sucesso = extrair_arquivo_com_senha(
            #caminho_rar='C:/Users/Raphael/Downloads/blaaa.rar',
            caminho_rar=tmpfile,
            nome_arquivo_desejado='blaaa.camproj',
            senha=palavra,
            #destino='C:/Users/Raphael/Downloads/extraido'
            destino=str(tamanho)
        )

        if sucesso:
            barra.close()
            logging.info(f"🔓 Senha encontrada: {palavra}")
            return palavra
    barra.close()
    return None

#  SEM HISTÓRICO
# def testar_combinacoes_por_tamanho(tamanho, tmpfile):
#     hex_chars = (#[chr(0x20), chr(0x5f)] + #espaço e underscore
#                  [j for j in 'raphelgvdnjulisoRAPHELGVDNJULISO@_!'] +
#                  [chr(j) for j in range(0x30, 0x3A)] #números
#                  #[chr(j) for j in range(0x40, 0x5A)] + #letras maiúsculas
#                  #[chr(j) for j in range(0x61, 0x7B)] #letras minúsculas
#                  )
#     # logging.info(hex_chars)
#     total = len(hex_chars) ** tamanho
#     barra = tqdm(total=total, desc=f"Tamanho {tamanho}", position=tamanho-5, leave=True, mininterval=5) #mininterval é para logar de 5s em 5s
#
#     for combinacao in itertools.product(hex_chars, repeat=tamanho):
#         palavra = ''.join(combinacao)
#         barra.update(1)
#
#         # if tem_tres_iguais_em_sequencia(palavra):
#         #     continue  # pula essa senha
#         #
#         # if tem_quatro_iguais_em_qualquer_posicao(palavra):
#         #     continue  # pula essa senha
#         #
#         # if tem_mais_de_4_numeros(palavra):
#         #     continue # pula essa senha
#         #
#         # if dois_pares_em_qualquer_lugar(palavra):
#         #     continue # pula essa senha
#         if palavra_invalida(palavra):
#             continue # pula essa senha
#
#         logging.info("Testando \'" + palavra + "\' para o arquivo " + tmpfile + " do posicionamento " + str(tamanho))
#         sucesso = extrair_arquivo_com_senha(
#             #caminho_rar='C:/Users/Raphael/Downloads/blaaa.rar',
#             caminho_rar=tmpfile,
#             nome_arquivo_desejado='blaaa.camproj',
#             senha=palavra,
#             #destino='C:/Users/Raphael/Downloads/extraido'
#             destino=str(tamanho)
#         )
#
#         if sucesso:
#             barra.close()
#             logging.info(f"🔓 Senha encontrada: {palavra}")
#             return palavra
#     barra.close()
#     return None

def gerar_combinacoes_em_threads(min_len, max_len):
    caminhos_por_tamanho = {}
    try:
        # Cria cópias do .rar para cada tamanho
        for tamanho in range(min_len, max_len + 1):
            temp_rar = tempfile.NamedTemporaryFile(delete=False, suffix=".rar")
            shutil.copyfile('blaaa.rar', temp_rar.name)
            caminhos_por_tamanho[tamanho] = temp_rar.name
            logging.info("Arquivo gerado: " + caminhos_por_tamanho[tamanho])

        with ThreadPoolExecutor(max_workers=(max_len - min_len + 1)) as executor:
            futuros = [executor.submit(testar_combinacoes_por_tamanho, tamanho, caminhos_por_tamanho[tamanho]) for tamanho in range(min_len, max_len + 1)]
            for futuro in futuros:
                resultado = futuro.result()
                if resultado:
                    logging.info(f"✅ Interrompendo todas as threads. Senha correta: {resultado}")
                    break
    finally:
        # Limpa os arquivos temporários
        for caminho in caminhos_por_tamanho:
            if os.path.exists(caminho):
                os.remove(caminho)

        logging.info("Arquivos temporários apagados")

# Executa
criar_log()

if platform.system() == "Windows":
    rarfile.UNRAR_TOOL = r"C:\Program Files\WinRAR\UnRAR.exe"
    logging.info("Windows")
else:
    rarfile.UNRAR_TOOL = "unrar"
    logging.info("Linux")

gerar_combinacoes_em_threads(min_len=6, max_len=11)

# palavras = ["aabbed", "abc123", "11ad22", "aeccgkk", "123456", "abcdefg", "çljdie,ck", "lçkjde", "kdeaaacc", "abacadaeekdi"] * 100000
#
# # Teste com 4 funções separadas
# start = time.time()
# for palavra in palavras:
#     if tem_tres_iguais_em_sequencia(palavra): continue
#     if tem_quatro_iguais_em_qualquer_posicao(palavra): continue
#     if dois_pares_em_qualquer_lugar(palavra): continue
#     if tem_mais_de_4_numeros(palavra): continue
# end = time.time()
# print("Tempo com 4 funções:", end - start)
#
# # Teste com função otimizada
# start = time.time()
# for palavra in palavras:
#     if palavra_invalida(palavra): continue
# end = time.time()
# print("Tempo com função otimizada:", end - start)

#Usando 100000 palavras
#Tempo com 4 funções: 3.658733367919922
#Tempo com função otimizada: 2.017991542816162



