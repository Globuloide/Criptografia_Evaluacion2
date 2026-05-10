# Simulación de Ataque de Intercepción sobre BB84 (QKD)

---

## (a) Tipo de ataque y justificación técnica

### Sistema objetivo elegido: BB84 — Distribución Cuántica de Claves

Se eligió BB84 como sistema objetivo porque permite demostrar un ataque cualitativamente distinto al de AES: en lugar de atacar la matemática del cifrado, el atacante explota la mecánica cuántica de la transmisión. Esto hace visible el rol del **principio de observación cuántica** como mecanismo de detección.

### Ataque implementado: Intercept-Resend

Eve intercepta los qubits enviados por Alice, los mide con una base aleatoria y reenvía a Bob un nuevo qubit preparado con su propio resultado. La pertinencia del ataque es doble:

**Fundamento teórico — por qué es el ataque natural contra BB84:**

```
Alice prepara qubit → Eve intercepta y mide con base aleatoria
  → Si base Eve = base Alice: Eve obtiene bit correcto, qubit no perturbado
  → Si base Eve ≠ base Alice: resultado de Eve es aleatorio; qubit perturbado
     → Bob mide un qubit diferente al original → error en la clave
```

La probabilidad de que Eve elija la base incorrecta es 0.5. Cuando eso ocurre, introduce un error con probabilidad 0.5. Por lo tanto:

```
P(error inducido por Eve) = 0.5 × 0.5 = 0.25
→ QBER esperado con Eve al 100% = 25%
→ QBER sin Eve = 0% (canal ideal)
```

Un QBER observado por encima del umbral de seguridad (11%) indica presencia de Eve con alta significancia estadística.

---

## (b) Procedimiento paso a paso

### Entorno de simulación

| Elemento | Detalle |
|---|---|
| Lenguaje | Python 3.11+ |
| Librerías | Solo librería estándar (`random`, `logging`, `statistics`) |
| Reproducibilidad | `random.seed(42)` al inicio |
| Logging | Archivo `simulacion_bb84.log` + consola |

### Paso 1 — Modelar el qubit

```python
@dataclass
class Qubit:
    bit: int    # 0 o 1
    base: str   # '+' (rectilínea) o 'x' (diagonal)
```

### Paso 2 — Simular la medición cuántica

```python
def medir_qubit(qubit: Qubit, base_medicion: str) -> int:
    if base_medicion == qubit.base:
        return qubit.bit            # bases iguales → resultado determinista
    return random.randint(0, 1)    # bases distintas → colapso aleatorio
```

Este es el núcleo del protocolo: una base incorrecta introduce aleatoriedad, lo que genera errores detectables.

### Paso 3 — Protocolo BB84 completo con Eve opcional

```python
def bb84(n_bits, eve_presente=False, tasa_intercepcion=1.0):
    # 1. Alice genera bits y bases aleatorias
    # 2. Eve intercepta (si está presente) y reenvía qubits perturbados
    # 3. Bob mide con bases aleatorias
    # 4. Sifting: conservar solo bits con bases Alice == Bob
    # 5. Calcular QBER sobre la clave sifted
```

### Paso 4 — Ataque 1: intercepción total (Eve = 100%)

Se ejecutaron 20 repeticiones con 1.000 qubits cada una:

```
QBER promedio CON Eve: 0.2443  (σ=0.0183) — teórico: 0.2500
QBER promedio SIN Eve: 0.0000              — teórico: 0.0000
Eve detectable en: 20/20 simulaciones (100%)
```

La simulación confirma la predicción teórica con alta fidelidad (error < 1%).

### Paso 5 — Ataque 2: intercepción parcial (tasa variable)

```
Tasa Eve |  QBER obs.  |  QBER teórico | Estado
  10%    |   0.0264    |    0.0250     | ✓ sin detección
  20%    |   0.0488    |    0.0500     | ✓ sin detección
  30%    |   0.0702    |    0.0750     | ✓ sin detección
  40%    |   0.0971    |    0.1000     | ✓ sin detección
  50%    |   0.1272    |    0.1250     | ⚠ DETECTABLE
  ...
 100%    |   0.2491    |    0.2500     | ⚠ DETECTABLE
```

Conclusión: Eve puede interceptar hasta ~44% de los qubits sin superar el umbral de 11%.

---

## (c) Identificación y documentación de vulnerabilidades

### Tabla de hallazgos

