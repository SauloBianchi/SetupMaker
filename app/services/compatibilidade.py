"""
CompatibilidadeService
======================
Verifica compatibilidade entre componentes com base nos dados
reais importados da API (socket, tipo RAM, wattage).

Regras implementadas:
  1. CPU ↔ Placa-Mãe: socket deve ser idêntico
  2. RAM ↔ Placa-Mãe: geração DDR deve coincidir
  3. Fonte ↔ Consumo:  wattage da fonte ≥ consumo total + 20% de margem
"""

# Mapeamento de sockets compatíveis entre si (casos especiais)
SOCKETS_COMPAT = {
    # Nenhum: cada socket é exclusivo — manter vazio
}


def verificar(build) -> list[str]:
    erros = []
    cpu = build.cpu
    mb  = build.motherboard
    ram = build.ram
    gpu = build.gpu
    psu = build.fonte

    # 1 ── Socket CPU ↔ Placa-Mãe ───────────────────────────────
    if cpu and mb:
        s_cpu = (cpu.socket or "").strip()
        s_mb  = (mb.socket  or "").strip()
        if s_cpu and s_mb and s_cpu != s_mb:
            erros.append(
                f"❌ Socket incompatível: CPU usa <strong>{s_cpu}</strong>, "
                f"mas a placa-mãe suporta <strong>{s_mb}</strong>. "
                f"Selecione uma placa-mãe {s_cpu} ou uma CPU {s_mb}."
            )

    # 2 ── Geração de RAM ↔ Placa-Mãe ───────────────────────────
    if ram and mb:
        r_ram = (ram.tipo_ram or "").strip().upper()
        r_mb  = (mb.tipo_ram  or "").strip().upper()
        if r_ram and r_mb and r_ram != r_mb:
            erros.append(
                f"❌ RAM incompatível: módulo é <strong>{r_ram}</strong>, "
                f"mas a placa-mãe suporta apenas <strong>{r_mb}</strong>."
            )

    # 3 ── Potência da Fonte ──────────────────────────────────────
    if psu:
        consumo = _consumo_sem_fonte(build)
        # Usa consumo_watts da fonte como wattage
        wattage = psu.consumo_watts or 0
        margem  = int(consumo * 1.2)
        if wattage and wattage < consumo:
            erros.append(
                f"⚠️ Fonte insuficiente: os componentes consomem ~<strong>{consumo}W</strong>, "
                f"mas a fonte tem apenas <strong>{wattage}W</strong>. "
                f"Recomendamos ao menos <strong>{margem}W</strong>."
            )

    return erros


def _consumo_sem_fonte(build) -> int:
    """Soma TDP de todos os componentes exceto a própria fonte."""
    pecas = [build.cpu, build.gpu, build.ram,
             build.motherboard, build.storage, build.gabinete]
    return sum((p.consumo_watts or 0) for p in pecas if p)


def status(erros: list[str]) -> dict:
    if not erros:
        return {"ok": True,  "label": "Compatível",   "color": "#10b981", "icon": "bi bi-check-circle-fill"}
    return     {"ok": False, "label": "Incompatível", "color": "#ef4444", "icon": "bi bi-x-circle-fill"}