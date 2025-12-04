import sys
import subprocess
import importlib.util
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path, PureWindowsPath
import itertools
from requests_oauthlib import OAuth2Session
import time
import requests
import io
import tempfile
from urllib.parse import urlsplit, quote
import os
import streamlit.components.v1 as components

#df_ibge = pd.read_parquet(r'C:\Users\Raphael.Oliveira\OneDrive - Transportes Della Volpe\Área de Trabalho\IBGE.parquet')

# --- LINK DIRETO DA IMAGEM NO GITHUB ---
url_imagem = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/AppBackground02.png"
url_logo = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/DellaVolpeLogoBranco.png"
fox_image = "https://raw.githubusercontent.com/DellaVolpe69/Images/main/Foxy4.png"

###### CONFIGURAR O TÍTULO DA PÁGINA #######
st.set_page_config(
    page_title="Prazos Default SLA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(
    f"""
    <style>
    /* Remove fundo padrão dos elementos de cabeçalho que às vezes ‘brigam’ com o BG */
    header, [data-testid="stHeader"] {{
        background: transparent;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<style>
/* Forçar cor branca em qualquer texto dentro de markdown ou write */
/* p, span, div, label { */
p, label {
    color: #EDEBE6 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* ===== Seletores amplos para pegar warnings/alerts em várias versões do Streamlit ===== */

/* Container genérico (várias builds usam esse data-testid) */
div[data-testid="stNotificationContent"],
div[data-testid="stNotification"],
div[data-testid="stAlert"],
div[class*="stNotification"],
div[class*="stAlert"],
div[role="alert"] {
    color: #EDEBE6 !important;         /* cor do texto */
}

/* Pegar explicitamente parágrafos/spans dentro do warning (onde o texto costuma estar) */
div[data-testid="stNotificationContent"] p,
div[data-testid="stNotificationContent"] span,
div[role="alert"] p,
div[role="alert"] span,
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span {
    color: #EDEBE6 !important;
}

/* Algumas builds colocam o texto dentro de elementos com classe .stMarkdown */
div[data-testid="stNotificationContent"] .stMarkdown,
div[role="alert"] .stMarkdown {
    color: #EDEBE6 !important;
}

/* Força também em labels e botões filhos (caso o warning tenha estruturas internas) */
div[data-testid="stNotification"] label,
div[role="alert"] label,
div[data-testid="stNotification"] button,
div[role="alert"] button {
    color: #EDEBE6 !important;
}
</style>
""", unsafe_allow_html=True)

##########################################
###### CARREGAR MÓDULOS E PARQUETS #######
# Caminho local onde o módulo será baixado
modulos_dir = Path(__file__).parent / "Modulos"

# Se o diretório ainda não existir, faz o clone direto do GitHub
if not modulos_dir.exists():
    print("📥 Clonando repositório Modulos do GitHub...")
    subprocess.run([
        "git", "clone",
        "https://github.com/DellaVolpe69/Modulos.git",
        str(modulos_dir)
    ], check=True)

# Garante que o diretório está no caminho de importação
if str(modulos_dir) not in sys.path:
    sys.path.insert(0, str(modulos_dir))

# Agora importa o módulo normalmente
from Modulos import AzureLogin
from Modulos import ConectionSupaBase
###################################
from Modulos.Minio.examples.MinIO import read_file  # ajuste o caminho se necessário

@st.cache_data(show_spinner="Carregando IBGE...")
def load_ibge():
    return read_file('dados/IBGE.parquet', 'calculation-view')

try:
    df_ibge = load_ibge()
except Exception as e:
    st.error(f"Erro ao carregar IBGE: {e}")
    st.stop()

#st.dataframe(df_ibge.head())

df_ibge.rename(columns={"NOME_MUNICIPIO": "CIDADE"}, inplace=True)
###################################
#combinacoes = sorted([f"{''.join(p)}" for p in itertools.product("NS", repeat=7)])

# 🔗 Conexão com o Supabase
supabase = ConectionSupaBase.conexao()

# Inicializa o estado da página
if "pagina" not in st.session_state:
    st.session_state.pagina = "menu"

# Funções para trocar de página
def ir_para_cadastrar():
    st.session_state.pagina = "Cadastrar"

def ir_para_editar():
    st.session_state.pagina = "Editar"

