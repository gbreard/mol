# Condicionales pre-procesados para el traductor del Eje 4 (2026-07-03)

Los 29 condicionales de la bandeja, agrupados por la familia/senal que los mando ahi,
cruzados con los arboles de Cyn (`exports/cyn_backlog/taxonomia_contexto_cyn.md`).

- **CUBIERTO-POR-ARBOL**: la familia ya tiene arbol de desambiguacion de Cyn -> el traductor arranca con la especificacion hecha.
- **FAMILIA-NUEVA**: no hay arbol -> necesita sesion con Cyn.

## azul:operario  (4)  — **CUBIERTO-POR-ARBOL**
- [1118019322] OPERARIO CENTRAL DE PESADA -> 9333.3
- [1118007106] BU667 Operario de Producción Metalúrgico (Experiencia e -> 7223.1
- [1118163504] Operario Sr - Corte y Costura - Multinacional Autoparti -> 8153.1
- [5804676995] Operario/a soldador -> 7212.2  _(arbol: 'operario/a soldador')_

## azul:tecnico  (3)  — **CUBIERTO-POR-ARBOL**
- [5876264262] Tecnico Torrista -> 3522.1
- [6053706024] Técnico de mantenimiento eléctrico industrial. Zona Aba -> 7412.3
- [6185898502] técnico/a electricista -> 7411.1.1

## blanca:advisor  (2)  — **FAMILIA-NUEVA**
- [1117985442] Advisor -> 2519.7
- [1117968852] Advisor -> 2519.7

## blanca:analista  (3)  — **FAMILIA-NUEVA**
- [1117978310] Analista Corporativo de operaciones - Data Center (CABA -> 2522.1
- [1118019485] Analista de Oficina Técnica -> 2142.1
- [5786782663] Ref 20975Analista de prevención para incorporar al área -> 2263.3

## blanca:asesor  (1)  — **FAMILIA-NUEVA**
- [5821474489] Asesor comercial -> 1221.3.2

## blanca:consultor  (1)  — **FAMILIA-NUEVA**
- [2145263] Consultor Junior y Semi Junior de Liquidación de Sueldo -> 2511.12

## blanca:encargado  (1)  — **FAMILIA-NUEVA**
- [7186551637] Encargado de Logistica -> 1324.3.4

## blanca:programador  (1)  — **FAMILIA-NUEVA**
- [1118132013] Programador/a de la Producción -> 3122.2

## blanca:responsable  (1)  — **FAMILIA-NUEVA**
- [5770283730] Responsable de Depósito – productos de alto valor y alt -> 1324.3.1.6.11

## dict:gerente  (2)  — **FAMILIA-NUEVA**
- [7006539054] Gerente Administración -> 1211.1
- [1118042070] Lobos - Gerente Comercial para Importante Grupo de Conc -> 1221.3.2.1

## dict:operador  (1)  — **FAMILIA-NUEVA**
- [1118145955] Operador de Producción -> 8142.2

## forma  (4)  — **FAMILIA-NUEVA**
- [1117951568] Desarrollador PYTHON Sr para Proyectos Bancarios -> 2512.9
- [1118059308] Estudiante de Abogacía -> 3411.4
- [1118019188] Chófer con experiencia en recolección de residuos Villa -> 8332.2
- [5898997970] Ayudante de taller. lonas y toldos -> 7533.4

## guard  (5)  — **FAMILIA-NUEVA**
- [6208652557] Ingeniero Electrónico (Vicente Lopez) -> 2152.1.12
- [1118019326] Medio Oficial de Mantenimiento- Rubro Plástico. Zona Vi -> 7233.8.1
- [2155532] Representante de Ventas - Sector Industrial - Zona Bahí -> 2433.6.1
- [5784938217] auxiliar de promociones y marketing -> 3332.2.1
- [5945752836] Supervisor de Instalacion -> 3123.1.22

---
## Split que ordena el diseno del traductor
- **CUBIERTO-POR-ARBOL: 7** / 29  (familias azules operario/tecnico con arbol de Cyn)
- **FAMILIA-NUEVA: 22** / 29  (blancas + dict-contexto + forma + guard, sin arbol)

El traductor arranca por las CUBIERTO (especificacion de Cyn ya escrita); las FAMILIA-NUEVA
son el orden de trabajo de la sesion con Cyn (definir arbol de contexto por familia).