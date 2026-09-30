# -*- coding: utf-8 -*-
import asyncio
import json
import secrets
import string
import random
import re
import unicodedata
import html
from pathlib import Path
from datetime import datetime
import requests
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# =========================================================
# PL STORE V3 - UTF-8 + ANIMAÇÕES
# =========================================================

TOKEN = ""
MP_ACCESS_TOKEN = "APP_USR-89407900806146-081419-c09aadab562cb8ed4c48f52d808161bc-2083530073"
ADMIN_ID = 7219090873
PIX_KEY = "f6688ab4-1012-447e-a1e5-c85e9fda74b5"
DEPOSITO_MINIMO = 10

VIP_PRICE = 20
VIP_LINK = "https://t.me/+iLXrv65at9NlYTJh"
SUPORTE_LINK = "https://t.me/plstoresuporte"
REFERENCIAS_LINK = "https://t.me/+g3FYvSu_cS05Yzkx"
REFERENCIAS_CHAT_ID = -1003389245773

FRASE_REFERENCIA = "💳 | Cartão full dados comprado!"
LOJA_LINK = "https://t.me/PL_STOREBOT"

BASE_DIR = Path(__file__).parent
PASTA_ESTOQUE = BASE_DIR / "estoque"
ARQUIVO_SALDOS = BASE_DIR / "saldos.json"
ARQUIVO_COMPRAS = BASE_DIR / "compras.json"
ARQUIVO_GIFTS = BASE_DIR / "gifts.json"
PASTA_ENTREGAS = BASE_DIR / "entregas"
ARQUIVO_PRODUTOS = BASE_DIR / "produtos_config.json"
SEPARADOR_PRODUTO = "---PRODUTO---"

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

depositos = {}
aguardando_deposito = {}

LINHA = ""

produtos = {
    "buy10": {"nome": "DÉBITO", "preco": 30, "arquivo": "debito.txt", "voltar": "ccfull"},
    "buy11": {"nome": "BLACK", "preco": 50, "arquivo": "black.txt", "voltar": "ccfull"},
    "buy12": {"nome": "ELO", "preco": 25, "arquivo": "elo.txt", "voltar": "ccfull"},
    "buy13": {"nome": "GOLD", "preco": 25, "arquivo": "gold.txt", "voltar": "ccfull"},
    "buy14": {"nome": "INDEFINIDO", "preco": 50, "arquivo": "indefinido.txt", "voltar": "ccfull"},
    "buy15": {"nome": "INFINITE", "preco": 50, "arquivo": "infinite.txt", "voltar": "ccfull"},
    "buy16": {"nome": "STANDARD", "preco": 35, "arquivo": "standard.txt", "voltar": "ccfull"},
    "buy17": {"nome": "AMEX", "preco": 50, "arquivo": "amex.txt", "voltar": "ccfull"},
    "buy18": {"nome": "NU GOLD", "preco": 8, "arquivo": "nugold.txt", "voltar": "ccfull"},
    "buy19": {"nome": "NU BLACK", "preco": 30, "arquivo": "nublack.txt", "voltar": "ccfull"},
    "buy20": {"nome": "NU MICRO", "preco": 15, "arquivo": "numicro.txt", "voltar": "ccfull"},
    "buy21": {"nome": "PLATINUM", "preco": 35, "arquivo": "platinum.txt", "voltar": "ccfull"},
    "buy22": {"nome": "CLASSIC", "preco": 20, "arquivo": "classic.txt", "voltar": "ccfull"},
    "buy23": {"nome": "MICR BUSINESS", "preco": 20, "arquivo": "micr business.txt", "voltar": "ccfull"},
    "buy24": {"nome": "NANJING", "preco": 70, "arquivo": "nanjing.txt", "voltar": "ccfull"},
    "buy25": {"nome": "BUSINESS", "preco": 20, "arquivo": "business.txt", "voltar": "ccfull"},
    "buy26": {"nome": "PERSONAL", "preco": 30, "arquivo": "personal.txt", "voltar": "ccfull"},
    "buy27": {"nome": "PREPAGO", "preco": 10, "arquivo": "prepago.txt", "voltar": "ccfull"},
    "mix5": {"nome": "MIX 5", "preco": 150, "arquivo": "mix5.txt", "voltar": "ccmix"},
    "mix10": {"nome": "MIX 10", "preco": 280, "arquivo": "mix10.txt", "voltar": "ccmix"},
    "mix50": {"nome": "MIX 50", "preco": 1100, "arquivo": "mix50.txt", "voltar": "ccmix"},
}

ESIM_CONFIG = {
    "vivo": {
        "nome": "VIVO",
        "preco": 20.00,
        "pasta": PASTA_ESTOQUE / "esim" / "vivo",
    },
    "tim": {
        "nome": "TIM",
        "preco": 40.00,
        "pasta": PASTA_ESTOQUE / "esim" / "tim",
    },
    "claro": {
        "nome": "CLARO",
        "preco": 35.00,
        "pasta": PASTA_ESTOQUE / "esim" / "claro",
    },
}

ESIM_EXTENSOES = {".jpg", ".jpeg", ".png", ".webp"}

def listar_estoque_esim(operadora):
    cfg = ESIM_CONFIG.get(operadora.lower())
    if not cfg:
        return []
    pasta = cfg["pasta"]
    pasta.mkdir(parents=True, exist_ok=True)
    return sorted(
        p for p in pasta.iterdir()
        if p.is_file() and p.suffix.lower() in ESIM_EXTENSOES
    )

def extrair_ddd_esim(caminho):
    m = re.match(r"^(?:DDD)?(\d{2})(?:[-_ ].*)?$", caminho.stem, re.I)
    return m.group(1) if m else None

def ddds_esim_disponiveis(operadora):
    ddds = set()
    for foto in listar_estoque_esim(operadora):
        ddd = extrair_ddd_esim(foto)
        if ddd:
            ddds.add(ddd)
    return sorted(ddds)

def estoque_esim_por_ddd(operadora, ddd):
    return [
        foto for foto in listar_estoque_esim(operadora)
        if extrair_ddd_esim(foto) == ddd
    ]

def retirar_esim(operadora, ddd):
    opcoes = estoque_esim_por_ddd(operadora, ddd)
    return random.choice(opcoes) if opcoes else None

def titulo(nome):
    return f"{nome}\n\n"

def dinheiro(valor):
    return f"R$ {valor:.2f}"

def carregar_json(caminho, padrao):
    if caminho.exists():
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return padrao
    return padrao

def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def aplicar_config_produtos():
    dados = carregar_json(ARQUIVO_PRODUTOS, {})
    if not isinstance(dados, dict):
        return
    for item_id, cfg in dados.items():
        if item_id in produtos and isinstance(cfg, dict):
            if "nome" in cfg:
                produtos[item_id]["nome"] = str(cfg["nome"])
            if "preco" in cfg:
                try:
                    produtos[item_id]["preco"] = float(cfg["preco"])
                except (TypeError, ValueError):
                    pass

def salvar_config_produtos():
    dados = {item_id: {"nome": prod["nome"], "preco": prod["preco"]} for item_id, prod in produtos.items()}
    salvar_json(ARQUIVO_PRODUTOS, dados)

def carregar_saldos():
    dados = carregar_json(ARQUIVO_SALDOS, {})
    return {int(k): float(v) for k, v in dados.items()}

def salvar_saldos():
    salvar_json(ARQUIVO_SALDOS, saldos)

def carregar_compras():
    return carregar_json(ARQUIVO_COMPRAS, [])

def salvar_compras():
    salvar_json(ARQUIVO_COMPRAS, compras)

def salvar_gifts():
    salvar_json(ARQUIVO_GIFTS, gifts)

async def enviar_referencia_compra(produto, preco, ddd=None):
    try:
        if produto.lower().startswith("esim "):
            operadora = produto[5:].strip()
            texto_referencia = (
                "📲 | <b>CHIP VIRTUAL COMPRADO</b>\n\n"
                f"<b>OPERADORA:</b> {operadora.upper()}\n"
                f"<b>PREÇO:</b> {dinheiro(preco)}\n"
                f"<b>DDD:</b> {ddd or 'N/A'}"
            )
        else:
            frase = FRASE_REFERENCIA.strip()
            partes = []
            if frase:
                partes.append(frase)
            partes.extend([
                f"🏅 <b>NIVEL:</b> {produto}",
                f"📈 <b>VALOR:</b> {dinheiro(preco)}"
            ])
            texto_referencia = "\n\n".join(partes)

        teclado_referencia = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 COMPRAR", url=LOJA_LINK)]
        ])

        await bot.send_message(
            chat_id=REFERENCIAS_CHAT_ID,
            text=texto_referencia,
            parse_mode="HTML",
            reply_markup=teclado_referencia
        )
    except Exception as erro:
        print("ERRO AO ENVIAR REFERÊNCIA DE COMPRA:", erro)

saldos = carregar_saldos()
compras = carregar_compras()
gifts = carregar_json(ARQUIVO_GIFTS, {})

aplicar_config_produtos()

class AvisoStates(StatesGroup):
    aguardando_mensagem = State()

class TrocaProdutoStates(StatesGroup):
    aguardando_nome = State()
    aguardando_preco = State()


def is_admin(user_id):
    return user_id == ADMIN_ID

def get_saldo(user_id):
    return saldos.get(user_id, 0)

def gerar_codigo_gift():
    caracteres = string.ascii_uppercase + string.digits
    tamanhos = (6, 4, 4, 6)
    while True:
        codigo = "-".join(
            "".join(secrets.choice(caracteres) for _ in range(tamanho))
            for tamanho in tamanhos
        )
        if codigo not in gifts:
            return codigo

def caminho_estoque(item_id):
    prod = produtos.get(item_id)
    if not prod:
        return None
    return PASTA_ESTOQUE / prod["arquivo"]

