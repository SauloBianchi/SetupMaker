"""
FPSEstimatorService
Estima FPS em jogos populares com base no score de desempenho
da CPU e GPU da build, usando tabelas de referência realistas.

Metodologia:
  fps_base × (cpu_score/100)^0.3 × (gpu_score/100)^0.7

Os valores base representam FPS em hardware de referência (score 75/100)
em 1080p Ultra para cada jogo.
"""

# FPS base calibrados para score 75/100 em 1080p Ultra
# Referências reais: RTX 4070 / Ryzen 5 7600X (~score 75)
JOGOS = {
    "Valorant":  {"base": 220, "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Valorant_logo_-_pink_color_version.svg/3840px-Valorant_logo_-_pink_color_version.svg.png",          "resolucao": "1080p Ultra"},
    "CS2":       {"base": 140, "icon": "https://1000logos.net/wp-content/uploads/2025/10/Counter-Strike-2-CS2-%E2%80%93-A-Modern-Evolution-2023%E2%80%93Present.png",                               "resolucao": "1080p Ultra"},
    "GTA V":     {"base":  90, "icon": "https://www.freepnglogos.com/uploads/gta-5-logo-png/grand-theft-auto-gold-7.png",         "resolucao": "1080p Ultra"},
    "Fortnite":  {"base": 110, "icon": "https://pngimg.com/uploads/fortnite/fortnite_PNG115.png", "resolucao": "1080p Ultra"},
    "Cyberpunk": {"base":  55, "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/Cyberpunk_2077_logo.svg/960px-Cyberpunk_2077_logo.svg.png",                                                   "resolucao": "1080p Ultra"},
    "Minecraft": {"base": 180, "icon": "https://logosmarcas.net/wp-content/uploads/2020/04/Minecraft-Logo.png", "resolucao": "1080p Ultra"},
}

# Score de referência usado para calibrar os valores base
_REF_SCORE = 0.75


def estimar(build) -> list[dict]:
    """
    Retorna lista de dicts com FPS estimado por jogo.
    Se CPU ou GPU não tiver score, usa 50 como padrão.
    """
    cpu_score = (build.cpu.desempenho if build.cpu and build.cpu.desempenho else 50) / 100
    gpu_score = (build.gpu.desempenho if build.gpu and build.gpu.desempenho else 50) / 100

    resultado = []
    for nome, info in JOGOS.items():
        # Normaliza em relação ao score de referência para que base = fps real do ref
        fator_cpu = (cpu_score / _REF_SCORE) ** 0.3
        fator_gpu = (gpu_score / _REF_SCORE) ** 0.7
        fps = int(info["base"] * fator_cpu * fator_gpu)
        fps = max(fps, 1)

        if fps >= 144:
            rating = "Excelente"
            cor    = "#10b981"
        elif fps >= 60:
            rating = "Bom"
            cor    = "#3b82f6"
        elif fps >= 30:
            rating = "Jogável"
            cor    = "#f59e0b"
        else:
            rating = "Ruim"
            cor    = "#ef4444"

        resultado.append({
            "jogo":      nome,
            "icon":      info["icon"],
            "fps":       fps,
            "rating":    rating,
            "cor":       cor,
            "resolucao": info["resolucao"],
        })

    return resultado


def consumo_mensal_kwh(build, horas_por_dia: int = 4) -> dict:
    """
    Calcula consumo energético mensal estimado.
    Considera apenas peças que efetivamente consomem energia:
    CPU, GPU, RAM, placa-mãe (~30W fixo), storage e cooler.
    A fonte não é somada (ela fornece energia), nem o gabinete.
    """
    pecas_consumo = [build.cpu, build.gpu, build.ram, build.storage, build.cooler]
    watts = sum(p.consumo_watts for p in pecas_consumo if p and p.consumo_watts)

    # Placa-mãe: usa o valor cadastrado ou 30W como fallback realista
    if build.motherboard and build.motherboard.consumo_watts:
        watts += build.motherboard.consumo_watts
    else:
        watts += 30

    kwh_dia  = (watts / 1000) * horas_por_dia
    kwh_mes  = kwh_dia * 30
    # Tarifa média BR ~R$0,75/kWh
    custo_mes = kwh_mes * 0.75

    if watts < 250:
        nivel = "Econômico"
        cor   = "#10b981"
    elif watts < 450:
        nivel = "Moderado"
        cor   = "#f59e0b"
    else:
        nivel = "Alto"
        cor   = "#ef4444"

    return {
        "watts":     watts,
        "kwh_mes":   round(kwh_mes, 1),
        "custo_mes": round(custo_mes, 2),
        "nivel":     nivel,
        "cor":       cor,
        "horas_dia": horas_por_dia,
    }