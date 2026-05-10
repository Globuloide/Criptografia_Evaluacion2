"""
=============================================================
SIMULACIÓN DE ATAQUE DE INTERCEPCIÓN (INTERCEPT-RESEND)
SOBRE PROTOCOLO BB84 — DISTRIBUCIÓN CUÁNTICA DE CLAVES
Asignatura: Criptografía Aplicada / Seguridad de Sistemas
=============================================================
Ataques implementados:
  1. Intercept-Resend Attack (Eve intercepts 100% of qubits)
     → Induce QBER ~25%, detectable por Alice y Bob
  2. Intercept-Resend Parcial (Eve intercepts X% of qubits)
     → Analiza relación entre tasa de intercepción y QBER

Fallas identificadas:
  - Implementación sin umbral de QBER → no aborta canal comprometido
  - Muestra de verificación insuficiente → Eve pasa desapercibida

Dependencias: solo librería estándar de Python (random, logging, statistics)
=============================================================
"""

import random
import logging
import statistics
from dataclasses import dataclass, field

# ──────────────────────────────────────────────────────────────
# LOGGING AUDITADO
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler("simulacion_bb84.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# MODELO BB84: QUBITS, BASES Y MEDICIÓN
# ──────────────────────────────────────────────────────────────

BASES = ["+", "x"]   # + = rectilínea, x = diagonal

@dataclass
class Qubit:
    """
    Representa un qubit polarizado según el protocolo BB84.
    base '+' → {0: |↑⟩, 1: |→⟩}
    base 'x' → {0: |↗⟩, 1: |↘⟩}
    """
    bit: int      # 0 o 1
    base: str     # '+' o 'x'

    def __repr__(self):
        simbolos = {(0, "+"): "|↑⟩", (1, "+"): "|→⟩",
                    (0, "x"): "|↗⟩", (1, "x"): "|↘⟩"}
        return simbolos.get((self.bit, self.base), "?")


def medir_qubit(qubit: Qubit, base_medicion: str) -> int:
    """
    Simula la medición cuántica de un qubit.
    - Misma base que la preparación → resultado determinista (sin error).
    - Base distinta → resultado aleatorio 50/50 (principio de observación cuántica).
    """
    if base_medicion == qubit.base:
        return qubit.bit
    return random.randint(0, 1)   # colapso aleatorio por incompatibilidad de base


# ──────────────────────────────────────────────────────────────
# PROTOCOLO BB84 COMPLETO
# ──────────────────────────────────────────────────────────────

@dataclass
class ResultadoBB84:
    bits_alice: list[int]         = field(default_factory=list)
    bases_alice: list[str]        = field(default_factory=list)
    bases_bob: list[str]          = field(default_factory=list)
    resultados_bob: list[int]     = field(default_factory=list)
    clave_alice: list[int]        = field(default_factory=list)   # post-sifting
    clave_bob: list[int]          = field(default_factory=list)
    errores: int                  = 0
    qber: float                   = 0.0      # Quantum Bit Error Rate
    eve_presente: bool            = False
    tasa_intercepcion_eve: float  = 0.0


def bb84(n_bits: int, eve_presente: bool = False,
         tasa_intercepcion: float = 1.0) -> ResultadoBB84:
    """
    Simula el protocolo BB84 entre Alice y Bob, con Eve opcional.

    Flujo:
      1. Alice genera bits y bases aleatorias → prepara qubits
      2. Eve (si presente) intercepta, mide con base aleatoria y reenvía
      3. Bob mide con base aleatoria
      4. Sifting: Alice y Bob conservan solo bits con bases coincidentes
      5. Verificación: comparan muestra → calculan QBER
    """
    # ── Paso 1: Alice prepara qubits ──────────────────────────
    bits_alice  = [random.randint(0, 1)          for _ in range(n_bits)]
    bases_alice = [random.choice(BASES)          for _ in range(n_bits)]
    qubits      = [Qubit(b, base) for b, base
                   in zip(bits_alice, bases_alice)]

    # ── Paso 2: Eve intercepta (intercept-resend) ─────────────
    if eve_presente:
        qubits_post_eve = []
        for qubit in qubits:
            if random.random() < tasa_intercepcion:
                # Eve mide con base aleatoria → perturba el qubit
                base_eve   = random.choice(BASES)
                bit_eve    = medir_qubit(qubit, base_eve)
                # Eve reenvía un qubit nuevo preparado con SU medición
                qubits_post_eve.append(Qubit(bit_eve, base_eve))
            else:
                qubits_post_eve.append(qubit)   # qubit sin tocar
        qubits = qubits_post_eve

    # ── Paso 3: Bob mide ──────────────────────────────────────
    bases_bob      = [random.choice(BASES) for _ in range(n_bits)]
    resultados_bob = [medir_qubit(q, b) for q, b in zip(qubits, bases_bob)]

    # ── Paso 4: Sifting (canal público) ───────────────────────
    clave_alice, clave_bob = [], []
    for i in range(n_bits):
        if bases_alice[i] == bases_bob[i]:
            clave_alice.append(bits_alice[i])
            clave_bob.append(resultados_bob[i])

    # ── Paso 5: Cálculo de QBER ──────────────────────────────
    errores = sum(a != b for a, b in zip(clave_alice, clave_bob))
    qber    = errores / len(clave_alice) if clave_alice else 0.0

    return ResultadoBB84(
        bits_alice=bits_alice,
        bases_alice=bases_alice,
        bases_bob=bases_bob,
        resultados_bob=resultados_bob,
        clave_alice=clave_alice,
        clave_bob=clave_bob,
        errores=errores,
        qber=qber,
        eve_presente=eve_presente,
        tasa_intercepcion_eve=tasa_intercepcion if eve_presente else 0.0
    )


# ══════════════════════════════════════════════════════════════
# ATAQUE 1: INTERCEPT-RESEND TOTAL (Eve = 100%)
# ══════════════════════════════════════════════════════════════

def ataque_intercept_resend_total(n_bits: int = 1000, repeticiones: int = 20) -> list[dict]:
    """
    Eve intercepta el 100% de los qubits.
    Teoría: QBER esperado ≈ 25%
      → Eve acierta la base 50% del tiempo
      → Cuando falla la base, introduce error con p=0.5
      → P(error) = 0.5 * 0.5 = 0.25

    Se ejecutan 'repeticiones' simulaciones para obtener estadísticas.
    """
    log.info("=" * 58)
    log.info("ATAQUE 1: Intercept-Resend Total (Eve intercepta 100%)")
    log.info("=" * 58)

    qbers_con_eve    = []
    qbers_sin_eve    = []
    hallazgos        = []

    for i in range(repeticiones):
        r_con = bb84(n_bits, eve_presente=True,  tasa_intercepcion=1.0)
        r_sin = bb84(n_bits, eve_presente=False)
        qbers_con_eve.append(r_con.qber)
        qbers_sin_eve.append(r_sin.qber)

        log.info(
            f"  [{i+1:02d}] CON Eve: QBER={r_con.qber:.4f} "
            f"| SIN Eve: QBER={r_sin.qber:.4f} "
            f"| Clave sifted: {len(r_con.clave_alice)} bits"
        )

    qber_promedio_con = statistics.mean(qbers_con_eve)
    qber_promedio_sin = statistics.mean(qbers_sin_eve)
    qber_stdev_con    = statistics.stdev(qbers_con_eve)

    log.info(f"\n  QBER promedio CON Eve: {qber_promedio_con:.4f} "
             f"(σ={qber_stdev_con:.4f}) — esperado teórico: 0.2500")
    log.info(f"  QBER promedio SIN Eve: {qber_promedio_sin:.4f} "
             f"— esperado teórico: 0.0000")

    # Detectar si el QBER supera el umbral de seguridad (11%)
    UMBRAL_QBER = 0.11
    for qber in qbers_con_eve:
        if qber > UMBRAL_QBER:
            hallazgos.append({
                "id": "DETECCIÓN",
                "evento": f"QBER={qber:.4f} supera umbral={UMBRAL_QBER} → canal comprometido"
            })

    detecciones = len(hallazgos)
    log.warning(
        f"  Eve detectable en {detecciones}/{repeticiones} simulaciones "
        f"({100*detecciones/repeticiones:.0f}%)"
    )

    return qbers_con_eve, qbers_sin_eve


# ══════════════════════════════════════════════════════════════
# ATAQUE 2: INTERCEPT-RESEND PARCIAL (variación de tasa)
# ══════════════════════════════════════════════════════════════

def ataque_intercept_parcial(n_bits: int = 2000) -> list[tuple]:
    """
    Eve varía su tasa de intercepción del 10% al 100%.
    Muestra la relación lineal entre tasa de intercepción y QBER inducido.

    Resultado clave: incluso al 30% de intercepción, QBER ≈ 7.5%,
    superando el umbral de seguridad de 11% a partir del ~44%.
    """
    log.info("\n" + "=" * 58)
    log.info("ATAQUE 2: Intercept-Resend Parcial (tasa variable)")
    log.info("=" * 58)

    tasas = [i / 10 for i in range(1, 11)]    # 0.1, 0.2, ..., 1.0
    resultados = []
    UMBRAL = 0.11

    log.info(f"  {'Tasa Eve':>10} | {'QBER obs.':>10} | {'QBER teórico':>13} | Estado")
    log.info("  " + "-" * 55)

    for tasa in tasas:
        # Promedio de 10 repeticiones por tasa
        qbers = [bb84(n_bits, eve_presente=True, tasa_intercepcion=tasa).qber
                 for _ in range(10)]
        qber_obs  = statistics.mean(qbers)
        qber_teo  = 0.25 * tasa          # fórmula teórica: P(error) = 0.25 * p_eve
        detectable = "⚠ DETECTABLE" if qber_obs > UMBRAL else "✓ sin detección"

        log.info(
            f"  {tasa:>10.0%} | {qber_obs:>10.4f} | {qber_teo:>13.4f} | {detectable}"
        )
        resultados.append((tasa, qber_obs, qber_teo))

    return resultados


# ══════════════════════════════════════════════════════════════
# SIMULACIÓN DE FALLA DE IMPLEMENTACIÓN: SIN VERIFICACIÓN QBER
# ══════════════════════════════════════════════════════════════

def sistema_sin_verificacion(n_bits: int = 500) -> dict:
    """
    Simula un sistema BB84 mal implementado que NO verifica el QBER.
    Eve puede comprometer el canal sin ser detectada por el sistema.
    Esta es VULN-01: falla de implementación, no del protocolo BB84.
    """
    log.info("\n" + "=" * 58)
    log.info("VULN-01: Sistema BB84 sin verificación de QBER")
    log.info("=" * 58)

    resultado = bb84(n_bits, eve_presente=True, tasa_intercepcion=1.0)

    # Sistema vulnerable: usa la clave aunque haya errores
    log.warning(
        f"  QBER real: {resultado.qber:.4f} — sistema NO verifica ni aborta"
    )
    log.warning(
        f"  Clave de {len(resultado.clave_alice)} bits entregada con "
        f"{resultado.errores} errores no detectados"
    )
    log.warning(
        "  Eve conoce ~50% de la clave sifted (los bits donde acertó la base)"
    )

    return {
        "id": "VULN-01",
        "tipo": "Falla de IMPLEMENTACIÓN",
        "descripcion": "El sistema acepta y usa la clave aunque el QBER supere el umbral seguro (11%).",
        "qber_observado": resultado.qber,
        "errores_no_detectados": resultado.errores,
        "impacto": "Eve obtiene información parcial de la clave sin que el sistema lo detecte.",
        "mitigacion": "Implementar verificación: si QBER > 0.11, abortar y reiniciar el protocolo."
    }


def sistema_sin_muestra_suficiente(n_bits: int = 200) -> dict:
    """
    Simula un sistema que usa muestra de verificación muy pequeña (10 bits).
    Con tan pocos bits, Eve puede pasar desapercibida por varianza estadística.
    Esta es VULN-02: falla de implementación por parámetro insuficiente.
    """
    log.info("\n" + "=" * 58)
    log.info("VULN-02: Muestra de verificación insuficiente (10 bits)")
    log.info("=" * 58)

    MUESTRA_INSUFICIENTE = 10
    no_detectados = 0
    intentos = 100

    for _ in range(intentos):
        resultado = bb84(n_bits, eve_presente=True, tasa_intercepcion=1.0)
        # Verificar solo 10 bits de la clave sifted
        muestra_alice = resultado.clave_alice[:MUESTRA_INSUFICIENTE]
        muestra_bob   = resultado.clave_bob[:MUESTRA_INSUFICIENTE]
        errores_muestra = sum(a != b for a, b in zip(muestra_alice, muestra_bob))
        qber_muestra = errores_muestra / MUESTRA_INSUFICIENTE
        # Sistema mal implementado: umbral aplicado a muestra insuficiente
        if qber_muestra <= 0.11:
            no_detectados += 1

    tasa_fallo = no_detectados / intentos
    log.warning(
        f"  Eve pasó desapercibida en {no_detectados}/{intentos} casos "
        f"({100*tasa_fallo:.0f}%) usando muestra de {MUESTRA_INSUFICIENTE} bits"
    )

    return {
        "id": "VULN-02",
        "tipo": "Falla de IMPLEMENTACIÓN",
        "descripcion": f"Muestra de verificación de solo {MUESTRA_INSUFICIENTE} bits: alta varianza estadística.",
        "tasa_falsos_negativos": tasa_fallo,
        "impacto": f"Eve evade detección en ~{100*tasa_fallo:.0f}% de los intentos.",
        "mitigacion": "Usar muestra de al menos el 20-30% de los bits sifted para garantizar significancia estadística."
    }


# ══════════════════════════════════════════════════════════════
# REPORTE FINAL DE VULNERABILIDADES
# ══════════════════════════════════════════════════════════════

def generar_reporte(vuln_01: dict, vuln_02: dict) -> None:
    log.info("\n" + "═" * 58)
    log.info("REPORTE FINAL DE VULNERABILIDADES")
    log.info("═" * 58)

    vulnerabilidades = [
        vuln_01,
        vuln_02,
        {
            "id": "VULN-03",
            "tipo": "Limitación de PROTOCOLO (no de implementación)",
            "descripcion": (
                "BB84 no detecta a Eve si su tasa de intercepción es baja "
                f"(< ~44% → QBER < 0.11). El protocolo base no incluye "
                "amplificación de privacidad ni corrección de errores."
            ),
            "impacto": "Eve puede extraer información parcial sin ser detectada con interceptación baja.",
            "mitigacion": "Incorporar Privacy Amplification y Error Correction (ej: reconciliación de Cascade)."
        }
    ]

    for v in vulnerabilidades:
        log.info(f"\n[{v['id']}] {v['tipo']}")
        log.info(f"  Descripción : {v['descripcion']}")
        log.info(f"  Impacto     : {v['impacto']}")
        log.info(f"  Mitigación  : {v['mitigacion']}")

    log.info("\n[DISTINCIÓN CLAVE]")
    log.info("  Falla de PROTOCOLO  → intrínseca al diseño de BB84, requiere extensión del protocolo")
    log.info("  Falla de IMPLEMENTACIÓN → decisión incorrecta del desarrollador, corregible en código")


# ══════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════

def main():
    random.seed(42)   # Reproducibilidad de la simulación
    log.info("INICIO DE SIMULACIÓN — ATAQUE SOBRE BB84")
    log.info("Sistema objetivo: Distribución Cuántica de Claves (QKD)\n")

    # Ataque 1: intercepción total
    qbers_con, qbers_sin = ataque_intercept_resend_total(n_bits=1000, repeticiones=20)

    # Ataque 2: intercepción parcial variable
    resultados_parcial = ataque_intercept_parcial(n_bits=2000)

    # Fallas de implementación
    v01 = sistema_sin_verificacion(n_bits=500)
    v02 = sistema_sin_muestra_suficiente(n_bits=200)

    # Reporte final
    generar_reporte(v01, v02)

    log.info("\nSimulación finalizada. Log completo en: simulacion_bb84.log")


if __name__ == "__main__":
    main()
