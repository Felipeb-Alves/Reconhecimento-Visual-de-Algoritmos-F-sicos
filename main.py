import cv2
import os
import pytesseract
import re
import numpy as np

def selecionar_imagem():
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.update()
        caminho = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif")]
        )
        root.destroy()
        if caminho:
            return caminho
        else:
            print("⚠️ Nenhuma imagem foi selecionada. Você pode digitar o caminho manualmente.")
    except Exception as e:
        print("⚠️ Interface gráfica indisponível. Detalhes do erro:")
        print(e)

    return input("Digite o caminho completo da imagem: ").strip()

def salvar_imagem(imagem, caminho_original, sufixo):
    pasta = os.path.dirname(caminho_original)
    nome_base = os.path.splitext(os.path.basename(caminho_original))[0]
    caminho_saida = os.path.join(pasta, f"{nome_base}_{sufixo}.png")
    cv2.imwrite(caminho_saida, imagem)
    print(f"📷 Imagem '{sufixo}' salva em: {caminho_saida}")

def tratar_texto_ocr(texto):
    # Remove caracteres que não sejam letras, números, pontuação e espaços
    texto = re.sub(r'[^a-zA-Z0-9\s.,;:!?()\[\]{}\'"<>/\-+=\n]', '', texto)

    # Remove espaços em excesso
    texto = re.sub(r'\s+', ' ', texto)

    # Divide em linhas e limpa espaços das bordas
    linhas = texto.split('\n')
    linhas = [linha.strip() for linha in linhas if linha.strip() != '']

    # Correções comuns simples
    correcoes = {
        '|': 'I',
        '0': 'O',
        '1': 'I',
        'ﬁ': 'fi',
        'ﬂ': 'fl',
        '—': '-',
        '“': '"',
        '”': '"',
        '‘': "'",
        '’': "'"
    }
    texto_corrigido = []
    for linha in linhas:
        for errado, certo in correcoes.items():
            linha = linha.replace(errado, certo)
        texto_corrigido.append(linha)

    return '\n'.join(texto_corrigido)

def extrair_texto_e_salvar(caminho_imagem, caminho_saida=None, lang='eng'):
    print("🔄 Carregando imagem...")
    imagem = cv2.imread(caminho_imagem)
    if imagem is None:
        print("❌ Erro ao carregar a imagem. Verifique o caminho informado.")
        return

    print("🔄 Redimensionando...")
    imagem_redim = cv2.resize(imagem, (0, 0), fx=2.5, fy=2.5)
    salvar_imagem(imagem_redim, caminho_imagem, "redimensionada")

    print("🔄 Convertendo para escala de cinza...")
    imagem_cinza = cv2.cvtColor(imagem_redim, cv2.COLOR_BGR2GRAY)
    salvar_imagem(imagem_cinza, caminho_imagem, "cinza")

    print("🔄 Aplicando filtro Sobel para realçar bordas...")
    sobelx = cv2.Sobel(imagem_cinza, cv2.CV_8U, 1, 0, ksize=3)
    sobely = cv2.Sobel(imagem_cinza, cv2.CV_8U, 0, 1, ksize=3)
    sobel = cv2.bitwise_or(sobelx, sobely)
    salvar_imagem(sobel, caminho_imagem, "sobel")

    print("🔄 Aplicando abertura morfológica para remover ruídos...")
    kernel = np.ones((2,2), np.uint8)
    abertura = cv2.morphologyEx(sobel, cv2.MORPH_OPEN, kernel)
    salvar_imagem(abertura, caminho_imagem, "abertura")

    print("🔄 Binarizando usando OTSU...")
    _, imagem_bin = cv2.threshold(abertura, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    salvar_imagem(imagem_bin, caminho_imagem, "binarizada")

    print("🔄 Executando OCR com pytesseract...")
    # Configurando whitelist para tentar melhorar (só letras, números e pontuação)
    config = "--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?()-[]{}'\""

    texto_raw = pytesseract.image_to_string(imagem_bin, lang=lang, config=config)

    if not texto_raw.strip():
        print("⚠️ Atenção: Nenhum texto detectado na imagem processada.")

    print("🔄 Tratando texto OCR...")
    texto_tratado = tratar_texto_ocr(texto_raw)

    if caminho_saida is None:
        nome_base = os.path.splitext(os.path.basename(caminho_imagem))[0]
        caminho_saida = f"{nome_base}_texto_extraido.txt"

    print(f"💾 Salvando texto extraído em '{caminho_saida}'...")
    with open(caminho_saida, 'w', encoding='utf-8') as arquivo:
        arquivo.write(texto_tratado)

    print("✅ Processo concluído!")

if __name__ == "__main__":
    caminho = selecionar_imagem()
    if caminho:
        extrair_texto_e_salvar(caminho, lang='eng')
    else:
        print("⚠️ Nenhuma imagem foi fornecida.")
