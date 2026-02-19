import json
import os

ANO = "2022"  # MUDE para 2010, 2014, 2022 depois

entrada = f"dados_processados/{ANO}/resumo.json"
saida_base = f"dados_processados/{ANO}/cidades"

os.makedirs(saida_base, exist_ok=True)

with open(entrada, "r", encoding="utf-8") as f:
    dados = json.load(f)

for cargo, info in dados.items():
    cidades = info.get("CIDADES", {})

    for cidade, dados_cidade in cidades.items():
        nome_arquivo = cidade.replace(" ", "_").replace("'", "").upper()
        caminho_saida = os.path.join(saida_base, f"{nome_arquivo}.json")

        estrutura = {
            cargo: {
                "TOTAL_RJ": info.get("TOTAL_RJ"),
                "CIDADES": {
                    cidade: dados_cidade
                }
            }
        }

        with open(caminho_saida, "w", encoding="utf-8") as out:
            json.dump(estrutura, out, ensure_ascii=False)

print("Divisão concluída.")