# --- CSS personalizado ---
st.markdown(f"""
    <style>
        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
                        url("{url_imagem}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        /* Inputs padrão: text_input, number_input, date_input, etc */
        input, textarea {{
            border: 1px solid white !important;
            border-radius: 5px !important;
        }}
        
        /* Selectbox (parte fechada) */
        .stSelectbox div[data-baseweb="select"] > div {{
            border: 1px solid white !important;
            border-radius: 5px !important;
        }}
        
        /* Date input container */
        .stDateInput input {{
            border: 1px solid white !important;
            border-radius: 5px !important;
        }}

        .stButton > button {{
            background-color: #FF5D01 !important;
            color: #EDEBE6 !important;
            border: 2px solid white !important;
            padding: 0.6em 1.2em;
            border-radius: 10px !important;
            font-size: 1rem;
            font-weight: 500;
            font-color: #EDEBE6 !important;
            cursor: pointer;
            transition: 0.2s ease;
            text-decoration: none !important;   /* 👈 AQUI remove de vez */
            display: inline-block;
        }}
        .stButton > button:hover {{
            background-color: #993700 !important;
            color: #FF5D01 !important;
            transform: scale(1.03);
            font-color: #FF5D01 !important;
            border: 2px solid #FF5D01 !important;
        }}

        /* RODAPÉ FIXO */
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: rgba(0, 0, 0, 0.6);
            color: white;
            text-align: center;
            font-size: 14px;
            padding: 8px 0;
            text-shadow: 1px 1px 2px black;
        }}
        .footer a {{
            color: #FF5D01;
            text-decoration: none;
            font-weight: bold;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE RODAPÉ ---
def rodape():
    st.markdown("""
        <div class="footer">
            © 2025 <b>Della Volpe</b> | Desenvolvido por <a href="#">Raphael Chiavegati Oliveira</a>
        </div>
    """, unsafe_allow_html=True)

##################################################################
################ FUNÇÕES DO FORMULÁRIO DE JANELAS ################
##################################################################

# Função para carregar dados
#def carregar_dados():
#    data = supabase.table("Prazos_Default_SLA").select("*").execute()
#    return pd.DataFrame(data.data)

def carregar_dados(limit=10000):
    data = (
        supabase.table("Prazos_Default_SLA")
        .select("*")
        .order("ID", desc=True)   # ordena do maior para o menor
        .limit(limit)             # pega só os últimos 5 mil
        .execute()
    )

    df = pd.DataFrame(data.data)

    # opcional: reordena do mais antigo → mais novo para ficar "bonito"
    df = df.sort_values(by="ID").reset_index(drop=True)

    return df

# Função para inserir
def inserir_registro(
    cliente, tp_medicao, referencia_medicao, tipo, faixa_km_inicio, faixa_km_fim, cidade_origem, uf_origem, cidade_destino, uf_destino,
    prazo_fracionado, prazo_lotacao, prazo_expresso, prazo_dedicado, ref_prazo_entrega, ref_prazo_coleta,
    incoterms, prazo_incoterms, coleta_normal, coleta_lotacao, coleta_expressa, coleta_dedicado,aplicacao, vigencia_inicio
):

    # -----------------------------
    # 🚀 Enviar ao Supabase
    # -----------------------------
    supabase.table("Prazos_Default_SLA").insert({
        "CLIENTE": cliente,
        "TPREFERENCIA_MEDICAO": tp_medicao,
        "REFERENCIA_MEDICAO": referencia_medicao,
        "TIPO": tipo,
        "FAIXA_KMINICIO": faixa_km_inicio,
        "FAIXA_KMFIM": faixa_km_fim,
        "CIDADE_ORIGEM": cidade_origem,
        "UF_ORIGEM": uf_origem,
        "CIDADE_DESTINO": cidade_destino,
        "UF_DESTINO": uf_destino,
        "PRAZO_FRACIONADO": prazo_fracionado,
        "PRAZO_LOTACAO": prazo_lotacao,
        "PRAZO_EXPRESSO": prazo_expresso,
        "PRAZO_DEDICADO": prazo_dedicado,
        "REF_PRAZO_ENTREGA": ref_prazo_entrega,
        "REF_PRAZO_COLETA": ref_prazo_coleta,
        "INCOTERMS": incoterms,
        "PRAZO_INCOTERMS": prazo_incoterms,
        "COLETA_NORMAL": coleta_normal,
        "COLETA_LOTACAO": coleta_lotacao,
        "COLETA_EXPRESSA": coleta_expressa,
        "COLETA_DEDICADO": coleta_dedicado,
        "APLICACAO": aplicacao,
        "VIGENCIA_INICIO": str(vigencia_inicio)
    }).execute()

# Função para atualizar faixa
def atualizar_registro_faixa(id,
                       referencia_medicao, 
                       faixa_km_inicio,
                       faixa_km_fim,
                       incoterms,
                       vigencia_inicio,
                       tipo):
    
    supabase.table("Prazos_Default_SLA").update({
        "REFERENCIA_MEDICAO": referencia_medicao,
        "FAIXA_KMINICIO": faixa_km_inicio,
        "FAIXA_KMFIM": faixa_km_fim,
        "INCOTERMS": incoterms,
        "VIGENCIA_INICIO": str(vigencia_inicio),
        "TIPO": tipo
    }).eq("ID", id).execute()
    st.success("✏️ Registro atualizado com sucesso!")
    
# Função para atualizar km
def atualizar_registro_km(id,
                       referencia_medicao,
                       incoterms,
                       vigencia_inicio,
                       tipo):
    
    supabase.table("Prazos_Default_SLA").update({
        "REFERENCIA_MEDICAO": referencia_medicao,
        "INCOTERMS": incoterms,
        "VIGENCIA_INICIO": str(vigencia_inicio),
        "TIPO": tipo
    }).eq("ID", id).execute()
    st.success("✏️ Registro atualizado com sucesso!")
    
# Função para atualizar tabela
def atualizar_registro_tabela(id,
                       referencia_medicao, 
                       uf_origem,
                       cidade_origem,
                       uf_destino,
                       cidade_destino,                       
                       incoterms,
                       vigencia_inicio,
                       tipo):
    
    supabase.table("Prazos_Default_SLA").update({
        "REFERENCIA_MEDICAO": referencia_medicao,
        "UF_ORIGEM": uf_origem,
        "CIDADE_ORIGEM": cidade_origem,
        "UF_DESTINO": uf_destino,
        "CIDADE_DESTINO": cidade_destino,        
        "INCOTERMS": incoterms,
        "VIGENCIA_INICIO": str(vigencia_inicio),
        "TIPO": tipo
    }).eq("ID", id).execute()
    st.success("✏️ Registro atualizado com sucesso!")

# Função para excluir
def excluir_registro(id):
    supabase.table("Prazos_Default_SLA").delete().eq("ID", id).execute()
    st.success("🗑️ Registro excluído com sucesso!")

# Função para limpar campos invisíveis
def limpar_campos():
    tipo_atual = st.session_state.get("tipo")

    # Se NÃO for FAIXA → limpa faixa_km_inicio e faixa_km_fim
    # if tipo_atual != "FAIXA":
    #     st.session_state["faixa_km_inicio"] = "NAO SE APLICA"
    #     st.session_state["faixa_km_fim"] = "NAO SE APLICA"
        
    # Se NÃO for TABELA → limpa cidade_origem, uf_origem, cidade_destino, uf_destino
    # if tipo_atual != "TABELA":
    #     st.session_state["cidade_origem"] = "NAO SE APLICA"
    #     st.session_state["uf_origem"] = "NAO SE APLICA"
    #     st.session_state["cidade_destino"] = "NAO SE APLICA"
    #     st.session_state["uf_destino"] = "NAO SE APLICA"
    
# Função para verificar se já existe um cadastro igual
def verificar_existencia(referencia_medicao, incoterms, prioridade, tipo_carga, vigencia_inicio):
    result = (
        supabase.table("Prazos_Default_SLA")
        .select("ID")
        .eq("REFERENCIA_MEDICAO", referencia_medicao)
        .eq("INCOTERMS", incoterms)
        .eq("PRIORIDADE", prioridade)
        .eq("TIPO_CARGA", tipo_carga)
        .eq("VIGENCIA_INICIO", vigencia_inicio)
        .execute()
    )

    # Se encontrar alguma linha → já existe
    return len(result.data) > 0

###########################################################################

# Função para verificar se já existe um cadastro igual para Faixa
def verificar_existencia_faixa(referencia_medicao, incoterms, faixa_km_inicio, faixa_km_fim, vigencia_inicio, tipo):
    result = (
        supabase.table("Prazos_Default_SLA")
        .select("ID")
        .eq("REFERENCIA_MEDICAO", referencia_medicao)
        .eq("INCOTERMS", incoterms)
        .eq("FAIXA_KMINICIO", faixa_km_inicio)
        .eq("FAIXA_KMFIM", faixa_km_fim)
        .eq("VIGENCIA_INICIO", vigencia_inicio)
        .eq("TIPO", tipo)
        .execute()
    )

    # Se encontrar alguma linha → já existe
    return len(result.data) > 0

###########################################################################

# Função para verificar se já existe um cadastro igual para Km
def verificar_existencia_km(referencia_medicao, incoterms, vigencia_inicio, tipo):
    result = (
        supabase.table("Prazos_Default_SLA")
        .select("ID")
        .eq("REFERENCIA_MEDICAO", referencia_medicao)
        .eq("INCOTERMS", incoterms)
        .eq("VIGENCIA_INICIO", vigencia_inicio)
        .eq("TIPO", tipo)
        .execute()
    )

    # Se encontrar alguma linha → já existe
    return len(result.data) > 0

###########################################################################

# Função para verificar se já existe um cadastro igual para Tabela
def verificar_existencia_tabela(referencia_medicao, incoterms, uf_origem, cidade_origem, uf_destino, cidade_destino, vigencia_inicio, tipo):
    result = (
        supabase.table("Prazos_Default_SLA")
        .select("ID")
        .eq("REFERENCIA_MEDICAO", referencia_medicao)
        .eq("INCOTERMS", incoterms)
        .eq("UF_ORIGEM", uf_origem)
        .eq("CIDADE_ORIGEM", cidade_origem)
        .eq("UF_DESTINO", uf_destino)
        .eq("CIDADE_DESTINO", cidade_destino)        
        .eq("VIGENCIA_INICIO", vigencia_inicio)
        .eq("TIPO", tipo)
        .execute()
    )

    # Se encontrar alguma linha → já existe
    return len(result.data) > 0

###########################################################################

#df_filial = MinIO.read_file('dados/CV_FILIAL.parquet', 'calculation-view')[['SALESORG', 'TXTMD_1']].drop_duplicates().reset_index(drop=True)
#df_filial = df_filial[['SALESORG', 'TXTMD_1']].drop_duplicates().reset_index(drop=True)

##################################################################
##################################################################
##################################################################

# --- MENU PRINCIPAL ---
if st.session_state.pagina == "menu":
    st.markdown(f"""
        <div class="header" style="text-align: center; padding-top: 2em;">
            <img src="{url_logo}" alt="Logo Della Volpe" 
                 style="width: 40%; max-width: 200px; height: auto; margin-bottom: 10px;">
            <h1 style="color: #EDEBE6; text-shadow: 1px 1px 3px black;">
                Prazos Default SLA
            </h1>
        </div>
    """, unsafe_allow_html=True)
    # Espaço antes dos botões (ajuste quantos <br> quiser)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.button("Cadastrar", use_container_width=True, on_click=ir_para_cadastrar)
        st.button("Editar", use_container_width=True, on_click=ir_para_editar)
    rodape()

# --- PÁGINA CADASTRAR ---
if st.session_state.pagina == "Cadastrar":
    st.markdown(
    "<h1 style='text-align: center; color: #EDEBE6; text-shadow: 1px 1px 3px black;'>"
    "📝 Cadastrar Prazos Default SLA"
    "</h1>",
    unsafe_allow_html=True
)
    
    ############################################
    
    cliente = st.text_input("Cliente")
    
    ############################################
    
    tp_medicao = st.selectbox(
        "Tipo de Referência da Medição",
        options=["BP", "CNJP_SACADO", "CONTRATO_CODIGO", "CONTRATO_DESCRICAO"],
        index=0  
    )    
    
    ############################################
    
    referencia_medicao = st.text_input("Referência da Medição")
    
    ############################################
    
    tipo = st.selectbox(
        "Tipo",
        options=["FAIXA", "KM", "TABELA"],
        key="tipo",
        on_change=limpar_campos  # 🔥 dispara a limpeza ao mudar
    )
    
    ############################################
    ################### FAIXA ##################
    
    if tipo == "FAIXA":
        faixa_km_inicio = st.selectbox(
            "Faixa Km Início",
            options=["0", "300", "301", "800", "801", "1300", "1301",
                    "1400", "1401", "1800", "1801", "2000", "2001", "2300", "2301",
                    "2600", "2601", "2800", "2801", "3300", "3301", "3600", "3601",
                    "3800", "3801"],
            index=0  
        )
    
        ############################################
        
        faixa_km_fim = st.selectbox(
            "Faixa Km Fim",
            options=["300", "800", "1300", "1400", "1800", "2000", "2300",
                    "2600", "2800", "3200", "3300", "3600", "3800"],
            index=0  
        )
    
    ############################################

    elif tipo == "TABELA":
        # Lista de UFs únicas de Origem
        uf_list_origem = sorted(df_ibge["UF"].unique())
        # Lista de UFs únicas de Destino
        uf_list_destino = sorted(df_ibge["UF"].unique())
        
        # Pergunta 1: Escolha da UF Origem
        uf_origem = st.selectbox(
            "Escolha a UF de origem:",
            options=uf_list_origem,
            index=0
        )

        # Filtra as cidades correspondentes à UF selecionada
        cidades_filtradas_origem = (df_ibge.loc[df_ibge["UF"] == uf_origem, "CIDADE"].sort_values().tolist())
        
        # Adiciona o valor "NULO" no início
        cidades_opcoes_origem = ["NAO SE APLICA"] + cidades_filtradas_origem

        # Pergunta 2: Escolha da Cidade Origem (dependente da UF Origem)
        cidade_origem = st.selectbox(
            "Escolha a cidade de origem:",
            options=cidades_opcoes_origem,
            index=0
        )
        ############################################################### 

        # Pergunta 1: Escolha da UF Destino
        uf_destino = st.selectbox(
            "Escolha a UF de destino:",
            options=uf_list_destino,
            index=0
        )

        # Filtra as cidades correspondentes à UF selecionada
        cidades_filtradas_destino = (df_ibge.loc[df_ibge["UF"] == uf_destino, "CIDADE"].sort_values().tolist())
        
        # Adiciona o valor "NULO" no início
        cidades_opcoes_destino = ["NAO SE APLICA"] + cidades_filtradas_destino

        # Pergunta 2: Escolha da Cidade Destino (dependente da UF Destino)
        cidade_destino = st.selectbox(
            "Escolha a cidade de destino:",
            options=cidades_opcoes_destino,
            index=0
        )
        
        ############################################################### 
    
    prazo_fracionado = st.text_input("Prazo Fracionado")
    if prazo_fracionado:
        if not prazo_fracionado.isdigit():
            st.error("⚠️ O prazo deve conter apenas números.")    
    ############################################
    
    prazo_lotacao = st.text_input("Prazo Lotação")
    if prazo_lotacao:
        if not prazo_lotacao.isdigit():
            st.error("⚠️ O prazo deve conter apenas números.")        
    ############################################
    
    prazo_expresso = st.text_input("Prazo Expresso")
    if prazo_expresso:
        if not prazo_expresso.isdigit():
            st.error("⚠️ O prazo deve conter apenas números.")        
    ############################################
    
    prazo_dedicado = st.text_input("Prazo Dedicado")
    if prazo_dedicado:
        if not prazo_dedicado.isdigit():
            st.error("⚠️ O prazo deve conter apenas números.")        
    ############################################
    
    ref_prazo_entrega = st.selectbox(
        "Referência de Prazo Entrega",
        options=["", "CONTA", "NAO CONTA", "NAO SE APLICA"],
        index=0  
    )
    
    ############################################
    
    ref_prazo_coleta = st.selectbox(
        "Referência de Prazo Coleta",
        options=["", "CONTA", "NAO CONTA", "NAO SE APLICA"],
        index=0  
    )
    
    ############################################
    
    incoterms = st.selectbox(
        "Incoterms",
        options=["EXW", "FCA"],
        index=0  
    )
    
    ############################################
    
    prazo_incoterms = st.selectbox(
        "Prazo Incoterms",
        options=["NAO SE APLICA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        index=0  
    )
    
    ############################################
    
    coleta_normal = st.selectbox(
        "Coleta Normal",
        options=["NAO SE APLICA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        index=0  
    )
    
    ############################################
    
    coleta_lotacao = st.selectbox(
        "Coleta Lotação",
        options=["NAO SE APLICA", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        index=0  
    )
    
    ############################################
    
    coleta_expressa = st.selectbox(
        "Coleta Expressa",
        options=["NAO SE APLICA", "0", "0,5", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        index=0  
    )
    
    ############################################    
    
    coleta_dedicado = st.selectbox(
        "Coleta Dedicado",
        options=["NAO SE APLICA", "0", "0,5", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        index=0  
    )
    
    ############################################   
    
    aplicacao = st.selectbox(
        "Aplicação",
        options=["CORRIDO", "ÚTIL"],
        index=0  
    )
    
    ############################################
    
    vigencia_inicio = st.date_input("Vigência Início", date.today())
    
    ############################################
    
    # Recupera valores do session_state antes de salvar
    # uf_origem = st.session_state.get("uf_origem", "NAO SE APLICA")
    # cidade_origem = st.session_state.get("cidade_origem", "NAO SE APLICA")
    # uf_destino = st.session_state.get("uf_destino", "NAO SE APLICA")
    # cidade_destino = st.session_state.get("cidade_destino", "NAO SE APLICA")
    # faixa_km_inicio = st.session_state.get("faixa_km_inicio", "NAO SE APLICA")
    # faixa_km_fim = st.session_state.get("faixa_km_fim", "NAO SE APLICA")
    
    # Criar espaço vazio nas laterais e centralizar os botões
    esp1, centro, esp2 = st.columns([1, 2, 1])

    with centro:
        # Duas colunas de mesma largura para os botões
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Voltar ao Menu", use_container_width=True):
                st.session_state.pagina = "menu"
                st.rerun()
                st.stop() 

        with col2:
            ############################################
            
            if tipo == "FAIXA":
                if st.button("💾 Salvar", use_container_width=True):
                    cidade_origem = "NAO SE APLICA"
                    uf_origem = "NAO SE APLICA"
                    cidade_destino = "NAO SE APLICA"
                    uf_destino = "NAO SE APLICA"
                    existe = verificar_existencia_faixa(
                        referencia_medicao, 
                        incoterms, 
                        faixa_km_inicio, 
                        faixa_km_fim, 
                        vigencia_inicio,
                        tipo
                    )

                    if existe:                    
                        st.error("❌ Este cadastro já existe.")

                    else:
                        if referencia_medicao and incoterms and faixa_km_inicio and faixa_km_fim and vigencia_inicio:
                            #################################################
                            valor_prazo_fracionado = prazo_fracionado.strip()

                            if valor_prazo_fracionado == "":
                                valor_prazo_fracionado = "NAO SE APLICA"
                                
                            prazo_fracionado = valor_prazo_fracionado
                            #################################################
                            valor_prazo_lotacao = prazo_lotacao.strip()

                            if valor_prazo_lotacao == "":
                                valor_prazo_lotacao = "NAO SE APLICA"
                                
                            prazo_lotacao = valor_prazo_lotacao
                            #################################################
                            valor_prazo_expresso = prazo_expresso.strip()

                            if valor_prazo_expresso == "":
                                valor_prazo_expresso = "NAO SE APLICA"
                                
                            prazo_expresso = valor_prazo_expresso
                            #################################################
                            valor_prazo_dedicado = prazo_dedicado.strip()

                            if valor_prazo_dedicado == "":
                                valor_prazo_dedicado = "NAO SE APLICA"
                                
                            prazo_dedicado = valor_prazo_dedicado
                            #################################################
                                                                                    
                            inserir_registro(
                                cliente=cliente,
                                tp_medicao=tp_medicao,
                                referencia_medicao=referencia_medicao,
                                tipo=tipo,
                                faixa_km_inicio=faixa_km_inicio,
                                faixa_km_fim=faixa_km_fim,
                                uf_origem=uf_origem,
                                cidade_origem=cidade_origem,
                                uf_destino=uf_destino,
                                cidade_destino=cidade_destino,
                                prazo_fracionado=prazo_fracionado,
                                prazo_lotacao=prazo_lotacao,
                                prazo_expresso=prazo_expresso,
                                prazo_dedicado=prazo_dedicado,
                                ref_prazo_entrega=ref_prazo_entrega,
                                ref_prazo_coleta=ref_prazo_coleta,
                                incoterms=incoterms,
                                prazo_incoterms=prazo_incoterms,
                                coleta_normal=coleta_normal,
                                coleta_lotacao=coleta_lotacao,
                                coleta_expressa=coleta_expressa,
                                coleta_dedicado=coleta_dedicado,
                                aplicacao=aplicacao,
                                vigencia_inicio=vigencia_inicio
                            )

                            st.session_state.pagina = "Sucesso"  # vai pra página oculta
                        else:
                            st.warning("⚠️ Preencha todos os campos obrigatórios.")
                        #st.rerun()
                        #st.stop() 
                        
            ######################################################################################## 
            
            elif tipo == "KM":
                if st.button("💾 Salvar", use_container_width=True):
                    faixa_km_inicio = "NAO SE APLICA"
                    faixa_km_fim = "NAO SE APLICA"
                    cidade_origem = "NAO SE APLICA"
                    uf_origem = "NAO SE APLICA"
                    cidade_destino = "NAO SE APLICA"
                    uf_destino = "NAO SE APLICA"
                    existe = verificar_existencia_km(
                        referencia_medicao, 
                        incoterms,
                        vigencia_inicio,
                        tipo
                    )

                    if existe:                    
                        st.error("❌ Este cadastro já existe.")

                    else:
                        if referencia_medicao and incoterms and vigencia_inicio:
                            inserir_registro(
                                cliente=cliente,
                                tp_medicao=tp_medicao,
                                referencia_medicao=referencia_medicao,
                                tipo=tipo,
                                faixa_km_inicio=faixa_km_inicio,
                                faixa_km_fim=faixa_km_fim,
                                uf_origem=uf_origem,
                                cidade_origem=cidade_origem,
                                uf_destino=uf_destino,
                                cidade_destino=cidade_destino,
                                prazo_fracionado=prazo_fracionado,
                                prazo_lotacao=prazo_lotacao,
                                prazo_expresso=prazo_expresso,
                                prazo_dedicado=prazo_dedicado,
                                ref_prazo_entrega=ref_prazo_entrega,
                                ref_prazo_coleta=ref_prazo_coleta,
                                incoterms=incoterms,
                                prazo_incoterms=prazo_incoterms,
                                coleta_normal=coleta_normal,
                                coleta_lotacao=coleta_lotacao,
                                coleta_expressa=coleta_expressa,
                                coleta_dedicado=coleta_dedicado,
                                aplicacao=aplicacao,
                                vigencia_inicio=vigencia_inicio
                            )

                            st.session_state.pagina = "Sucesso"  # vai pra página oculta
                        else:
                            st.warning("⚠️ Preencha todos os campos obrigatórios.")
                        #st.rerun()
                        #st.stop() 
                        
            ######################################################################################## 
            
            elif tipo == "TABELA":
                if st.button("💾 Salvar", use_container_width=True):
                    faixa_km_inicio = "NAO SE APLICA"
                    faixa_km_fim = "NAO SE APLICA"
                    # st.write("DEBUG verifica tabela:", {
                    #     "referencia_medicao": referencia_medicao,
                    #     "incoterms": incoterms,
                    #     "uf_origem": uf_origem,
                    #     "cidade_origem": cidade_origem,
                    #     "uf_destino": uf_destino,
                    #     "cidade_destino": cidade_destino,
                    #     "vigencia_inicio": str(vigencia_inicio),
                    #     "tipo": tipo,
                    # })

                    existe = verificar_existencia_tabela(
                        referencia_medicao, 
                        incoterms,
                        uf_origem,
                        cidade_origem,
                        uf_destino,
                        cidade_destino,                        
                        vigencia_inicio,
                        tipo
                    )

                    if existe:                    
                        st.error("❌ Este cadastro já existe.")

                    else:
                        if referencia_medicao and incoterms and cidade_origem and uf_origem and cidade_destino and uf_destino and vigencia_inicio:
                            inserir_registro(
                                cliente=cliente,
                                tp_medicao=tp_medicao,
                                referencia_medicao=referencia_medicao,
                                tipo=tipo,
                                faixa_km_inicio=faixa_km_inicio,
                                faixa_km_fim=faixa_km_fim,
                                uf_origem=uf_origem,
                                cidade_origem=cidade_origem,
                                uf_destino=uf_destino,
                                cidade_destino=cidade_destino,
                                prazo_fracionado=prazo_fracionado,
                                prazo_lotacao=prazo_lotacao,
                                prazo_expresso=prazo_expresso,
                                prazo_dedicado=prazo_dedicado,
                                ref_prazo_entrega=ref_prazo_entrega,
                                ref_prazo_coleta=ref_prazo_coleta,
                                incoterms=incoterms,
                                prazo_incoterms=prazo_incoterms,
                                coleta_normal=coleta_normal,
                                coleta_lotacao=coleta_lotacao,
                                coleta_expressa=coleta_expressa,
                                coleta_dedicado=coleta_dedicado,
                                aplicacao=aplicacao,
                                vigencia_inicio=vigencia_inicio
                            )

                            st.session_state.pagina = "Sucesso"  # vai pra página oculta
                        else:
                            st.warning("⚠️ Preencha todos os campos obrigatórios.")
                        #st.rerun()
                        #st.stop() 

# --- PÁGINA EDITAR ---
elif st.session_state.pagina == "Editar":
    st.markdown(
    "<h1 style='text-align: center; color: #EDEBE6; text-shadow: 1px 1px 3px black;'>"
    "✏️ Editar"
    "</h1>",
    unsafe_allow_html=True
)
    st.markdown("<h3 style='color: white;'>Lista de Registros</h3>", unsafe_allow_html=True)
    df = carregar_dados()
    
    # estilo abrangente para títulos de expander (várias versões do Streamlit)
    st.markdown("""
    <style>
    /* seletor moderno: expander com data-testid */
    div[data-testid="stExpander"] > div[role="button"],
    div[data-testid="stExpander"] > button,
    div[data-testid="stExpander"] summary {
        color: #EDEBE6 !important;
    }
    
    /* spans/labels dentro do botão (algumas builds usam span) */
    div[data-testid="stExpander"] span,
    div[data-testid="stExpander"] [aria-expanded="true"] span {
        color: #FF8C00 !important;
    }

    /* ícone SVG do expander (setinha) */
    div[data-testid="stExpander"] svg,
    div[data-testid="stExpander"] button svg {
        fill: #EDEBE6 !important;
        stroke: #EDEBE6 !important;
    }

    /* fallback para classes antigas / alternadas */
    .st-expanderHeader,
    .stExpanderHeader,
    .css-1v0mbdj-summary { /* exemplo de classe gerada dinamicamente */
        color: #EDEBE6 !important;
    }

    /* força também quando o texto está dentro de um label/button com background */
    div[data-testid="stExpander"] button {
        color: #EDEBE6 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if not df.empty:
        # 🔍 Filtros

        with st.expander("🔎 Filtros"):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                filtro_referencia_medicao = st.selectbox(
                    "Referência Medição", 
                    ["Todas"] + sorted(df["REFERENCIA_MEDICAO"].unique().tolist())
                )

            with col2:
                filtro_incoterms = st.selectbox(
                    "Incoterms", 
                    ["Todas"] + sorted(df["INCOTERMS"].unique().tolist())
                )
                
            with col3:
                filtro_uforigem = st.selectbox(
                    "UF Origem", 
                    ["Todas"] + sorted(df["UF_ORIGEM"].unique().tolist())
                )
                
            with col4:
                filtro_cidadeorigem = st.selectbox(
                    "Cidade Origem", 
                    ["Todas"] + sorted(df["CIDADE_ORIGEM"].unique().tolist())
                )

            # Filtro de data
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data Início (vigência)", value=None)
            with col2:
                data_fim = st.date_input("Data Fim (vigência)", value=None)

        # Aplicar filtros
        if filtro_referencia_medicao != "Todas":
            df = df[df["REFERENCIA_MEDICAO"] == filtro_referencia_medicao]

        if filtro_incoterms != "Todas":
            df = df[df["INCOTERMS"] == filtro_incoterms]
            
        if filtro_uforigem != "Todas":
            df = df[df["UF_ORIGEM"] == filtro_uforigem]

        if filtro_cidadeorigem != "Todas":
            df = df[df["CIDADE_ORIGEM"] == filtro_cidadeorigem]

        if data_inicio:
            df = df[pd.to_datetime(df["VIGENCIA_INICIO"]) >= pd.to_datetime(data_inicio)]
        if data_fim:
            df = df[pd.to_datetime(df["VIGENCIA_INICIO"]) <= pd.to_datetime(data_fim)]

        # Mostrar tabela filtrada
        #df.drop(columns=['CREATED_AT'], inplace=True)
        df.sort_values(by=["ID", "REFERENCIA_MEDICAO", "INCOTERMS", "UF_ORIGEM", "CIDADE_ORIGEM", "VIGENCIA_INICIO"], ascending=[False, False, True, True, True, True], inplace=True)
        st.dataframe(df.copy().set_index('ID'))

    if not df.empty:

        # Selecionar registro para editar/excluir
        id_registro = st.selectbox("Selecione o ID para editar/excluir", df["ID"].sort_values(ascending=False))

        registro = df[df["ID"] == id_registro].iloc[0]

        with st.expander("✏️ Editar Registro"):
            opcoes_incoterms = ["EXW", "FCA"]
            opcoes_prioridade = ["NORMAL", "EXPRESSA"]
            opcoes_tipo_carga = ["FRACIONADO", "LOTACAO", "DEDICADO", "PRODUTO QUIMICO"]
            opcoes_faixa_km_inicio = ["0", "300", "301", "800", "801", "1300", "1301",
                    "1400", "1401", "1800", "1801", "2000", "2001", "2300", "2301",
                    "2600", "2601", "2800", "2801", "3300", "3301", "3600", "3601",
                    "3800", "3801"]
            opcoes_faixa_km_fim = ["300", "800", "1300", "1400", "1800", "2000", "2300",
                    "2600", "2800", "3200", "3300", "3600", "3800"]
            
            # Lista de UFs únicas de Origem
            uf_list_origem_2 = sorted(df_ibge["UF"].unique())
            # Lista de UFs únicas de Destino
            uf_list_destino_2 = sorted(df_ibge["UF"].unique())
            
            novo_referencia_medicao = st.text_input("Referência Medição", registro["REFERENCIA_MEDICAO"])

            novo_incoterms = st.selectbox(
                "Incoterms",
                options=opcoes_incoterms,
                index=opcoes_incoterms.index(registro["INCOTERMS"]) 
                    if registro["INCOTERMS"] in opcoes_incoterms else 0
            )
            
            if registro["TIPO"] == "FAIXA":
                #faixa_km_inicio
                novo_faixa_km_inicio = st.selectbox(
                    "Faixa Km Início",
                    options=opcoes_faixa_km_inicio,
                    index=opcoes_faixa_km_inicio.index(registro["FAIXA_KMINICIO"]) 
                        if registro["FAIXA_KMINICIO"] in opcoes_faixa_km_inicio else 0
                )
                
                #faixa_km_fim
                novo_faixa_km_fim = st.selectbox(
                    "Faixa Km Fim",
                    options=opcoes_faixa_km_fim,
                    index=opcoes_faixa_km_fim.index(registro["FAIXA_KMFIM"]) 
                        if registro["FAIXA_KMFIM"] in opcoes_faixa_km_fim else 0
                )
                
            if registro["TIPO"] == "TABELA":
                #uf origem
                novo_uf_origem = st.selectbox(
                    "UF Origem",
                    options=uf_list_origem_2,
                    index=uf_list_origem_2.index(registro["UF_ORIGEM"]) 
                        if registro["UF_ORIGEM"] in uf_list_origem_2 else 0
                )
                
                # Filtra as cidades correspondentes à UF selecionada
                cidades_filtradas_origem_2 = (df_ibge.loc[df_ibge["UF"] == novo_uf_origem, "CIDADE"].sort_values().tolist())
                #cidades_filtradas_origem = (df_ibge.loc[df_ibge["UF"] == filtro_uforigem, "CIDADE"].sort_values().tolist())
                
                # Adiciona o valor "NULO" no início
                cidades_opcoes_origem_2 = ["NAO SE APLICA"] + cidades_filtradas_origem_2
                
                #cidade origem
                novo_cidade_origem = st.selectbox(
                    "Cidade Origem",
                    options=cidades_opcoes_origem_2,
                    index=cidades_opcoes_origem_2.index(registro["CIDADE_ORIGEM"]) 
                        if registro["CIDADE_ORIGEM"] in cidades_opcoes_origem_2 else 0
                )
                
                ######################################################################
                
                #uf destino
                novo_uf_destino = st.selectbox(
                    "UF Destino",
                    options=uf_list_destino_2,
                    index=uf_list_destino_2.index(registro["UF_DESTINO"]) 
                        if registro["UF_DESTINO"] in uf_list_destino_2 else 0
                )
                
                # Filtra as cidades correspondentes à UF selecionada
                cidades_filtradas_destino_2 = (df_ibge.loc[df_ibge["UF"] == novo_uf_destino, "CIDADE"].sort_values().tolist())
                
                # Adiciona o valor "NULO" no início
                cidades_opcoes_destino_2 = ["NAO SE APLICA"] + cidades_filtradas_destino_2
                
                #cidade destino
                novo_cidade_destino = st.selectbox(
                    "Cidade Destino",
                    options=cidades_opcoes_destino_2,
                    index=cidades_opcoes_destino_2.index(registro["CIDADE_DESTINO"]) 
                        if registro["CIDADE_DESTINO"] in cidades_opcoes_destino_2 else 0
                )

            novo_inicio = st.date_input(
                "Vigência Início",
                value=(pd.to_datetime(registro["VIGENCIA_INICIO"]).date()
                    if pd.notna(registro["VIGENCIA_INICIO"])
                    else None)
            )
            
            novo_tipo = registro["TIPO"]  # manter o tipo original

            if registro["TIPO"] == "FAIXA":
                if st.button("Salvar Alterações"):
                    existe = verificar_existencia_faixa(
                        novo_referencia_medicao, 
                        novo_incoterms,
                        novo_faixa_km_inicio,
                        novo_faixa_km_fim,
                        novo_inicio,
                        novo_tipo
                    )

                    if existe:                    
                        st.error("❌ Este cadastro já existe.")
                    else:
                        #st.info("🔄 Atualizando registro...")
                        atualizar_registro_faixa(id_registro, novo_referencia_medicao, novo_faixa_km_inicio, novo_faixa_km_fim, novo_incoterms, novo_inicio, novo_tipo)
                        st.session_state.pagina = "Editado"  # vai pra página oculta
                        st.rerun()
                        st.stop() 
                        
            elif registro["TIPO"] == "KM":
                if st.button("Salvar Alterações"):
                    existe = verificar_existencia_km(
                        novo_referencia_medicao, 
                        novo_incoterms,
                        novo_inicio,
                        novo_tipo
                    )

                    if existe:                    
                        st.error("❌ Este cadastro já existe.")
                    else:
                        #st.info("🔄 Atualizando registro...")
                        atualizar_registro_km(id_registro, novo_referencia_medicao, novo_incoterms, novo_inicio, novo_tipo)
                        st.session_state.pagina = "Editado"  # vai pra página oculta
                        st.rerun()
                        st.stop() 
                        
            elif registro["TIPO"] == "TABELA":
                if st.button("Salvar Alterações"):
                    existe = verificar_existencia_tabela(
                        novo_referencia_medicao,
                        novo_incoterms,
                        novo_uf_origem,
                        novo_cidade_origem,
                        novo_uf_destino,
                        novo_cidade_destino,
                        novo_inicio,
                        novo_tipo
                    )

                    if existe:                    
                        st.error("❌ Este cadastro já existe.")
                    else:
                        #st.info("🔄 Atualizando registro...")
                        atualizar_registro_tabela(id_registro,
                                              novo_referencia_medicao,
                                              novo_uf_origem,
                                              novo_cidade_origem,
                                              novo_uf_destino,
                                              novo_cidade_destino,                                              
                                              novo_incoterms,
                                              novo_inicio,
                                              novo_tipo)
                        st.session_state.pagina = "Editado"  # vai pra página oculta
                        st.rerun()
                        st.stop() 
                    
        # Inicializar flag
        if "confirmar_exclusao" not in st.session_state:
            st.session_state.confirmar_exclusao = False
        if "registro_pendente_exclusao" not in st.session_state:
            st.session_state.registro_pendente_exclusao = None

        with st.expander("🗑️ Excluir Registro"):

            # Primeiro botão: pedir confirmação
            if st.button("Excluir", type="primary"):
                st.session_state.confirmar_exclusao = True
                st.session_state.registro_pendente_exclusao = id_registro
                st.rerun()

            # Se clicou em "Excluir", aparece a confirmação
            if st.session_state.confirmar_exclusao:

                st.warning("⚠️ Tem certeza de que deseja excluir este registro?")

                col1, col2 = st.columns(2)

                # Botão "Sim"
                with col1:
                    if st.button("Sim, excluir", type="primary"):
                        excluir_registro(st.session_state.registro_pendente_exclusao)
                        st.session_state.confirmar_exclusao = False
                        st.session_state.registro_pendente_exclusao = None
                        st.session_state.pagina = "Excluido"
                        st.rerun()

                # Botão "Não"
                with col2:
                    if st.button("Cancelar"):
                        st.session_state.confirmar_exclusao = False
                        st.session_state.registro_pendente_exclusao = None
                        st.rerun()
    else:
        st.info("Nenhum registro encontrado.")

    # Criar espaço vazio nas laterais e centralizar os botões
    esp1, centro, esp2 = st.columns([1, 1, 1])

    with centro:
        if st.button("Voltar ao Menu", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()
            st.stop()   # ← ESSENCIAL NO LUGAR DO return            

# 🟢 Página oculta de sucesso (não aparece no menu)
elif st.session_state.pagina == "Sucesso":

    # Força a página a subir para o topo
    st.markdown("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="foguete">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: white;'>🎈 Cadastro efetuado!</h3>", unsafe_allow_html=True)

    fox_image_html = f"""
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    ">
        <img src="{fox_image}" alt="Foxy" 
            style="
                width: min(400px, 80vw);
                height: auto;
                margin-bottom: 10px;
            ">
    </div>
    """
    
    st.markdown(fox_image_html, unsafe_allow_html=True)
    st.success("✅ Registro atualizado com sucesso!")
    st.balloons()
    
    # Criar espaço vazio nas laterais e centralizar os botões
    esp1, centro, esp2 = st.columns([1, 1, 1])

    with centro:
        if st.button("Ok", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()
            st.stop()   # ← ESSENCIAL NO LUGAR DO return     

# 🟢 Página oculta de editado (não aparece no menu)
elif st.session_state.pagina == "Editado":

    # Força a página a subir para o topo
    st.markdown("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="foguete">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: white;'>🎈 Dado editado!</h3>", unsafe_allow_html=True)

    fox_image_html = f"""
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    ">
        <img src="{fox_image}" alt="Foxy" 
            style="
                width: min(400px, 80vw);
                height: auto;
                margin-bottom: 10px;
            ">
    </div>
    """

    st.markdown(fox_image_html, unsafe_allow_html=True)

    st.success("✅ Registro atualizado com sucesso!")
    st.balloons()

    # Criar espaço vazio nas laterais e centralizar os botões
    esp1, centro, esp2 = st.columns([1, 1, 1])

    with centro:
        if st.button("Ok", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()
            st.stop()   # ← ESSENCIAL NO LUGAR DO return   
    
# 🟢 Página oculta de editado (não aparece no menu)
elif st.session_state.pagina == "Excluido":

    # Força a página a subir para o topo
    st.markdown("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)

    st.markdown('<div class="foguete">', unsafe_allow_html=True)
    st.markdown("<h3 style='color: white;'>🎈 Dado excluído!</h3>", unsafe_allow_html=True)

    fox_image_html = f"""
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    ">
        <img src="{fox_image}" alt="Foxy" 
            style="
                width: min(400px, 80vw);
                height: auto;
                margin-bottom: 10px;
            ">
    </div>
    """

    st.markdown(fox_image_html, unsafe_allow_html=True)

    st.success("✅ Registro excluído com sucesso!")
    st.balloons()

    # Criar espaço vazio nas laterais e centralizar os botões
    esp1, centro, esp2 = st.columns([1, 1, 1])

    with centro:
        if st.button("Ok", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()
            st.stop()   # ← ESSENCIAL NO LUGAR DO return   
