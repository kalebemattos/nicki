import csv
import json
import os
from collections import defaultdict

PASTA_VOTACAO = "dados_brutos/votacao"
PASTA_CANDIDATOS = "dados_brutos/candidatos"
PASTA_SAIDA = "dados_processados"
CSV_BAIRROS = "bairros.csv"

ANOS = ["2010", "2014", "2018", "2022"]


def normalizar(txt):
    if not txt:
        return ""
    return txt.strip().upper()


# ===============================
# CARREGAR MAPA DE BAIRROS
# ===============================

def carregar_bairros():
    mapa = {}

    with open(CSV_BAIRROS, encoding="latin1") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            try:
                chave = (
                    int(row["Zona Eleitoral"]),
                    int(row["Número do Local"]),
                    int(row["Seção"])
                )
                mapa[chave] = normalizar(row["Bairro"])
            except:
                continue

    print(f"✔ {len(mapa)} seções com bairro")
    return mapa


# ===============================
# CARREGAR CANDIDATOS (2010/2014)
# ===============================

def carregar_candidatos(ano):

    caminho = f"{PASTA_CANDIDATOS}/consulta_cand_{ano}_RJ.csv"

    if not os.path.exists(caminho):
        return {}

    mapa = {}

    with open(caminho, encoding="latin1") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            try:
                cargo = normalizar(row["DS_CARGO"])
                numero = row["NR_CANDIDATO"]
                sq = row["SQ_CANDIDATO"]

                chave = (cargo, numero)
                mapa[chave] = sq

            except:
                continue

    print(f"✔ {len(mapa)} candidatos carregados ({ano})")
    return mapa


# ===============================
# PROCESSAR ANO
# ===============================

def processar_ano(ano, mapa_bairros):

    print(f"\n📊 Processando {ano}...")

    caminho_votacao = f"{PASTA_VOTACAO}/{ano}.csv"
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    mapa_candidatos = {}
    if ano in ["2010", "2014"]:
        mapa_candidatos = carregar_candidatos(ano)

    resumo = defaultdict(lambda: {
        "TOTAL_RJ": 0,
        "CIDADES": defaultdict(lambda: {
            "total_validos": 0,
            "candidatos": [],
            "BAIRROS": defaultdict(lambda: {
                "total_validos": 0,
                "candidatos": []
            })
        })
    })

    with open(caminho_votacao, encoding="latin1") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:

            try:
                zona = int(row["NR_ZONA"])
                secao = int(row["NR_SECAO"])
                local = int(row["NR_LOCAL_VOTACAO"])

                cargo = normalizar(row["DS_CARGO"])
                cidade = normalizar(row["NM_MUNICIPIO"])
                nome = normalizar(row["NM_VOTAVEL"])
                numero = row["NR_VOTAVEL"]
                votos = int(row["QT_VOTOS"])

                chave_bairro = (zona, local, secao)
                bairro = mapa_bairros.get(chave_bairro)

                # SQ candidato
                sq = None
                if "SQ_CANDIDATO" in row:
                    sq = row["SQ_CANDIDATO"]
                else:
                    sq = mapa_candidatos.get((cargo, numero))

                # TOTAL ESTADO
                resumo[cargo]["TOTAL_RJ"] += votos

                # CIDADE
                cidade_obj = resumo[cargo]["CIDADES"][cidade]
                cidade_obj["total_validos"] += votos

                # inserir candidato cidade
                inserir_candidato(cidade_obj["candidatos"], nome, numero, votos, sq)

                # BAIRRO
                if bairro:
                    bairro_obj = cidade_obj["BAIRROS"][bairro]
                    bairro_obj["total_validos"] += votos
                    inserir_candidato(bairro_obj["candidatos"], nome, numero, votos, sq)

            except:
                continue

    ordenar_posicoes(resumo)

    salvar_json(ano, resumo)
    print(f"✅ {ano} finalizado.")


# ===============================
# INSERIR OU SOMAR CANDIDATO
# ===============================

def inserir_candidato(lista, nome, numero, votos, sq):

    for c in lista:
        if c["nome"] == nome:
            c["votos"] += votos
            return

    lista.append({
        "nome": nome,
        "numero": numero,
        "votos": votos,
        "sq_candidato": sq,
        "posicao": 0
    })


# ===============================
# ORDENAR E POSIÇÃO
# ===============================

def ordenar_posicoes(resumo):

    for cargo in resumo.values():

        for cidade in cargo["CIDADES"].values():

            cidade["candidatos"].sort(key=lambda x: x["votos"], reverse=True)

            for i, c in enumerate(cidade["candidatos"], start=1):
                c["posicao"] = i

            for bairro in cidade["BAIRROS"].values():
                bairro["candidatos"].sort(key=lambda x: x["votos"], reverse=True)

                for i, c in enumerate(bairro["candidatos"], start=1):
                    c["posicao"] = i


# ===============================
# SALVAR JSON
# ===============================

def salvar_json(ano, resumo):

    caminho_resumo = f"{PASTA_SAIDA}/{ano}/resumo.json"
    os.makedirs(f"{PASTA_SAIDA}/{ano}", exist_ok=True)

    with open(caminho_resumo, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)

    caminho_bairro = f"{PASTA_SAIDA}/resumo_bairro_{ano}.json"

    with open(caminho_bairro, "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)


# ===============================
# MAIN
# ===============================

def main():

    print("🔎 Carregando bairros...")
    mapa_bairros = carregar_bairros()

    for ano in ANOS:
        processar_ano(ano, mapa_bairros)

    print("\n🎯 PROCESSAMENTO FINALIZADO")


if __name__ == "__main__":
    main()