| ID | Tipo de falla | Descripción | Evidencia de la simulación |
|---|---|---|---|
| VULN-01 | **Falla de implementación** | Sistema no verifica QBER ni aborta el protocolo si supera el umbral | QBER=0.2274 aceptado; 63 errores en clave de 277 bits entregada sin alerta |
| VULN-02 | **Falla de implementación** | Muestra de verificación de solo 10 bits: varianza estadística permite que Eve evada detección | Eve pasó desapercibida en 25/100 casos (25%) |
| VULN-03 | **Limitación de protocolo** | BB84 base no detecta a Eve con tasa baja (<44%); no incluye corrección de errores ni amplificación de privacidad | QBER < 0.11 en tasas de intercepción ≤ 40% |

### Criterio de distinción aplicado

**Falla de implementación (VULN-01 y VULN-02):** son decisiones incorrectas del desarrollador que no tienen relación con el diseño matemático de BB84. El protocolo BB84 *especifica* que se debe verificar el QBER y abortar si supera el umbral; un sistema que no lo hace tiene una falla de código, no del protocolo. Se corrigen modificando el código sin cambiar el algoritmo.

**Limitación de protocolo (VULN-03):** es intrínseca al diseño base de BB84. El protocolo no incluye por defecto amplificación de privacidad (Privacy Amplification) ni corrección de errores cuánticos (Cascade). No puede corregirse sin extender el protocolo con capas adicionales.

---

## (d) Reflexión sobre las limitaciones de la simulación

### Limitación 1 — Ruido de canal cuántico real

La simulación modela un canal ideal donde QBER=0 en ausencia de Eve. En un sistema QKD real (fibra óptica o espacio libre), el canal introduce **ruido cuántico intrínseco** que genera un QBER de fondo de entre 1% y 5% incluso sin ningún atacante. Esto crea un problema de discriminación: si Alice y Bob observan QBER=0.08, ¿es ruido del canal o Eve interceptando al 32%? La simulación **no puede modelar esta ambigüedad**, que en sistemas reales se aborda con modelos estadísticos del ruido de canal calibrados previamente.

### Limitación 2 — Pérdida de fotones y eficiencia de detectores

BB84 real transmite fotones individuales a través de fibra o aire. Los detectores de fotones únicos tienen eficiencias de 10%–80% y tasas de conteo oscuro (dark count), lo que genera pérdidas y falsos positivos que la simulación ignora por completo. Eve podría explotar estas pérdidas con un ataque de división de número de fotones (Photon Number Splitting, PNS), que **no es modelable** con la abstracción de qubit perfecto usada aquí.

### Limitación 3 — Ataques cuánticos avanzados (coherentes)

La simulación solo modela el ataque Intercept-Resend, que es incoherente (Eve mide qubit a qubit). Un adversario cuántico avanzado puede aplicar **ataques coherentes** donde Eve almacena qubits en memoria cuántica y los mide después de escuchar la reconciliación pública de bases. Estos ataques tienen potencial de extraer más información con menor QBER inducido. La simulación clásica en Python no puede representar superposición ni entrelazamiento real, por lo que estos vectores quedan fuera del alcance.

### Limitación 4 — Ausencia de Privacy Amplification y corrección de errores

En QKD real, después del sifting se aplican dos capas: reconciliación de errores (Error Correction, ej: protocolo Cascade) y amplificación de privacidad (Privacy Amplification mediante funciones de hash universales). Estas capas reducen drásticamente la información que Eve puede haber obtenido, incluso si interceptó una fracción de qubits. La simulación entrega la clave sifted cruda, **sobrestimando la información real de Eve** en un sistema correctamente implementado y subestimando la seguridad efectiva del protocolo completo.

---



La simulación demostró con evidencia estadística reproducible que el ataque Intercept-Resend sobre BB84 induce un QBER de ~24.4% (teórico: 25%), detectable en el 100% de los casos cuando Eve intercepta todos los qubits. Con interceptación parcial, Eve puede operar por debajo del umbral de detección si captura menos del ~44% del canal. Se identificaron dos fallas de implementación críticas (ausencia de verificación de QBER y muestra insuficiente) y una limitación de protocolo (ausencia de amplificación de privacidad). La simulación no puede capturar ruido de canal cuántico real, pérdida de fotones, ataques coherentes con memoria cuántica, ni el efecto de las capas de corrección de errores y amplificación de privacidad presentes en sistemas QKD de producción.
