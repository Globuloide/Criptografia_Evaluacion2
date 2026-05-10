# 🔬 Simulación de Ataque de Intercepción — BB84 (QKD)

> Ejercicio de seguridad criptográfica cuántica: ataque Intercept-Resend sobre el protocolo de Distribución Cuántica de Claves BB84, con análisis de QBER y fallas de implementación.

---

## 📋 Descripción

Este proyecto simula el ataque más fundamental contra BB84: el **Intercept-Resend**, donde Eve intercepta los qubits en tránsito, los mide con una base aleatoria y reenvía nuevos qubits a Bob, introduciendo errores detectables en la clave.

| Simulación | Objetivo |
|---|---|
| **Ataque 1** | Intercept-Resend total (Eve = 100%) → QBER ≈ 25% |
| **Ataque 2** | Intercept-Resend parcial (tasa 10%–100%) → relación QBER vs. detección |
| **VULN-01** | Sistema sin verificación de QBER → clave comprometida aceptada |
| **VULN-02** | Muestra de verificación insuficiente → Eve evade detección en 25% de casos |

---

## 📁 Estructura del proyecto

```
proyecto/
├── ataque_bb84.py                # Script principal de simulación
├── respuesta_ataque_bb84.md      # Respuesta teórica completa (a/b/c/d)
├── simulacion_bb84.log           # Log generado automáticamente al ejecutar
└── README.md                     # Este archivo
```

---

## ⚙️ Requisitos

- Python 3.11 o superior
- **Sin dependencias externas** — usa solo la librería estándar de Python

---

## 🚀 Instalación y ejecución

### 1. Clonar o descargar el repositorio

```bash
git clone https://github.com/Globuloide/Criptografia_Evaluacion2
cd proyecto-bb84
```

### 2. Ejecutar directamente (sin instalación)

```bash
python ataque_bb84.py
```

El script imprime los resultados en consola y genera `simulacion_bb84.log`.

---

## 🧪 ¿Cómo funciona BB84?

### Protocolo base

```
Alice                          Canal cuántico                        Bob
──────                         ──────────────                        ───
Genera bit aleatorio (0/1)  →  Envía qubit polarizado           →  Mide con base aleatoria
Elige base aleatoria (+/x)                                          Elige base aleatoria (+/x)
                                   ↕ (Eve puede interceptar)
                           Canal clásico (público)
Alice y Bob anuncian bases usadas (no los bits)
Conservan solo los bits donde sus bases coincidieron → clave sifted
Comparan muestra de bits sifted → calculan QBER
Si QBER > 11% → abortar (canal comprometido)
```

### Modelo de qubit implementado

| Base | Bit 0 | Bit 1 |
|---|---|---|
| `+` (rectilínea) | \|↑⟩ | \|→⟩ |
| `x` (diagonal) | \|↗⟩ | \|↘⟩ |

Medir con base incorrecta → resultado aleatorio 50/50 (principio de observación cuántica).

---

## 🎯 Resultados de la simulación

### Ataque 1 — Intercepción total

```
QBER promedio CON Eve: 0.2443  (σ=0.0183) — teórico: 0.2500
QBER promedio SIN Eve: 0.0000             — teórico: 0.0000
Eve detectable:        20/20 simulaciones (100%)
```

La predicción teórica `P(error) = 0.5 × 0.5 = 0.25` se confirma con error < 1%.

### Ataque 2 — Intercepción parcial

```
Tasa Eve |  QBER obs.  | Estado
   10%   |   0.0264    | ✓ sin detección
   20%   |   0.0488    | ✓ sin detección
   30%   |   0.0702    | ✓ sin detección
   40%   |   0.0971    | ✓ sin detección  ← límite práctico
   50%   |   0.1272    | ⚠ DETECTABLE
  100%   |   0.2491    | ⚠ DETECTABLE
```