def ler_blocos_estoque(item_id):
    caminho = caminho_estoque(item_id)
    if not caminho or not caminho.exists():
        return []
    conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
    blocos = []
    for bloco in conteudo.split(SEPARADOR_PRODUTO):
        bloco = bloco.strip()
        if bloco:
            blocos.append(bloco)
    return blocos

def salvar_blocos_estoque(item_id, blocos):
    caminho = caminho_estoque(item_id)
    if not caminho:
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = f"\n\n{SEPARADOR_PRODUTO}\n\n".join(blocos)
    if conteudo.strip():
        conteudo += "\n"
    caminho.write_text(conteudo, encoding="utf-8")

def contar_estoque(item_id):
    return len(ler_blocos_estoque(item_id))

def normalizar_busca(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.replace(" ", "").replace("-", "").replace("_", "")
    return texto

def encontrar_produto_busca(termo):
    termo_norm = normalizar_busca(termo)
    if not termo_norm:
        return None, []
    encontrados = []
    for item_id, prod in produtos.items():
        nome_norm = normalizar_busca(prod["nome"])
        arquivo_norm = normalizar_busca(Path(prod["arquivo"]).stem)
        item_norm = normalizar_busca(item_id)
        if termo_norm in (nome_norm, arquivo_norm, item_norm) or termo_norm in nome_norm or termo_norm in arquivo_norm:
            encontrados.append((item_id, prod))
    if len(encontrados) == 1:
        return encontrados[0], encontrados
    return None, encontrados

def total_estoque():
    return sum(contar_estoque(item_id) for item_id in produtos)

def entregar_produto(item_id):
    blocos = ler_blocos_estoque(item_id)
    if not blocos:
        return None
    entrega = blocos[0]
    salvar_blocos_estoque(item_id, blocos[1:])
    return entrega

def nome_arquivo_seguro(nome):
    proibidos = '<>:"/\\|?*'
    for char in proibidos:
        nome = nome.replace(char, '-')
    return nome.strip()

def criar_arquivo_entrega_txt(user_id, prod, entrega):
    PASTA_ENTREGAS.mkdir(parents=True, exist_ok=True)
    agora = datetime.now()
    nome_produto = prod["nome"]
    nome_base = nome_arquivo_seguro(f"PL STORE - {nome_produto}")
    nome_arquivo = f"{nome_base}.txt"
    caminho = PASTA_ENTREGAS / f"{user_id}_{agora.strftime('%Y%m%d_%H%M%S')}_{nome_arquivo}"
    conteudo = (
        "✅COMPRA EFETUADA!✅\n\n"
        "⚠️GARANTIMOS SOMENTE LIVE!\n\n"
        f"{entrega.strip()}\n\n"
        "⏰ TEMPO MÁXIMO PARA O REEMBOLSO SÃO DE 10 MINUTOS❗️\n"
    )
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho, nome_arquivo

def registrar_compra(user_id, produto, valor, conteudo):
    compras.append({
        "user_id": user_id,
        "produto": produto,
        "valor": valor,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "conteudo": conteudo,
        "reembolsado": False
    })
    salvar_compras()

async def avisar_admin_compra(user_id, produto, valor, saldo_restante=None):
    try:
        chat = await bot.get_chat(user_id)
        username = f"@{chat.username}" if chat.username else "-"
        if saldo_restante is None:
            saldo_restante = get_saldo(user_id)
        await bot.send_message(
            ADMIN_ID,
            "🛒 <b>NOVA COMPRA REALIZADA!</b>\n\n"
            "👤 <b>Cliente:</b>\n"
            f"├ Nome: {chat.full_name}\n"
            f"├ Username: {username}\n"
            f"└ ID: <code>{user_id}</code>\n\n"
            f"📦 <b>Produto:</b> {produto}\n"
            f"💰 <b>Valor:</b> {dinheiro(valor)}\n"
            f"💼 <b>Saldo restante:</b> {dinheiro(saldo_restante)}\n\n"
            f"🕒 <b>Data:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            parse_mode="HTML"
        )
    except Exception as erro:
        print("ERRO AO AVISAR ADMIN SOBRE COMPRA:", erro)

def recuperar_entrega_antiga(compra):
    try:
        data_compra = datetime.strptime(compra["data"], "%d/%m/%Y %H:%M")
        nome_produto = nome_arquivo_seguro(compra["produto"])
        prefixo = (
            f"{compra['user_id']}_{data_compra.strftime('%Y%m%d_%H%M')}"
            f"*_PL STORE - {nome_produto}.txt"
        )
        arquivos = sorted(PASTA_ENTREGAS.glob(prefixo))
        if arquivos:
            return arquivos[-1].read_text(encoding="utf-8", errors="ignore").strip()
    except (KeyError, TypeError, ValueError, OSError):
        pass
    return None

async def safe_edit(message, text, reply_markup=None):
    try:
        return await message.edit_text(text, reply_markup=reply_markup)
    except:
        return await message.edit_caption(caption=text, reply_markup=reply_markup)

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Comprar Produtos", callback_data="comprar")],
        [InlineKeyboardButton(text="💰 Depositar Saldo", callback_data="deposito")],
        [
            InlineKeyboardButton(text="👤 Perfil", callback_data="perfil"),
            InlineKeyboardButton(text="💼 Saldo", callback_data="saldo")
        ],
        [
            InlineKeyboardButton(text="📜 Histórico", callback_data="historico"),
            InlineKeyboardButton(text="📜 Termos e Trocas", callback_data="termos_trocas")
        ],
        [
            InlineKeyboardButton(text="📢 Referências", callback_data="referencias"),
            InlineKeyboardButton(text="🆘 Suporte", callback_data="suporte")
        ],
    ])

def btn_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
    ])

def btn_entrada_obrigatoria():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Entrar no canal", url=REFERENCIAS_LINK)],
        [InlineKeyboardButton(text="Já entrei — verificar", callback_data="verificar_entrada")]
    ])

async def usuario_no_canal(user_id):
    if is_admin(user_id):
        return True
    try:
        membro = await bot.get_chat_member(REFERENCIAS_CHAT_ID, user_id)
        return membro.status in ("member", "administrator", "creator")
    except Exception as erro:
        print("ERRO AO VERIFICAR INSCRIÇÃO:", erro)
        return False

def texto_entrada_obrigatoria():
    return (
        "Para acessar este bot é obrigatório entrar no canal de referências.\n\n"
        "Entre pelo botão abaixo e depois clique em Já entrei — verificar."
    )

async def garantir_acesso_mensagem(msg):
    if await usuario_no_canal(msg.from_user.id):
        return True
    await msg.answer(texto_entrada_obrigatoria(), reply_markup=btn_entrada_obrigatoria())
    return False

def menu_avisos_texto(user_id=None):
    return (
        "🚨 📋 REGRAS E INFORMAÇÕES 🚨\n\n"
        "💳MELHOR MATERIAL FULL DADOS DA NET💳\n\n"
        "👨🏾‍💻 | FULL direto do admin\n"
        "✅ | QUALIDADE extrema garantida\n"
        "📜 | Leia as REGRAS & os TERMOS de TROCAS antes de comprar\n"
        "🛒 | BOAS compras\n\n"
        "⚠️ ATENÇÃO, LEIA AS REGRAS ANTES DE COMPRAR!\n\n"
        "➡️ Nosso BOT entrega o material TESTADO ou VIRGEM, você quem escolhe❗️\n\n"
        "➡️ Comprou o material? Você tem 10 MINUTOS para testar e solicitar troca automática no BOT ou SUPORTE❗️\n\n"
        "➡️ Só aceitamos VÍDEOS seguindo as regras. Não aceitamos print❗️\n"
        "Lembrando: tem que estar dentro do prazo citado❗️\n\n"
        "🔴 Pedidos de trocas fora das regras acima serão desconsiderados 🔴\n\n"
        "📞 | Dúvidas ou solicitação de troca?\n"
        "➡️ Entre em contato com nosso SUPORTE: @plstoresuporte\n\n"
        f"🏦 | Carteira:\n"
        f" |_ID: {user_id}\n"
        f" |_💰 Saldo: R$ {saldos.get(user_id, 0):.2f}\n"
    )

async def enviar_menu(chat_id, user_id=None):
    banner = BASE_DIR / "banner.jpg"
    texto_menu = menu_avisos_texto(user_id)
    if banner.exists():
        await bot.send_photo(
            chat_id,
            FSInputFile(banner),
            caption=texto_menu,
            reply_markup=main_menu()
        )
    else:
        await bot.send_message(chat_id, texto_menu, reply_markup=main_menu())

@router.message(Command("start"))
async def start(msg: types.Message):
    if not await garantir_acesso_mensagem(msg):
        return
    await enviar_menu(msg.chat.id, msg.from_user.id)

