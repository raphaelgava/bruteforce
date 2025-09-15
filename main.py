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
    # except rarfile.BadRarFile as e:
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

def testar_combinacoes_por_tamanho(tamanho, tmpfile):
    hex_chars = ([chr(0x20), chr(0x5f)] + #espaço e underscore
                 [chr(j) for j in range(0x30, 0x3A)] + #números
                 [chr(j) for j in range(0x40, 0x5A)] + #letras maiúsculas
                 [chr(j) for j in range(0x61, 0x7B)]) #letras minúsculas
    # logging.info(hex_chars)
    total = len(hex_chars) ** tamanho
    barra = tqdm(total=total, desc=f"Tamanho {tamanho}", position=tamanho-5, leave=True, mininterval=5) #mininterval é para logar de 5s em 5s

    for combinacao in itertools.product(hex_chars, repeat=tamanho):
        palavra = ''.join(combinacao)
        barra.update(1)

        if tem_tres_iguais_em_sequencia(palavra):
            continue  # pula essa senha

        if tem_quatro_iguais_em_qualquer_posicao(palavra):
            continue  # pula essa senha

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

gerar_combinacoes_em_threads(min_len=6, max_len=12)