> **Conclusión:** Eve puede interceptar hasta ~44% del canal sin activar la alarma de QBER.

---

## 🐛 Vulnerabilidades identificadas

| ID | Tipo | Descripción | Severidad |
|---|---|---|---|
| VULN-01 | Falla de implementación | Sistema no verifica QBER ni aborta — clave comprometida entregada | Crítica |
| VULN-02 | Falla de implementación | Muestra de 10 bits insuficiente — Eve evade en 25% de casos | Alta |
| VULN-03 | Limitación de protocolo | BB84 base no detecta intercepción < 44% ni incluye Privacy Amplification | Media |

### Distinción clave

```
Falla de IMPLEMENTACIÓN → corregible en código sin cambiar el protocolo
Limitación de PROTOCOLO → requiere extensión: Error Correction + Privacy Amplification
```

---

## ✅ Correcciones recomendadas

### VULN-01 — Agregar verificación de QBER

```python
# ❌ Sistema vulnerable (sin verificación)
clave = resultado.clave_alice   # acepta cualquier QBER

# ✅ Sistema correcto
UMBRAL_QBER = 0.11
if resultado.qber > UMBRAL_QBER:
    raise SecurityError("Canal comprometido — QBER supera umbral. Abortar.")
clave = resultado.clave_alice
```

### VULN-02 — Tamaño de muestra adecuado

```python
# ❌ Muestra insuficiente
muestra = clave_sifted[:10]

# ✅ Al menos 20-30% de los bits sifted
n_muestra = max(50, len(clave_sifted) // 4)
muestra = clave_sifted[:n_muestra]
```

---

## 📊 Output esperado

```
INICIO DE SIMULACIÓN — ATAQUE SOBRE BB84
ATAQUE 1: Intercept-Resend Total (Eve intercepta 100%)
  [01] CON Eve: QBER=0.2576 | SIN Eve: QBER=0.0000 | Clave sifted: 528 bits
  ...
  QBER promedio CON Eve: 0.2443 (σ=0.0183) — esperado teórico: 0.2500
  Eve detectable en 20/20 simulaciones (100%)

ATAQUE 2: Intercept-Resend Parcial (tasa variable)
  Tasa Eve |  QBER obs. | Estado
    50%    |    0.1272  | ⚠ DETECTABLE

VULN-01: Sistema BB84 sin verificación de QBER
  QBER real: 0.2274 — sistema NO verifica ni aborta
  Clave de 277 bits entregada con 63 errores no detectados

VULN-02: Muestra de verificación insuficiente (10 bits)
  Eve pasó desapercibida en 25/100 casos (25%)
```

---

## ⚠️ Limitaciones de la simulación

| Limitación | Aspecto no capturado |
|---|---|
| Ruido cuántico de canal | QBER de fondo real (1-5%) sin Eve, que se confunde con intercepción |
| Pérdida de fotones | Eficiencia de detectores, dark counts, ataque PNS (Photon Number Splitting) |
| Ataques coherentes | Eve con memoria cuántica puede atacar tras escuchar bases públicas |
| Privacy Amplification | En QKD real, post-procesamiento reduce drásticamente la info de Eve |

---

## 📚 Referencias

- Bennett, C. H. & Brassard, G. (1984). *Quantum cryptography: Public key distribution and coin tossing*
- Gisin, N. et al. (2002). *Quantum cryptography*. Reviews of Modern Physics, 74(1)
- NIST IR 8413 — Status Report on the Third Round of the NIST Post-Quantum Cryptography Standardization Process
- Scarani, V. et al. (2009). *The security of practical quantum key distribution*

---

## 👤 Autor Pablo Salazar Juarez

Ejercicio desarrollado para la asignatura de Criptografía Aplicada / Seguridad de Sistemas.  
Uso estrictamente educativo — simulación controlada en entorno local.  
La simulación no requiere hardware cuántico; modela el comportamiento estadístico del protocolo.