@router.message(Command("buscar"))
async def buscar_produto(msg: types.Message):
    if not await garantir_acesso_mensagem(msg):
        return
    partes = msg.text.split(maxsplit=1)
    if len(partes) < 2 or not partes[1].strip():
        await msg.answer(
            titulo("🔎 BUSCAR PRODUTO") +
            "Digite o nome do produto que deseja consultar.\n\n"
            "Exemplos:\n"
            "• /buscar gold\n"
            "• /buscar black\n"
            "• /buscar elo\n"
            "• /buscar amex\n"
            "• /buscar mix5\n\n"
            f"{LINHA}"
        )
        return

    termo = partes[1].strip()
    resultado, encontrados = encontrar_produto_busca(termo)
    if resultado:
        item_id, prod = resultado
        estoque = contar_estoque(item_id)
        if estoque > 0:
            await msg.answer(
                titulo("🔎 CONSULTA") +
                f"✅ {prod['nome']} disponível.\n\n"
                f"📦 Estoque\n{estoque} unidades\n\n"
                f"💰 Valor\n{dinheiro(prod['preco'])}\n\n"
                f"{LINHA}"
            )
        else:
            await msg.answer(
                titulo("🔎 CONSULTA") +
                f"❌ {prod['nome']} indisponível no momento.\n\n"
                f"📦 Estoque\n0 unidades\n\n"
                f"{LINHA}"
            )
        return

    if encontrados:
        linhas = []
        for item_id, prod in encontrados[:8]:
            linhas.append(f"• {prod['nome']} — {contar_estoque(item_id)} unidades")
        await msg.answer(
            titulo("🔎 CONSULTA") +
            "Encontrei mais de uma opção parecida:\n\n" +
            "\n".join(linhas) +
            "\n\nDigite o nome mais completo.\n\n" +
            f"{LINHA}"
        )
        return

    await msg.answer(
        titulo("🔎 CONSULTA") +
        "❌ Produto não encontrado ou indisponível no momento.\n\n"
        "Confira se digitou o nome certinho.\n\n"
        "Exemplos:\n"
        "• /buscar gold\n"
        "• /buscar black\n"
        "• /buscar mix5\n\n"
        f"{LINHA}"
    )

# =========================================================
# CONSULTA POR BIN / BANCO (COM PAGINAÇÃO IGUAL IMAGEM 2)
# =========================================================

def extrair_campos_cartao(bloco):
    """Extrai os campos estruturados de um bloco de cartão (suporta | ou ; ou quebra de linha)."""
    # Tenta separar por pipe ou ponto e vírgula se estiver em linha única
    partes = [p.strip() for p in re.split(r'[|;]', bloco) if p.strip()]
    
    # Valores padrão caso venha incompleto
    cartao = partes[0] if len(partes) > 0 else bloco[:16]
    mes = partes[1] if len(partes) > 1 else "N/A"
    ano = partes[2] if len(partes) > 2 else "N/A"
    cvv = partes[3] if len(partes) > 3 else "***"
    bandeira = "Desconhecida"
    nivel = "Standard"
    tipo = "credit"
    banco = "N/A"
    pais = "Brasil"
    nome = "N/A"
    cpf = "N/A"

    # Se tiver mais partes, tenta mapear
    if len(partes) >= 5:
        # Tenta verificar se tem nome/cpf nas últimas partes
        for p in partes[4:]:
            if p.isdigit() and len(p) == 11:
                cpf = p
            elif not any(char.isdigit() for char in p) and len(p.split()) >= 2:
                nome = p
            elif len(p) <= 3 and p.isalpha():
                bandeira = p

    # Se o bloco tiver linhas com chaves
    for linha in bloco.splitlines():
        l_low = linha.lower()
        if "banco" in l_low or "bank" in l_low:
            banco = linha.split(":", 1)[-1].strip()
        elif "nome" in l_low:
            nome = linha.split(":", 1)[-1].strip()
        elif "cpf" in l_low:
            cpf = linha.split(":", 1)[-1].strip()

    # Formatar mes/ano
    mes_ano = f"{mes}/{ano}" if ano != "N/A" else mes

    # Mascarar cartão igual imagem 2 (ex: 559288***********)
    num_limpo = re.sub(r'\D', '', cartao)
    if len(num_limpo) >= 6:
        cartao_masc = num_limpo[:6] + "*" * (len(num_limpo) - 6)
    else:
        cartao_masc = cartao[:6] + "******"

    return {
        "cartao_masc": cartao_masc,
        "mes_ano": mes_ano,
        "cvv": cvv if len(cvv) <= 4 else "***",
        "bandeira": bandeira,
        "nivel": nivel,
        "tipo": tipo,
        "banco": banco,
        "pais": pais,
        "nome": nome,
        "cpf": cpf,
        "raw": bloco
    }

def buscar_cartoes_no_estoque(termo):
    termo = termo.strip().lower()
    resultados = [] # Lista de tuplas (item_id, prod, dados_cartao)

    for item_id, prod in produtos.items():
        blocos = ler_blocos_estoque(item_id)
        for bloco in blocos:
            if termo in bloco.lower():
                dados = extrair_campos_cartao(bloco)
                resultados.append((item_id, prod, dados))
    return resultados

async def mostrar_cartao_busca(message_or_call, resultados, index=0, edit=False):
    total = len(resultados)
    index = max(0, min(index, total - 1))
    item_id, prod, dados = resultados[index]
    user_id = message_or_call.from_user.id if hasattr(message_or_call, 'from_user') else message_or_call.chat.id
    saldo_atual = get_saldo(user_id)
    preco = prod["preco"]

    texto = (
        f"\n"
        f"{dados['cartao_masc'][:6]}...\n\n"
        f"📊 Mostrando {index + 1} de {total}\n\n"
        f"✨ Detalhes do cartão\n\n"
        f"💳 cartão: {dados['cartao_masc']}\n"
        f"🔑 cvv: {dados['cvv']}\n"
        f"💼 tipo: {dados['tipo']}\n"
        f"🏦 banco: {dados['banco']}\n"
        f"🌍 país: {dados['pais']}\n"
        f"👤 Nome: {dados['nome']}\n"
        f"🆔 cpf: {dados['cpf']}\n"
        f"💰 Preço: {preco}\n"
    )

    botoes = [
        [InlineKeyboardButton(text="🛒 QUERO COMPRAR", callback_data=f"comprasbin_{item_id}_{index}")],
    ]

    if total > 1:
        ant = (index - 1) % total
        prox = (index + 1) % total
        botoes.append([
            InlineKeyboardButton(text="<< CARTÃO ANTERIOR", callback_data=f"binpage_{index}_{ant}"),
            InlineKeyboardButton(text="PRÓXIMO CARTÃO >>", callback_data=f"binpage_{index}_{prox}")
        ])

    botoes.append([InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=botoes)

    # Armazenar temporariamente os resultados na sessão ou global para navegação rápida (ou passar via callback state/cache simples)
    global _cache_busca_bin
    if '_cache_busca_bin' not in globals():
        _cache_busca_bin = {}
    _cache_busca_bin[user_id] = resultados

    if edit:
        await safe_edit(message_or_call, texto, reply_markup=kb)
    else:
        if hasattr(message_or_call, 'answer'):
            await message_or_call.answer(texto, parse_mode="HTML", reply_markup=kb)
        else:
            await message_or_call.message.answer(texto, parse_mode="HTML", reply_markup=kb)

@router.message(Command("bin"))
async def consultar_bin(msg: types.Message):
    partes = msg.text.split(maxsplit=1)
    if len(partes) < 2:
        await msg.answer("❌ Use: /bin 123456")
        return
    bin_digitado = partes[1].strip()
    if not bin_digitado.isdigit() or len(bin_digitado) != 6:
        await msg.answer("❌ O BIN precisa ter exatamente 6 números.")
        return

    resultados = buscar_cartoes_no_estoque(bin_digitado)
    if not resultados:
        await msg.answer(f"🔎 BIN: {bin_digitado}\n\n❌ BIN INDISPONÍVEL NO ESTOQUE.")
        return

    await mostrar_cartao_busca(msg, resultados, index=0, edit=False)

@router.message(Command("bank"))
async def consultar_bank(msg: types.Message):
    partes = msg.text.split(maxsplit=1)
    if len(partes) < 2 or not partes[1].strip():
        await msg.answer("❌ Use: /bank nome do banco")
        return
    banco = partes[1].strip()

    resultados = buscar_cartoes_no_estoque(banco)
    if not resultados:
        await msg.answer(f"🏦 BANCO: {banco.upper()}\n\n❌ BANCO INDISPONÍVEL NO ESTOQUE.")
        return

    await mostrar_cartao_busca(msg, resultados, index=0, edit=False)

@router.callback_query(lambda c: c.data and c.data.startswith("binpage_"))
async def callback_binpage(call: types.CallbackQuery):
    user_id = call.from_user.id
    partes = call.data.split("_")
    novo_index = int(partes[2])

    if '_cache_busca_bin' in globals() and user_id in _cache_busca_bin:
        resultados = _cache_busca_bin[user_id]
        await mostrar_cartao_busca(call.message, resultados, index=novo_index, edit=True)
    else:
        await call.answer("Sessão expirada. Faça a consulta novamente.", show_alert=True)
    await call.answer()

@router.callback_query(lambda c: c.data and c.data.startswith("comprasbin_"))
async def callback_comprasbin(call: types.CallbackQuery):
    user_id = call.from_user.id
    partes = call.data.split("_")
    item_id = partes[1]
    index = int(partes[2])

    prod = produtos.get(item_id)
    if not prod:
        await call.answer("Produto não encontrado.", show_alert=True)
        return

    saldo = get_saldo(user_id)
    if saldo < prod["preco"]:
        await call.answer("Saldo insuficiente para realizar esta compra!", show_alert=True)
        return

    if '_cache_busca_bin' in globals() and user_id in _cache_busca_bin:
        resultados = _cache_busca_bin[user_id]
        if index < len(resultados):
            _, _, dados = resultados[index]
            entrega = dados["raw"]

            # Remove do estoque real
            blocos = ler_blocos_estoque(item_id)
            if entrega in blocos:
                blocos.remove(entrega)
                salvar_blocos_estoque(item_id, blocos)

            saldos[user_id] -= prod["preco"]
            salvar_saldos()
            registrar_compra(user_id, prod["nome"], prod["preco"], entrega)
            await avisar_admin_compra(user_id, prod["nome"], prod["preco"], saldos[user_id])
            await enviar_referencia_compra(prod["nome"], prod["preco"])

            arquivo_entrega, nome_arquivo = criar_arquivo_entrega_txt(user_id, prod, entrega)

            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
            ])
            await safe_edit(
                call.message,
                titulo("🎉 COMPRA REALIZADA COM SUCESSO!") +
                f"📦 Produto\n{prod['nome']}\n\n"
                f"💰 Valor\n{dinheiro(prod['preco'])}\n\n"
                f"💼 Saldo restante\n{dinheiro(saldos[user_id])}\n\n"
                "📄 Seu material foi preparado com sucesso.\n"
                "⬇️ O arquivo está logo abaixo.\n\n"
                f"{LINHA}",
                kb
            )

            await bot.send_document(
                chat_id=user_id,
                document=FSInputFile(arquivo_entrega, filename=nome_arquivo),
                caption="AQUI ESTÁ SUA INFO CC"
            )
            await call.answer("Compra aprovada!")
            return

    await call.answer("Erro ao processar compra. Tente consultar novamente.", show_alert=True)

