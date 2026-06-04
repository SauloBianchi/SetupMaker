"""
Gera URLs de busca direta para cada loja com o nome do produto.
Usa favicons oficiais de cada loja para os ícones.
"""
from urllib.parse import quote_plus


def gerar_urls_busca(nome_produto: str) -> dict:
    q = quote_plus(nome_produto)
    return {
        "Pichau":        f"https://www.pichau.com.br/search?q={q}",
        "KaBuM!":        f"https://www.kabum.com.br/busca/{q}",
        "TerabyteShop":  f"https://www.terabyteshop.com.br/busca?str={q}",
        "Amazon BR":     f"https://www.amazon.com.br/s?k={q}&i=computers",
        "Mercado Livre": f"https://lista.mercadolivre.com.br/{q}",
        "AliExpress":    f"https://www.aliexpress.com/wholesale?SearchText={q}",
    }


# Favicons oficiais de cada loja
LOJAS_CONFIG = {
    "Pichau": {
        "favicon": "https://www.pichau.com.br/favicon.ico",
        "cor":      "#ff6b00",
        "cor_bg":   "rgba(255,107,0,0.08)",
        "cor_borda":"rgba(255,107,0,0.25)",
    },
    "KaBuM!": {
        "favicon": "https://www.kabum.com.br/favicon.ico",
        "cor":      "#ff4500",
        "cor_bg":   "rgba(255,69,0,0.08)",
        "cor_borda":"rgba(255,69,0,0.25)",
    },
    "TerabyteShop": {
        "favicon": "https://www.terabyteshop.com.br/favicon.ico",
        "cor":      "#00aaff",
        "cor_bg":   "rgba(0,170,255,0.08)",
        "cor_borda":"rgba(0,170,255,0.25)",
    },
    "Amazon BR": {
        "favicon": "https://www.amazon.com.br/favicon.ico",
        "cor":      "#ff9900",
        "cor_bg":   "rgba(255,153,0,0.08)",
        "cor_borda":"rgba(255,153,0,0.25)",
    },
    "Mercado Livre": {
        "favicon": "https://http2.mlstatic.com/frontend-assets/ml-web-navigation/ui-navigation/6.6.92/mercadolibre/favicon.svg",
        "cor":      "#ffe600",
        "cor_bg":   "rgba(255,230,0,0.08)",
        "cor_borda":"rgba(255,230,0,0.25)",
    },
    "AliExpress": {
        "favicon": "https://ae01.alicdn.com/images/eng/wholesale/icon/aliexpress.ico",
        "cor":      "#e43226",
        "cor_bg":   "rgba(228,50,38,0.08)",
        "cor_borda":"rgba(228,50,38,0.25)",
    },
}


def config_loja(nome: str) -> dict:
    for chave, cfg in LOJAS_CONFIG.items():
        if chave.lower() in nome.lower():
            return cfg
    return {
        "favicon":   None,
        "cor":       "#64748b",
        "cor_bg":    "rgba(100,116,139,0.08)",
        "cor_borda": "rgba(100,116,139,0.25)",
    }