# =========================================================

@router.message(Command("trocar"))
async def trocar_produto_menu(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Você não é admin.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 TROCAR NOMES", callback_data="trocar_nomes")],
        [InlineKeyboardButton(text="💰 TROCAR PREÇOS", callback_data="trocar_precos")],
    ])
    await msg.answer(
        "⚙️ <b>EDITAR PRODUTOS</b>\n\n"
        "Escolha o que deseja alterar:",
        parse_mode="HTML",
        reply_markup=kb
    )


def teclado_troca_produtos(acao):
    botoes = []
    for item_id, prod in produtos.items():
        botoes.append([
            InlineKeyboardButton(
                text=f"{prod['nome']} — {dinheiro(prod['preco'])}",
                callback_data=f"trocar_{acao}_{item_id}"
            )
        ])
    botoes.append([InlineKeyboardButton(text="❌ CANCELAR", callback_data="trocar_cancelar")])
    return InlineKeyboardMarkup(inline_keyboard=botoes)


@router.callback_query(lambda c: c.data == "trocar_nomes")
async def trocar_nomes(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Sem permissão.", show_alert=True)
        return
    await call.message.edit_text(
        "📝 <b>TROCAR NOME</b>\n\nEscolha o produto:",
        parse_mode="HTML",
        reply_markup=teclado_troca_produtos("nome")
    )
    await call.answer()


@router.callback_query(lambda c: c.data == "trocar_precos")
async def trocar_precos(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Sem permissão.", show_alert=True)
        return
    await call.message.edit_text(
        "💰 <b>TROCAR PREÇO</b>\n\nEscolha o produto:",
        parse_mode="HTML",
        reply_markup=teclado_troca_produtos("preco")
    )
    await call.answer()


@router.callback_query(lambda c: c.data == "trocar_cancelar")
async def trocar_cancelar(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Sem permissão.", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("❌ Alteração cancelada.")
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("trocar_nome_"))
async def escolher_nome_produto(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Sem permissão.", show_alert=True)
        return
    item_id = call.data[len("trocar_nome_"):]
    prod = produtos.get(item_id)
    if not prod:
        await call.answer("Produto não encontrado.", show_alert=True)
        return
    await state.update_data(item_id=item_id)
    await state.set_state(TrocaProdutoStates.aguardando_nome)
    await call.message.edit_text(
        f"📝 <b>NOVO NOME</b>\n\n"
        f"Produto atual: <b>{html.escape(prod['nome'])}</b>\n\n"
        "Digite o novo nome:",
        parse_mode="HTML"
    )
    await call.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("trocar_preco_"))
async def escolher_preco_produto(call: types.CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Sem permissão.", show_alert=True)
        return
    item_id = call.data[len("trocar_preco_"):]
    prod = produtos.get(item_id)
    if not prod:
        await call.answer("Produto não encontrado.", show_alert=True)
        return
    await state.update_data(item_id=item_id)
    await state.set_state(TrocaProdutoStates.aguardando_preco)
    await call.message.edit_text(
        f"💰 <b>NOVO PREÇO</b>\n\n"
        f"Produto: <b>{html.escape(prod['nome'])}</b>\n"
        f"Preço atual: <b>{dinheiro(prod['preco'])}</b>\n\n"
        "Digite somente o novo preço.\n"
        "Exemplo: <code>29,90</code>",
        parse_mode="HTML"
    )
    await call.answer()


@router.message(TrocaProdutoStates.aguardando_nome)
async def salvar_novo_nome(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    novo_nome = (msg.text or "").strip()
    if not novo_nome or len(novo_nome) > 80:
        await msg.answer("❌ Nome inválido. Digite um nome entre 1 e 80 caracteres.")
        return
    dados = await state.get_data()
    item_id = dados.get("item_id")
    if item_id not in produtos:
        await state.clear()
        await msg.answer("❌ Produto não encontrado.")
        return
    produtos[item_id]["nome"] = novo_nome
    salvar_config_produtos()
    await state.clear()
    await msg.answer(
        "✅ <b>NOME ALTERADO!</b>\n\n"
        f"📦 Produto: <b>{html.escape(novo_nome)}</b>\n"
        f"💰 Preço: <b>{dinheiro(produtos[item_id]['preco'])}</b>",
        parse_mode="HTML"
    )


@router.message(TrocaProdutoStates.aguardando_preco)
async def salvar_novo_preco(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return
    texto = (msg.text or "").strip().replace("R$", "").replace(" ", "").replace(",", ".")
    try:
        novo_preco = float(texto)
    except ValueError:
        await msg.answer("❌ Preço inválido. Exemplo: <code>29,90</code>", parse_mode="HTML")
        return
    if novo_preco < 0 or novo_preco > 1000000:
        await msg.answer("❌ Digite um preço entre R$ 0,00 e R$ 1.000.000,00.")
        return
    dados = await state.get_data()
    item_id = dados.get("item_id")
    if item_id not in produtos:
        await state.clear()
        await msg.answer("❌ Produto não encontrado.")
        return
    produtos[item_id]["preco"] = novo_preco
    salvar_config_produtos()
    await state.clear()
    await msg.answer(
        "✅ <b>PREÇO ALTERADO!</b>\n\n"
        f"📦 Produto: <b>{html.escape(produtos[item_id]['nome'])}</b>\n"
        f"💰 Novo preço: <b>{dinheiro(novo_preco)}</b>",
        parse_mode="HTML"
    )


@router.message(Command("admin"))
async def admin(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Você não é admin.")
        return
    pendentes = [d for d in depositos.values() if d["status"] == "pendente"]
    faturamento = sum(float(c.get("valor", 0)) for c in compras)
    await msg.answer(
        titulo("👑 PAINEL ADMIN") +
        f"📥 Depósitos pendentes: {len(pendentes)}\n"
        f"📦 Estoque total: {total_estoque()}\n"
        f"🛒 Compras registradas: {len(compras)}\n"
        f"💵 Faturamento registrado: {dinheiro(faturamento)}\n\n"
        "⚙️ Depósitos aparecem com botões para aprovar ou recusar.\n\n"
        f"{LINHA}"
    )

@router.message(Command("avisos"))
async def iniciar_avisos(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Você não é admin.")
        return

    await state.set_state(AvisoStates.aguardando_mensagem)
    await msg.answer(
        "📢 <b>ENVIAR AVISO</b>\n\n"
        "Digite agora a mensagem que deseja enviar para <b>todos os usuários do bot</b>.\n\n"
        "❌ Para cancelar, envie /cancelar_aviso",
        parse_mode="HTML"
    )


@router.message(Command("cancelar_aviso"), AvisoStates.aguardando_mensagem)
async def cancelar_avisos(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    await msg.answer("❌ Envio de aviso cancelado.")


@router.message(AvisoStates.aguardando_mensagem)
async def enviar_aviso_para_todos(msg: types.Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        await state.clear()
        return

    # Envia exatamente a mensagem que o admin mandou, sem adicionar
    # título, emoji ou qualquer outro texto. Isso também preserva
    # foto + legenda, formatação e outros tipos de mensagem suportados.
    usuarios = list(saldos.keys())
    enviados = 0
    falhas = 0

    await msg.answer(
        f"📤 Enviando exatamente esta mensagem para <b>{len(usuarios)}</b> usuários...",
        parse_mode="HTML"
    )

    for user_id in usuarios:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=msg.chat.id,
                message_id=msg.message_id
            )
            enviados += 1
            await asyncio.sleep(0.05)
        except Exception as erro:
            falhas += 1
            print(f"ERRO AO ENVIAR AVISO PARA {user_id}: {erro}")

    await state.clear()
    await msg.answer(
        "✅ <b>AVISO ENVIADO!</b>\n\n"
        f"👥 Usuários encontrados: <b>{len(usuarios)}</b>\n"
        f"📨 Enviados com sucesso: <b>{enviados}</b>\n"
        f"❌ Falhas: <b>{falhas}</b>",
        parse_mode="HTML"
    )


@router.message(Command("reembolsar"))
async def reembolsar(msg: types.Message):
    # Somente o administrador pode executar reembolsos.
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Você não é admin.")
        return

    partes = (msg.text or "").strip().split(maxsplit=1)
    if len(partes) != 2:
        await msg.answer("❌ Use assim:\n/reembolsar ID_DO_USUARIO")
        return

    try:
        user_id = int(partes[1].strip())
    except ValueError:
        await msg.answer("❌ O ID do usuário precisa ser numérico.")
        return

    # Procura a última compra desse usuário que ainda não foi reembolsada.
    compra = None
    for item in reversed(compras):
        try:
            mesmo_usuario = int(item.get("user_id")) == user_id
        except (TypeError, ValueError):
            mesmo_usuario = False
        if mesmo_usuario and not item.get("reembolsado", False):
            compra = item
            break

    if compra is None:
        await msg.answer(
            f"❌ Nenhuma compra pendente de reembolso encontrada para o ID <code>{user_id}</code>.",
            parse_mode="HTML"
        )
        return

    try:
        valor = float(compra.get("valor", 0))
    except (TypeError, ValueError):
        valor = 0

    if valor <= 0:
        await msg.answer("❌ O valor dessa compra é inválido para reembolso.")
        return

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # O item já foi retirado do estoque no momento da compra.
    # O reembolso NÃO devolve o item ao estoque.
    saldos[user_id] = get_saldo(user_id) + valor
    compra["reembolsado"] = True
    compra["data_reembolso"] = agora
    salvar_saldos()
    salvar_compras()

    novo_saldo = get_saldo(user_id)
    produto = str(compra.get("produto", "Produto não informado"))
    data_compra = str(compra.get("data", "Não informada"))

    # Busca nome e username reais do cliente para o relatório do admin.
    nome_cliente = "Não disponível"
    username = "-"
    try:
        chat = await bot.get_chat(user_id)
        nome_cliente = chat.full_name or "Não disponível"
        username = f"@{chat.username}" if chat.username else "-"
    except Exception as erro:
        print("ERRO AO BUSCAR CLIENTE NO REEMBOLSO:", erro)

    conteudo_produto = compra.get("conteudo", produto)

    relatorio = (
        "💰 <b>DETALHES DO REEMBOLSO:</b>\n\n"
        "👤 <b>Cliente:</b>\n"
        f"├ ID: <code>{user_id}</code>\n"
        f"├ Nome: {nome_cliente}\n"
        f"├ Username: {username}\n"
        f"└ Novo saldo: {dinheiro(novo_saldo)}\n\n"
        "📦 <b>PRODUTO REEMBOLSADO:</b>\n\n"
        f"{conteudo_produto}\n\n"
        f"├ Data da compra: {data_compra}\n"
        f"└ Data do reembolso: {agora}\n\n"
        "ℹ️ Status: ✅ <b>Reembolso realizado com sucesso!</b>"
    )

    await msg.answer(relatorio, parse_mode="HTML")

    # Aviso ao cliente, sem impedir o reembolso caso ele tenha bloqueado o bot.
    try:
        await bot.send_message(
            user_id,
            "💰 <b>REEMBOLSO REALIZADO!</b>\n\n"
            f"📦 Produto: {produto}\n"
            f"💵 Valor devolvido: {dinheiro(valor)}\n"
            f"💳 Seu novo saldo: {dinheiro(novo_saldo)}\n\n"
            "✅ O valor foi devolvido para sua carteira.",
            parse_mode="HTML"
        )
    except Exception as erro:
        print("ERRO AO AVISAR CLIENTE SOBRE REEMBOLSO:", erro)

@router.message(Command("gift"))
async def criar_gift(msg: types.Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Você não é admin.")
        return
    partes = (msg.text or "").strip().split(maxsplit=2)
    if len(partes) < 2:
        await msg.answer("Use assim:\n/gift 10\n/gift 10 100")
        return
    try:
        valor = float(partes[1].replace(",", "."))
        quantidade = int(partes[2]) if len(partes) == 3 else 1
    except ValueError:
        await msg.answer("❌ Valor ou quantidade inválida.")
        return
    if valor <= 0:
        await msg.answer("❌ O valor do gift precisa ser maior que zero.")
        return
    if quantidade < 1 or quantidade > 500:
        await msg.answer("❌ A quantidade deve ser de 1 até 500 gifts.")
        return

    codigos = []
    criado_em = datetime.now().strftime("%d/%m/%Y %H:%M")
    for _ in range(quantidade):
        codigo = gerar_codigo_gift()
        gifts[codigo] = {
            "valor": valor,
            "criado_por": msg.from_user.id,
            "criado_em": criado_em,
            "usado": False,
            "resgatado_por": None,
            "resgatado_em": None
        }
        codigos.append(codigo)
    salvar_gifts()

    valor_texto = f"R$ {valor:.2f}".replace(".", ",")
    if quantidade == 1:
        await msg.answer(
            "🏷 GIFT GERADO!\n\n"
            f"🏷 GIFT: /resgata {codigos[0]}\n"
            f"💰 VALOR: {valor_texto}\n"
            "📥 RESGATE: @PL_STOREBOT"
        )
    else:
        blocos = [
            "🏷 GIFT GERADO!\n\n"
            f"🏷 GIFT: /resgata {codigo}\n"
            f"💰 VALOR: {valor_texto}\n"
            "📥 RESGATE: @PL_STOREBOT"
            for codigo in codigos
        ]
        arquivo = types.BufferedInputFile(
            "\n\n".join(blocos).encode("utf-8"),
            filename=f"{quantidade}_gifts_{valor:.2f}.txt"
        )
        await msg.answer_document(
            arquivo,
            caption=f"✅ {quantidade} gifts de {valor_texto} gerados com sucesso."
        )

@router.message(Command("resgata"))
async def resgatar_gift(msg: types.Message):
    if not await garantir_acesso_mensagem(msg):
        return
    partes = (msg.text or "").strip().split(maxsplit=1)
    if len(partes) != 2:
        await msg.answer("Use assim: /resgata CÓDIGO")
        return
    codigo = partes[1].strip().upper()
    gift = gifts.get(codigo)
    if not gift:
        await msg.answer("❌ Gift inválido ou inexistente.")
        return
    if gift.get("usado"):
        await msg.answer("❌ Este gift já foi resgatado.")
        return

    user_id = msg.from_user.id
    valor = float(gift["valor"])
    saldos[user_id] = get_saldo(user_id) + valor
    gift["usado"] = True
    gift["resgatado_por"] = user_id
    gift["resgatado_em"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    salvar_saldos()
    salvar_gifts()

    await msg.answer(
        "✅ GIFT RESGATADO COM SUCESSO!\n\n"
        f"💰 Valor recebido: {dinheiro(valor)}\n"
        f"💼 Saldo atual: {dinheiro(saldos[user_id])}"
    )

    username = f"@{msg.from_user.username}" if msg.from_user.username else "Sem @username"
    try:
        await bot.send_message(
            ADMIN_ID,
            "🏷 GIFT RESGATADO!\n\n"
            f"🔑 Código: {codigo}\n"
            f"💰 Valor: {dinheiro(valor)}\n"
            f"👤 Usuário: {username}\n"
            f"🆔 ID: {user_id}\n"
            f"🕒 Data: {gift['resgatado_em']}"
        )
    except Exception as erro:
        print("ERRO AO AVISAR RESGATE DO GIFT:", erro)

async def animar_processamento(message, prod):
    await safe_edit(
        message,
        "⏰ Estou fazendo o checker do material escolhido, por favor, aguarde..."
    )
    await asyncio.sleep(5)

@router.callback_query()
async def callbacks(call: types.CallbackQuery):
    data = call.data
    user_id = call.from_user.id

    if data.startswith("binpage_") or data.startswith("comprasbin_"):
        return

    if data == "verificar_entrada":
        if await usuario_no_canal(user_id):
            await safe_edit(call.message, menu_avisos_texto(user_id), main_menu())
            await call.answer("Acesso liberado!")
        else:
            await call.answer("Você ainda não entrou no canal.", show_alert=True)
        return

    if not await usuario_no_canal(user_id):
        await safe_edit(
            call.message,
            texto_entrada_obrigatoria(),
            btn_entrada_obrigatoria()
        )
        await call.answer("Entre no canal para continuar.", show_alert=True)
        return

    if data == "menu":
        texto_menu = menu_avisos_texto(user_id)
        await safe_edit(call.message, texto_menu, main_menu())

    elif data == "perfil":
        username = call.from_user.username or "Sem usuário"
        await safe_edit(
            call.message,
            titulo("👤 MEU PERFIL") +
            f"🆔 ID\n{user_id}\n\n"
            f"👤 Usuário\n@{username}\n\n"
            f"💰 Saldo disponível\n{dinheiro(get_saldo(user_id))}\n\n"
            f"{LINHA}",
            btn_menu()
        )

    elif data == "saldo":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 Depositar Saldo", callback_data="deposito")],
            [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
        ])
        await safe_edit(
            call.message,
            titulo("💼 SEU SALDO") +
            f"💰 Saldo atual\n{dinheiro(get_saldo(user_id))}\n\n"
            "➕ Para adicionar saldo, clique no botão abaixo.\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "deposito":
        aguardando_deposito[user_id] = True
        await safe_edit(
            call.message,
            titulo("💰 DEPÓSITO VIA PIX AUTOMATICO") +
            f"✅ depósito mínimo\n{dinheiro(DEPOSITO_MINIMO)}\n\n"
            "💵 digite o valor que deseja depositar.\n\n"
            "Exemplo:/pix 10",
            btn_menu()
        )

    elif data == "comprar":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👑 VIP GRUPO - R$20", callback_data="vip")],
            [InlineKeyboardButton(text="💳 COMPRAR CC ", callback_data="card")],
            [InlineKeyboardButton(text="📱 eSIM", callback_data="esim")],
            [InlineKeyboardButton(text="🔎 BUSCAR PRODUTO", callback_data="buscar_produto")],
            [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
        ])
        await safe_edit(
            call.message,
            titulo("🛒 COMPRAR PRODUTOS") +
            "- 𝙚𝙨𝙘𝙤𝙡𝙝𝙖 𝙪𝙢𝙖 𝙘𝙖𝙩𝙚𝙜𝙤𝙧𝙞𝙖 𝙖𝙗𝙖𝙞𝙭𝙤:\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "esim":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 VIVO • R$ 20,00", callback_data="esim_vivo")],
            [InlineKeyboardButton(text="📱 TIM • R$ 40,00", callback_data="esim_tim")],
            [InlineKeyboardButton(text="📱 CLARO • R$ 35,00", callback_data="esim_claro")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="comprar")]
        ])
        await safe_edit(
            call.message,
            titulo("📱 eSIM") +
            "𝗲𝘀𝗰𝗼𝗹𝗵𝗮 𝗮 𝗼𝗽𝗲𝗿𝗮𝗱𝗼𝗿𝗮 𝗮𝗯𝗮𝗶𝘅𝗼:\n\n"
            "📶 VIVO • R$ 20,00\n"
            "📶 TIM • R$ 40,00\n"
            "📶 CLARO • R$ 35,00\n\n"
            "𝗰𝗮𝘀𝗼 𝘁𝗲𝗻𝗵𝗮 𝗼𝗰𝗼𝗿𝗿𝗶𝗱𝗼 𝗲𝗿𝗿𝗼 𝗻𝗮 𝗵𝗼𝗿𝗮 𝗱𝗮 𝗮𝘁𝗶𝘃𝗮𝗰̧𝗮𝗼, 𝗺𝗮𝗻𝗱𝗮 𝗽𝗿𝗶𝗻𝘁 𝗱𝗼 ERRO 𝗽𝗮𝗿𝗮 𝗼 𝘀𝘂𝗽𝗼𝗿𝘁𝗲, 𝗽𝗮𝗿𝗮 𝗾𝘂𝗲 𝗮 𝘀𝗶𝘁𝘂𝗮𝗰̧𝗮𝗼 𝘀𝗲𝗷𝗮 𝘃𝗲𝗿𝗳𝗶𝗰𝗮𝗱𝗮.🤝✅.\n\n"
            f"{LINHA}",
            kb
        )

    elif data.startswith("esim_") and data.split("_", 1)[1] in ("vivo", "tim", "claro"):
        operadora = data.split("_", 1)[1].lower()
        cfg = ESIM_CONFIG[operadora]
        ddds_disponiveis = ddds_esim_disponiveis(operadora)
        if not ddds_disponiveis:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Voltar", callback_data="esim")]
            ])
            await safe_edit(
                call.message,
                titulo(f"📱 eSIM {cfg['nome']}") +
                "❌ 𝗻𝗲𝗻𝗵𝘂𝗺 𝗲𝗦𝗜𝗠 𝗱𝗶𝘀𝗽𝗼𝗻𝗶́𝘃𝗲𝗹 𝗻𝗼 𝗲𝘀𝘁𝗼𝗾𝘂𝗲 𝗱𝗲𝘀𝘁𝗮 𝗼𝗽𝗲𝗿𝗮𝗱𝗼𝗿𝗮.\n\n"
                f"{LINHA}",
                kb
            )
            await call.answer()
            return

        botoes_ddd = []
        for i in range(0, len(ddds_disponiveis), 4):
            botoes_ddd.append([
                InlineKeyboardButton(text=f"DDD {ddd}", callback_data=f"esim_ddd_{operadora}_{ddd}")
                for ddd in ddds_disponiveis[i:i + 4]
            ])
        botoes_ddd.append([InlineKeyboardButton(text="🎲 Escolher DDD aleatório", callback_data=f"esim_random_{operadora}")])
        botoes_ddd.append([InlineKeyboardButton(text="🔙 Voltar", callback_data="esim")])

        await safe_edit(
            call.message,
            titulo(f"📱 eSIM {cfg['nome']}") +
            f"💰 Preço: {dinheiro(cfg['preco'])}\n\n"
            "📍 DDDs disponíveis no estoque:\n\n"
            "Escolha um DDD ou deixe o sistema sortear aleatoriamente.\n\n"
            f"{LINHA}",
            InlineKeyboardMarkup(inline_keyboard=botoes_ddd)
        )

    elif data.startswith("esim_random_"):
        operadora = data.replace("esim_random_", "").lower()
        cfg = ESIM_CONFIG.get(operadora)
        ddds = ddds_esim_disponiveis(operadora)
        if not ddds:
            await call.answer("Sem estoque.", show_alert=True)
            return
        ddd = random.choice(ddds)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Continuar com DDD {ddd}", callback_data=f"esim_selected_{operadora}_{ddd}")],
            [InlineKeyboardButton(text="🎲 Sortear novamente", callback_data=f"esim_random_{operadora}")],
            [InlineKeyboardButton(text="🔙 Voltar aos DDDs", callback_data=f"esim_{operadora}")]
        ])
        await safe_edit(
            call.message,
            titulo(f"🎲 eSIM {cfg['nome']}") +
            f"📍 DDD sorteado: <b>{ddd}</b>\n\n"
            f"💰 Valor: {dinheiro(cfg['preco'])}\n"
            f"📦 Unidades nesse DDD: {len(estoque_esim_por_ddd(operadora, ddd))}\n\n"
            "Clique para continuar.",
            kb
        )

    elif data.startswith("esim_ddd_"):
        partes = data.split("_")
        operadora = partes[2].lower()
        ddd = partes[3]
        cfg = ESIM_CONFIG.get(operadora)
        if not estoque_esim_por_ddd(operadora, ddd):
            await call.answer("Esse DDD ficou sem estoque.", show_alert=True)
            return
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💳 Comprar • {dinheiro(cfg['preco'])}", callback_data=f"esim_selected_{operadora}_{ddd}")],
            [InlineKeyboardButton(text="🎲 Escolher outro DDD", callback_data=f"esim_{operadora}")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="esim")]
        ])
        await safe_edit(
            call.message,
            titulo(f"📱 eSIM {cfg['nome']}") +
            f"📍 DDD: <b>{ddd}</b>\n"
            f"💰 Valor: <b>{dinheiro(cfg['preco'])}</b>\n"
            f"📦 Disponíveis: {len(estoque_esim_por_ddd(operadora, ddd))}\n\n"
            "Confira os dados e confirme a compra.",
            kb
        )

    elif data.startswith("esim_selected_"):
        partes = data.split("_")
        operadora = partes[2].lower()
        ddd = partes[3]
        cfg = ESIM_CONFIG.get(operadora)
        valor = cfg["preco"]

        if get_saldo(user_id) < valor:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Depositar Saldo", callback_data="deposito")],
                [InlineKeyboardButton(text="🔙 Voltar", callback_data=f"esim_{operadora}")]
            ])
            await safe_edit(
                call.message,
                titulo("❌ SALDO INSUFICIENTE") +
                f"📱 Operadora: {cfg['nome']}\n"
                f"📍 DDD: {ddd}\n\n"
                f"💰 Seu saldo: {dinheiro(get_saldo(user_id))}\n"
                f"💸 Necessário: {dinheiro(valor)}\n\n"
                f"{LINHA}",
                kb
            )
            await call.answer()
            return

        foto_estoque = retirar_esim(operadora, ddd)
        if foto_estoque is None:
            await call.answer("Esse DDD acabou de ficar sem estoque.", show_alert=True)
            return

        saldos[user_id] -= valor
        salvar_saldos()
        numero_pedido = len(compras) + 1
        compras.append({
            "user_id": user_id,
            "produto": f"eSIM {cfg['nome']} - DDD {ddd}",
            "valor": valor,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "ddd": ddd,
            "reembolsado": False
        })
        salvar_compras()
        await avisar_admin_compra(user_id, f"eSIM {cfg['nome']} - DDD {ddd}", valor, saldos[user_id])
        await enviar_referencia_compra(f"eSIM {cfg['nome']}", valor, ddd)

        legenda = (
            "🎉 <b>Pagamento confirmado!</b>\n\n"
            "✅ Seu eSIM foi entregue com sucesso!\n\n"
            f"📦 <b>Pedido:</b> #{numero_pedido}\n"
            f"📱 <b>Produto:</b> eSIM {cfg['nome']}\n"
            f"📍 <b>DDD:</b> {ddd}\n"
            f"💰 <b>Valor:</b> {dinheiro(valor)}\n"
            f"💳 <b>Novo saldo:</b> {dinheiro(saldos[user_id])}\n\n"
            "🔐 <b>Código de ativação:</b>\n"
            "Ver QR Code na imagem acima.\n\n"
            "⬇️ Escaneie o QR Code acima para ativar."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Meus Pedidos", callback_data="historico")],
            [InlineKeyboardButton(text="🛒 Comprar outro", callback_data="esim")],
            [InlineKeyboardButton(text="☰ Menu", callback_data="menu")]
        ])
        try:
            await call.message.delete()
        except Exception:
            pass
        await bot.send_photo(chat_id=user_id, photo=FSInputFile(foto_estoque), caption=legenda, parse_mode="HTML", reply_markup=kb)

    elif data == "buscar_produto":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="comprar")]
        ])
        await safe_edit(
            call.message,
            titulo("🔎 BUSCAR PRODUTO") +
            "𝗱𝗶𝗴𝗶𝘁𝗲 𝗼 𝗰𝗼𝗺𝗮𝗻𝗱𝗼 𝗮𝗯𝗮𝗶𝘅𝗼 𝗰𝗼𝗺 𝗼 𝗻𝗼𝗺𝗲 𝗱𝗼 𝗽𝗿𝗼𝗱𝘂𝘁𝗼.:\n\n"
            "/buscar nome_do_produto\n\n"
            "Exemplos:\n"
            "• /buscar gold\n"
            "• /buscar black\n"
            "• /buscar elo\n"
            "• /buscar amex\n"
            "• /buscar mix5\n\n"
            "o sistema verificará automaticamente se o produto está disponível.\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "vip":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Confirmar {dinheiro(VIP_PRICE)}", callback_data="confirm_vip")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="comprar")]
        ])
        await safe_edit(
            call.message,
            titulo("👑 VIP GRUPO") +
            f"💰 Valor\n{dinheiro(VIP_PRICE)}\n\n"
            "🚀 Acesso ao grupo exclusivo.\n"
            "✅ Clique abaixo para confirmar.\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "confirm_vip":
        saldo = get_saldo(user_id)
        if saldo < VIP_PRICE:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Depositar Saldo", callback_data="deposito")],
                [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
            ])
            await safe_edit(
                call.message,
                titulo("❌ SALDO INSUFICIENTE") +
                f"💰 Seu saldo\n{dinheiro(saldo)}\n\n"
                f"💸 Necessário\n{dinheiro(VIP_PRICE)}\n\n"
                f"{LINHA}",
                kb
            )
            await call.answer()
            return

        saldos[user_id] -= VIP_PRICE
        salvar_saldos()
        await avisar_admin_compra(user_id, "VIP", VIP_PRICE, saldos[user_id])
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
        ])
        await safe_edit(
            call.message,
            titulo("✅ VIP LIBERADO") +
            f"💼 Saldo restante\n{dinheiro(saldos[user_id])}\n\n"
            "🚀 Clique abaixo para entrar.\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "card":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 CC FULL", callback_data="ccfull")],
            [InlineKeyboardButton(text="📦 CC MIX", callback_data="ccmix")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="comprar")]
        ])
        await safe_edit(
            call.message,
            titulo("💳 CC FULL DADOS") +
            "- 𝙀𝙨𝙘𝙤𝙡𝙝𝙖 𝙖𝙗𝙖𝙞𝙭𝙤 𝙤 𝙥𝙧𝙤𝙙𝙪𝙩𝙤 𝙦𝙪𝙚 𝙙𝙚𝙨𝙚𝙟𝙖 𝙘𝙤𝙢𝙥𝙧𝙖𝙧.:\n\n"
            "💳 CC FULL\n"
            "🎲 CC MIX\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "ccfull":
        saldo_usuario = get_saldo(user_id)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{produtos['buy10']['nome']} • {dinheiro(produtos['buy10']['preco'])}", callback_data="buy10"),
                InlineKeyboardButton(text=f"{produtos['buy11']['nome']} • {dinheiro(produtos['buy11']['preco'])}", callback_data="buy11")
            ],
            [
                InlineKeyboardButton(text=f"{produtos['buy12']['nome']} • {dinheiro(produtos['buy12']['preco'])}", callback_data="buy12"),
                InlineKeyboardButton(text=f"{produtos['buy13']['nome']} • {dinheiro(produtos['buy13']['preco'])}", callback_data="buy13")
            ],
            [
                InlineKeyboardButton(text=f"{produtos['buy14']['nome']} • {dinheiro(produtos['buy14']['preco'])}", callback_data="buy14"),
                InlineKeyboardButton(text=f"{produtos['buy15']['nome']} • {dinheiro(produtos['buy15']['preco'])}", callback_data="buy15")
            ],
            [
                InlineKeyboardButton(text=f"{produtos['buy16']['nome']} • {dinheiro(produtos['buy16']['preco'])}", callback_data="buy16"),
                InlineKeyboardButton(text=f"{produtos['buy17']['nome']} • {dinheiro(produtos['buy17']['preco'])}", callback_data="buy17")
            ],
            [InlineKeyboardButton(text=f"{produtos['buy18']['nome']} • {dinheiro(produtos['buy18']['preco'])}", callback_data="buy18")],
            [
                InlineKeyboardButton(text=f"{produtos['buy19']['nome']} • {dinheiro(produtos['buy19']['preco'])}", callback_data="buy19"),
                InlineKeyboardButton(text=f"{produtos['buy20']['nome']} • {dinheiro(produtos['buy20']['preco'])}", callback_data="buy20")
            ],
            [
                InlineKeyboardButton(text=f"{produtos['buy21']['nome']} • {dinheiro(produtos['buy21']['preco'])}", callback_data="buy21"),
                InlineKeyboardButton(text=f"{produtos['buy22']['nome']} • {dinheiro(produtos['buy22']['preco'])}", callback_data="buy22")
            ],
            [
                InlineKeyboardButton(text=f"{produtos['buy23']['nome']} • {dinheiro(produtos['buy23']['preco'])}", callback_data="buy23"),
                InlineKeyboardButton(text=f"{produtos['buy24']['nome']} • {dinheiro(produtos['buy24']['preco'])}", callback_data="buy24")
            ],
            [
                InlineKeyboardButton(text=f"{produtos['buy25']['nome']} • {dinheiro(produtos['buy25']['preco'])}", callback_data="buy25"),
                InlineKeyboardButton(text=f"{produtos['buy26']['nome']} • {dinheiro(produtos['buy26']['preco'])}", callback_data="buy26")
            ],
            [InlineKeyboardButton(text=f"{produtos['buy27']['nome']} • {dinheiro(produtos['buy27']['preco'])}", callback_data="buy27")],
            [InlineKeyboardButton(text="🔙 VOLTAR", callback_data="card")]
        ])
        texto_cc_full = (
            "⚠️ COMPRE APENAS SE VOCÊ ESTIVER DE ACORDO COM AS REGRAS:\n\n"
            "‼️ NÃO É ACEITO PRINT, APENAS VÍDEO ‼️\n"
            "‼️ ACEITO SOMENTE TESTES GOOGLE (GPAY) ‼️\n"
            "‼️ OBRIGATÓRIO VINCULAR A INFO ‼️\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⏱️ TROCAS EM ATÉ 10 MINUTOS APÓS A COMPRA.\n"
            "⚠️ SALDO ADICIONADO NÃO É REEMBOLSÁVEL.\n"
            "💬 TROCAS — @PLSTORESUPORTE\n\n"
            "- ESCOLHA ABAIXO O PRODUTO QUE DESEJA COMPRAR.\n\n"
            f"🏦 CARTEIRA:\n ├ ID: {user_id}\n ├ 💰 SALDO: {dinheiro(saldo_usuario)}\n\n"
        )
        await safe_edit(call.message, texto_cc_full, kb)

    elif data == "ccmix":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📦 MIX 5 • R$150 • 📦 {contar_estoque('mix5')}", callback_data="mix5")],
            [InlineKeyboardButton(text=f"📦 MIX 10 • R$280 • 📦 {contar_estoque('mix10')}", callback_data="mix10")],
            [InlineKeyboardButton(text=f"📦 MIX 50 • R$1100 • 📦 {contar_estoque('mix50')}", callback_data="mix50")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data="card")]
        ])
        await safe_edit(
            call.message,
            titulo("📦 CC MIX") +
            "👇 Escolha uma opção abaixo:\n\n"
            "📦 Estoque atualizado automaticamente pelo TXT.\n\n"
            f"{LINHA}",
            kb
        )

    elif data in produtos:
        prod = produtos[data]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Confirmar {dinheiro(prod['preco'])}", callback_data=f"confirm_{data}")],
            [InlineKeyboardButton(text="🔙 Voltar", callback_data=prod["voltar"])]
        ])
        await safe_edit(
            call.message,
            f"✅| após confirmar a compra, sua info será enviada automaticamente para o checker. Aguarde a entrega.\n\n"
            f"🎖️| level: {prod['nome']}\n"
            f"💲| valor: {dinheiro(prod['preco'])}\n"
            f"💰| saldo atual: {dinheiro(get_saldo(user_id))}",
            kb
        )

    elif data.startswith("confirm_"):
        item_id = data.replace("confirm_", "")
        prod = produtos.get(item_id)
        if not prod:
            await call.answer()
            return
        saldo = get_saldo(user_id)
        if saldo < prod["preco"]:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💰 Depositar Saldo", callback_data="deposito")],
                [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
            ])
            await safe_edit(
                call.message,
                titulo("❌ SALDO INSUFICIENTE") +
                f"💰 Seu saldo\n{dinheiro(saldo)}\n\n"
                f"💸 Necessário\n{dinheiro(prod['preco'])}\n\n"
                f"{LINHA}",
                kb
            )
            await call.answer()
            return

        await animar_processamento(call.message, prod)
        entrega = entregar_produto(item_id)
        if entrega is None:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Voltar", callback_data=prod["voltar"])],
                [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
            ])
            await safe_edit(
                call.message,
                "❗️ Não consegui achar CCs lives deste nível no estoque. Tente novamente com outro nível ou BIN..\n\n"
                f"{LINHA}",
                kb
            )
            await call.answer()
            return

        saldos[user_id] -= prod["preco"]
        salvar_saldos()
        registrar_compra(user_id, prod["nome"], prod["preco"], entrega)
        await avisar_admin_compra(user_id, prod["nome"], prod["preco"], saldos[user_id])
        await enviar_referencia_compra(prod["nome"], prod["preco"])
        arquivo_entrega, nome_arquivo = criar_arquivo_entrega_txt(user_id, prod, entrega)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
        ])
        await safe_edit(
            call.message,
            titulo("🎉 ENTREGA CONCLUÍDA") +
            f"📦 Produto\n{prod['nome']}\n\n"
            f"💰 Valor\n{dinheiro(prod['preco'])}\n\n"
            f"💼 Saldo restante\n{dinheiro(saldos[user_id])}\n\n"
            "📄 Seu material foi preparado com sucesso.\n"
            "⬇️ O arquivo está logo abaixo.\n\n"
            f"{LINHA}",
            kb
        )
        await bot.send_document(
            chat_id=user_id,
            document=FSInputFile(arquivo_entrega, filename=nome_arquivo),
            caption="AQUI ESTÁ SUA INFO CC"
        )

    elif data == "historico" or data.startswith("historico_"):
        minhas = list(reversed([c for c in compras if c.get("user_id") == user_id][-10:]))
        if not minhas:
            texto = titulo("📜 HISTÓRICO") + "Você ainda não tem compras registradas.\n\n" + LINHA
            kb = btn_menu()
        else:
            try:
                pagina = int(data.replace("historico_", "")) if data.startswith("historico_") else 0
            except ValueError:
                pagina = 0
            pagina = max(0, min(pagina, len(minhas) - 1))
            compra = minhas[pagina]
            conteudo = compra.get("conteudo") or recuperar_entrega_antiga(compra) or "Não foi possível localizar o arquivo."

            texto = (
                titulo("📜 HISTÓRICO DE COMPRAS") +
                f"PRODUTO\n{compra['produto']}\n\n"
                f"VALOR\n{dinheiro(float(compra['valor']))}\n\n"
                f"DATA\n{compra['data']}\n\n"
                f"DADOS DO PRODUTO\n{conteudo}\n\n"
                f"Compra {pagina + 1} de {len(minhas)}\n\n"
                f"{LINHA}"
            )
            botoes = []
            if len(minhas) > 1:
                anterior = (pagina - 1) % len(minhas)
                proxima = (pagina + 1) % len(minhas)
                botoes.append([
                    InlineKeyboardButton(text="← Anterior", callback_data=f"historico_{anterior}"),
                    InlineKeyboardButton(text="Próximo →", callback_data=f"historico_{proxima}")
                ])
            botoes.append([InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")])
            kb = InlineKeyboardMarkup(inline_keyboard=botoes)

        await safe_edit(call.message, texto, kb)

    elif data == "termos_trocas":
        texto = (
            titulo("📜 TERMOS E TROCAS") +
            "⚠️ AVISO IMPORTANTE\n\n"
            "📱| APP PARA VERIFICAÇÃO (LIVE)\n\nLINK:http://payments.google.com/gp/w/u/0/home/paymentmethods \n\n"
            "✅ AS TROCAS SERÃO REALIZADAS APENAS MEDIANTE ANÁLISE DA EQUIPE DE SUPORTE.\n\n"
            "📹 CASO ENFRENTE ALGUM PROBLEMA COM O MATERIAL RECEBIDO, ENTRE EM CONTATO COM O SUPORTE E ENVIE UM VÍDEO DEMONSTRANDO O OCORRIDO PARA QUE A SITUAÇÃO POSSA SER VERIFICADA.\n\n"
            "🔄 APÓS A CONFIRMAÇÃO DA OCORRÊNCIA, A TROCA SERÁ REALIZADA CONFORME NOSSA POLÍTICA DE GARANTIA.\n\n"
            "🤝 NOSSO OBJETIVO É GARANTIR UM ATENDIMENTO RÁPIDO, JUSTO E TRANSPARENTE PARA TODOS OS CLIENTES."
        )
        await safe_edit(call.message, texto, btn_menu())

    elif data == "referencias":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Canal de Referências", url=REFERENCIAS_LINK)],
            [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
        ])
        await safe_edit(
            call.message,
            titulo("📢 AVISOS E REFERÊNCIAS") +
            "✅|veja prova, avisos e atualizações da nossa store..\n\n"
            "👇|clique no botao abaixo para acessar.\n\n"
            f"{LINHA}",
            kb
        )

    elif data == "suporte":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Chamar Suporte", url=SUPORTE_LINK)],
            [InlineKeyboardButton(text="⬅️ VOLTAR", callback_data="menu")]
        ])
        await safe_edit(
            call.message,
            titulo("🆘 SUPORTE PL STORE") +
            "💬 Precisa de ajuda?\n"
            "Clique no botão abaixo para chamar o suporte.\n\n"
            f"{LINHA}",
            kb
        )

    await call.answer()

@router.message(Command("pix"))
async def gerar_pix(msg: types.Message):
    import uuid
    import base64
    import html

    if not await garantir_acesso_mensagem(msg):
        return

    def brl(valor):
        return f"R${float(valor):.2f}".replace(".", ",")

    partes = (msg.text or "").strip().split(maxsplit=1)
    if len(partes) != 2:
        await msg.answer("❌ Use assim:\n\n<code>/pix 10</code>", parse_mode="HTML")
        return

    try:
        valor = float(partes[1].replace(",", "."))
    except ValueError:
        await msg.answer("❌ Valor inválido.\n\nExemplo: <code>/pix 10</code>", parse_mode="HTML")
        return

    if valor < DEPOSITO_MINIMO:
        await msg.answer(f"❌ O depósito mínimo é {brl(DEPOSITO_MINIMO)}.")
        return

    user_id = msg.from_user.id
    gerando = await msg.answer(f"⌛ Gerando PIX de {brl(valor)}, por favor aguarde...")
    referencia = f"telegram_{user_id}_{int(datetime.now().timestamp() * 1000)}"

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }

    payload = {
        "type": "online",
        "total_amount": f"{valor:.2f}",
        "external_reference": referencia,
        "processing_mode": "automatic",
        "transactions": {
            "payments": [
                {
                    "amount": f"{valor:.2f}",
                    "payment_method": {"id": "pix", "type": "bank_transfer"},
                    "expiration_time": "PT30M"
                }
            ]
        },
        "payer": {"email": "plfornecedor7@gmail.com"}
    }

    try:
        resposta = await asyncio.to_thread(
            requests.post,
            "https://api.mercadopago.com/v1/orders",
            headers=headers,
            json=payload,
            timeout=30
        )
        dados = resposta.json()
        if resposta.status_code not in (200, 201):
            await gerando.edit_text("❌ Não foi possível gerar o PIX.\nTente novamente em alguns instantes.")
            return

        order_id = dados.get("id")
        pagamentos = dados.get("transactions", {}).get("payments", [])
        if not order_id or not pagamentos:
            await gerando.edit_text("❌ O Mercado Pago não retornou o PIX.")
            return

        pagamento = pagamentos[0]
        metodo = pagamento.get("payment_method", {})
        qr_code = metodo.get("qr_code")
        qr_base64 = metodo.get("qr_code_base64")

        if not qr_code or not qr_base64:
            await gerando.edit_text("❌ Não foi possível gerar o QR Code.")
            return

        if qr_base64.startswith("data:"):
            qr_base64 = qr_base64.split(",", 1)[1]

        imagem_qr = base64.b64decode(qr_base64)
        foto = types.BufferedInputFile(imagem_qr, filename="pix.png")
        codigo_seguro = html.escape(qr_code)

        teclado_pix = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⌛ Aguardando Pagamento", callback_data="pix_aguardando")],
            [InlineKeyboardButton(text="☰ Menu", callback_data="menu")]
        ])

        legenda = (
            "✅ <b>Pagamento gerado</b>\n\n"
            "⚠️ Está com problemas no pagamento? Tente pagar de outro banco!\n\n"
            f"💰 <b>Valor a ser pago:</b> {brl(valor)}\n\n"
            "⏱️ <b>Prazo de expiração:</b> 30 Minutos\n\n"
            "💠 <b>Pix Copia e Cola:</b>\n"
            f"<code>{codigo_seguro}</code>\n\n"
            "💡 <b>Dica:</b> Clique no código acima para copiá-lo.\n\n"
            "<i>Após o pagamento, aguarde a confirmação para que o seu saldo seja creditado automaticamente.</i>"
        )

        try:
            await gerando.delete()
        except:
            pass

        mensagem_pix = await msg.answer_photo(photo=foto, caption=legenda, parse_mode="HTML", reply_markup=teclado_pix)

    except Exception as erro:
        print("ERRO AO GERAR PIX:", erro)
        try:
            await gerando.edit_text("❌ Erro ao gerar o PIX.")
        except:
            pass
        return

    async def verificar_pagamento():
        for _ in range(360):
            await asyncio.sleep(5)
            try:
                consulta = await asyncio.to_thread(
                    requests.get,
                    f"https://api.mercadopago.com/v1/orders/{order_id}",
                    headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"},
                    timeout=30
                )
                if consulta.status_code != 200:
                    continue
                ordem = consulta.json()
                pagamentos_atualizados = ordem.get("transactions", {}).get("payments", [])
                if not pagamentos_atualizados:
                    continue
                pagamento_atual = pagamentos_atualizados[0]
                status = pagamento_atual.get("status")
                detalhe = pagamento_atual.get("status_detail")

                if status == "processed" and detalhe == "accredited":
                    saldos[user_id] = saldos.get(user_id, 0) + valor
                    salvar_saldos()
                    teclado_pago = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="✅ Pagamento Aprovado", callback_data="pix_pago")],
                        [InlineKeyboardButton(text="☰ Menu", callback_data="menu")]
                    ])
                    legenda_pago = (
                        "✅ <b>PAGAMENTO APROVADO!</b>\n\n"
                        f"💰 <b>Valor pago:</b> {brl(valor)}\n\n"
                        f"💵 <b>Saldo atual:</b> {brl(saldos[user_id])}\n\n"
                        "✅ Seu saldo foi creditado automaticamente."
                    )
                    try:
                        await mensagem_pix.edit_caption(caption=legenda_pago, parse_mode="HTML", reply_markup=teclado_pago)
                    except Exception as erro:
                        print("ERRO AO ATUALIZAR MENSAGEM:", erro)
                    return

                if status in ("expired", "canceled", "failed"):
                    teclado_expirado = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="❌ PIX Expirado", callback_data="pix_expirado")],
                        [InlineKeyboardButton(text="☰ Menu", callback_data="menu")]
                    ])
                    try:
                        await mensagem_pix.edit_caption(
                            caption="❌ <b>PIX EXPIRADO</b>\n\nEsse pagamento não foi concluído.\n\nGere um novo PIX para tentar novamente.",
                            parse_mode="HTML",
                            reply_markup=teclado_expirado
                        )
                    except:
                        pass
                    return
            except Exception as erro:
                print("ERRO AO CONSULTAR PIX:", erro)

    asyncio.create_task(verificar_pagamento())

dp.include_router(router)

async def main():
    print("Bot iniciado com sucesso! Layout de busca atualizado conforme imagem 2.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
