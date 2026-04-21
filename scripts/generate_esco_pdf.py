#!/usr/bin/env python3
"""
Genera un PDF compilado en español con todo el contenido de "About ESCO".
Usa los datos scrapeados + contenido de WebFetch para páginas que fallaron.
"""

import json
import os
import textwrap
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── WebFetch content for pages that failed scraping ───────────────────────────
# Translated to Spanish

WEBFETCH_CONTENT = {
    "https://esco.ec.europa.eu/es/node/222": """Cualificaciones y ESCO

La información sobre cualificaciones a nivel europeo se muestra actualmente en Europass y proviene de bases de datos nacionales que reflejan los Marcos Nacionales de Cualificaciones de cada Estado Miembro de la UE.

Requisitos de metadatos:
Las cualificaciones mostradas en Europass deben incluir campos de información básica:
- Título exacto de la cualificación
- Campo (basado en CINE-F 2013)
- País/Región
- Nivel del Marco Europeo de Cualificaciones (EQF)
- Organismo otorgante o autoridad competente
- Descripción de resultados de aprendizaje

Los Estados Miembros cargan los datos de cualificaciones estructurados según el esquema de metadatos en el registro de conjuntos de datos de cualificaciones (QDR).

Conexión con el Pilar de Competencias:
Las organizaciones pueden vincular los resultados de aprendizaje con la terminología de competencias de ESCO. La Comisión Europea realizó proyectos piloto en 2019-2020 para probar la vinculación automatizada de resultados de aprendizaje con conceptos de competencias ESCO en diferentes idiomas.

Conexión con el Pilar de Ocupaciones:
Las relaciones entre cualificaciones y ocupaciones se muestran solo cuando existen a nivel nacional. Estas relaciones pueden indicar si una cualificación es necesaria para ejercer ocupaciones específicas dentro de un Estado Miembro.""",

    "https://esco.ec.europa.eu/es/node/492": """Competencias Digitales en ESCO

En octubre de 2022, ESCO introdujo el etiquetado de Competencias y Conocimientos Digitales para distinguir las competencias digitales dentro de la clasificación, alineado con la Agenda Europea de Competencias.

Definición de Competencias Digitales:
La definición de ESCO se basa en el Marco de Competencia Digital para Ciudadanos (DigComp). Según la Recomendación del Consejo sobre Competencias Clave para el Aprendizaje Permanente, la competencia digital abarca "el uso seguro, crítico y responsable de las tecnologías digitales, y la interacción con ellas, para el aprendizaje, en el trabajo y para la participación en la sociedad."

Esto incluye: alfabetización informacional y de datos, comunicación y colaboración, alfabetización mediática, creación de contenido digital (incluida la programación), seguridad (incluyendo ciberseguridad y bienestar digital), cuestiones de propiedad intelectual, resolución de problemas y pensamiento crítico.

Metodología:
El proceso de etiquetado combina algoritmos de aprendizaje automático con validación humana a través de cinco pasos:
1. Etiquetado manual de competencias y conocimientos ESCO basado en DigComp 2.2
2. Etiquetado manual de ofertas de empleo en línea de la base de datos EURES
3. Desarrollo de un modelo de aprendizaje automático para clasificar conceptos digitales
4. Cálculo de puntuaciones de probabilidad digital
5. Comparación de conceptos etiquetados manualmente versus clasificados automáticamente

Resultados:
1.201 competencias y conocimientos ESCO clasificados como digitales, comprendiendo:
- 718 competencias
- 475 conceptos de conocimiento
- 7 competencias transversales

Beneficiarios:
- Servicios públicos de empleo identifican requisitos de competencias digitales
- Proveedores de educación recomiendan cursos apropiados de aprendizaje permanente
- Responsables políticos desarrollan políticas preparadas para lo digital
- Investigadores analizan patrones de digitalización""",

    "https://esco.ec.europa.eu/es/node/192": """Marco Europeo de Competencia Digital para Ciudadanos (DigComp)

El marco aborda "el uso seguro, crítico y responsable de las tecnologías digitales, y la interacción con ellas" en el aprendizaje, el trabajo y la participación cívica. La Comisión Europea lo desarrolló para mejorar la comprensión y el avance de la competencia digital en toda Europa.

Estructura del Marco:
DigComp consta de 21 competencias organizadas en cinco áreas:
- Alfabetización informacional y de datos
- Comunicación y colaboración
- Creación de contenido digital (incluida la programación)
- Seguridad (bienestar digital y ciberseguridad)
- Resolución de problemas

Integración con ESCO:
La Comisión incorporó las 21 competencias en el pilar de competencias de ESCO, manteniendo la organización jerárquica con metadatos en 28 idiomas. La integración requirió modificaciones mínimas debido a la alineación con el modelo de datos de ESCO. Los usuarios pueden acceder a DigComp a través del navegador de competencias ESCO, opciones de descarga o la API de ESCO.

Estado actual: ESCO v1.2 (actualizado el 15 de mayo de 2024)""",

    "https://esco.ec.europa.eu/es/node/202": """CINE-F 2013 (Clasificación Internacional Normalizada de la Educación: Campos de Educación y Formación)

La CINE-F 2013 es un sistema de clasificación mantenido por la UNESCO, separado de los niveles educativos ISCED.

Características clave:
El marco presenta "una jerarquía de tres niveles" con "11 campos amplios, 29 campos estrechos y aproximadamente 80 campos detallados."

Aplicación en ESCO:
Dentro del pilar de competencias de ESCO, la CINE-F sirve para organizar los conceptos de conocimiento de manera sistemática a través de los dominios educativos.

El Instituto de Estadística de la UNESCO mantiene documentación exhaustiva que detalla las descripciones de campos para este estándar de clasificación.""",

    "https://esco.ec.europa.eu/es/node/544": """Relevancia de Competencias en los Perfiles Ocupacionales de ESCO

El portal ESCO incorpora una función de Cuota de grupo de competencias dentro de los perfiles ocupacionales para ayudar a los usuarios a comprender intuitivamente los requisitos de competencias para trabajos específicos.

Funcionalidad clave:
La función visualiza cómo los diferentes dominios de competencias se relacionan con las ocupaciones a través de una representación gráfica. "Cada segmento del gráfico representa un grupo de competencias, y su tamaño refleja cuán relevante es ese grupo para la ocupación."

Los usuarios pueden interactuar con estos segmentos pasando el cursor para revelar la cantidad de competencias contenidas dentro de cada grupo.

Base de datos:
Esta funcionalidad depende de las Tablas de la Matriz de Competencias-Ocupaciones, que cuantifican la presencia proporcional de cada grupo de competencias ESCO dentro de ocupaciones particulares.

Propósito:
La Comisión Europea creó esta herramienta de visualización para permitir a los usuarios identificar rápidamente qué dominios de competencias son más importantes para cualquier ocupación dada.""",

    "https://esco.ec.europa.eu/es/node/224": """Grupos de Referencia

Los Grupos de Referencia fueron grupos de expertos de la Comisión Europea establecidos entre 2011 y 2015 para guiar el desarrollo de la clasificación ESCO.

Estructura:
Dos tipos de grupos operaron:
- Grupos de Referencia Sectoriales: enfocados en sectores económicos individuales
- Grupo de Referencia Intersectorial: abordó "competencias intersectoriales, cualificaciones intersectoriales y otros aspectos intersectoriales"

Composición:
Los miembros fueron designados por su experiencia personal, no como representación oficial. Los participantes incluyeron "interlocutores sociales, servicios de empleo, empleadores, asociaciones profesionales, consejos de competencias sectoriales, institutos de educación y formación, oficinas estadísticas y otros."

Operaciones:
La Comisión identificó 27 sectores económicos utilizando la clasificación NACE. Los primeros 11 sectores tuvieron Grupos de Referencia dedicados, mientras que los 16 restantes involucraron a las partes interesadas mediante consulta en línea.

Cronología:
Los tres primeros grupos se lanzaron en 2011; cuatro grupos adicionales en 2012, cinco más en 2013. Todos completaron su trabajo en 2015.""",

    "https://esco.ec.europa.eu/es/node/184": """ESCO v0.8

ESCO v0.8 se describe como "una versión de demostración de ESCO con fines de prueba piloto y testeo", finalizada en febrero de 2017.

Contenido: La versión abarca casi el conjunto de datos completo de ESCO v1 en su formato y estructura de modelo de datos final.

Cobertura lingüística: La versión de referencia en inglés es completa con ocupaciones traducidas a 26 idiomas ESCO, aunque las traducciones de conocimientos, competencias y habilidades permanecen incompletas en esta etapa.

Limitaciones notables: La versión no incluye un pilar de cualificaciones, que se añadiría en versiones posteriores.""",

    "https://esco.ec.europa.eu/es/node/185": """ESCO v0.9

ESCO v0.9 sirvió como versión de demostración diseñada para pruebas piloto. Estaba "programada para mayo de 2017 e incluiría casi el conjunto de datos completo de ESCO v1 en su formato y modelo de datos final."

Cobertura lingüística: La versión abarcó la edición de referencia en inglés junto con traducciones a 26 idiomas diferentes.

Limitaciones: "ESCO v0.9 no contiene un pilar de cualificaciones", distinguiéndola de la versión más completa ESCO v1.

Esta versión intermedia permitió pruebas y validación extensivas antes del lanzamiento oficial de v1.""",

    "https://esco.ec.europa.eu/es/node/186": """ESCO v1

ESCO v1 fue la primera versión a escala completa, lanzada a mediados de 2017. A diferencia de versiones anteriores (numeradas 0.x), "no solo se recomienda para pruebas piloto y testeo, sino también para sistemas en producción que prestan servicios a usuarios finales."

Escala del contenido:
La clasificación abarcó aproximadamente 3.000 ocupaciones, 13.500 conceptos de conocimiento/competencia/habilidad, y estableció un marco para el pilar de cualificaciones. Estaba disponible en 27 idiomas.

Proceso de desarrollo:
La creación abarcó de 2011 a 2017, involucrando dos enfoques paralelos: grupos de referencia sectoriales desarrollaron contenido para 11 sectores económicos, mientras que consultas en línea de expertos manejaron 16 sectores adicionales. Un Grupo de Referencia Intersectorial supervisó el desarrollo horizontal.

Sistema de versionado:
ESCO v1 introdujo un mecanismo formal de versionado para rastrear cambios, con múltiples sub-versiones (v1.0.1 a v1.0.9) abordando correcciones, mejoras de traducción, mejoras de API y refinamientos por retroalimentación de partes interesadas.""",

    "https://esco.ec.europa.eu/es/node/490": """ESCO v1.1.2

En febrero de 2024, la Comisión Europea lanzó ESCO v1.1.2, una actualización menor dirigida a mejorar la traducción al ucraniano dentro de ESCO.

Actualizaciones clave:
1. Descripciones en ucraniano: Traducción completa de descripciones de ocupaciones y competencias al ucraniano a nivel de clasificación ESCO
2. Refinamiento de competencias: Mejoras de calidad y correcciones que afectan a "9.680 títulos de competencias existentes (términos preferidos)"
3. Mejora de ocupaciones: Actualizaciones a "2.918 títulos de ocupaciones existentes (términos preferidos)"

Impacto práctico:
El conjunto de datos ampliado en ucraniano permite a las partes interesadas de ESCO aprovechar recursos lingüísticos más completos, beneficiando particularmente las herramientas de correspondencia de competencias.""",

    "https://esco.ec.europa.eu/es/node/503": """ESCO v1.2

En mayo de 2024, la Comisión Europea presentó esta actualización de versión mayor, empleando "un enfoque basado en datos que combina experiencia humana y técnicas de IA para la creación de contenido y mejora de calidad."

Adiciones clave:
La clasificación se amplió para incluir treinta y cinco nuevas ocupaciones, cuarenta y dos competencias adicionales, y ciento noventa y seis nuevos conceptos de conocimiento. La actualización introdujo seiscientos setenta y siete etiquetas alternativas y noventa y seis términos ocultos para mejorar la descubribilidad.

Mejoras de calidad:
Se ejecutaron dieciocho tareas de mejora, afectando a más de doce mil conceptos. Las modificaciones abordaron "eliminación de términos duplicados, corrección de competencias huérfanas, reasignación de competencias y conocimientos en la jerarquía."

Soporte lingüístico:
Se implementaron mejoras de traducción en veintiocho idiomas, con la adición de opciones de lengua de signos nacional para mayor accesibilidad.""",

    "https://esco.ec.europa.eu/es/node/210": """Sectores Económicos para el Desarrollo de ESCO v1

La Comisión Europea organizó el desarrollo de ESCO v1 en torno a 27 sectores de actividades económicas basados en la NACE revisión 2.

Proceso de desarrollo:
- Sectores 1-11: Participación de partes interesadas a través de Grupos de Referencia
- Sectores 12-27: Consulta en línea de partes interesadas

Los 27 sectores abarcan áreas económicas diversas, incluyendo:
- Industrias primarias: Agricultura, silvicultura, pesca; minería y canteras
- Manufactura: Alimentos, bebidas, textiles, químicos, maquinaria, equipos de transporte
- Servicios: TIC, hostelería, turismo, salud, educación, finanzas, seguros
- Sector público: Administración, defensa, organizaciones de membresía
- Campos especializados: Actividades veterinarias, energía, gestión de residuos, medios

Cada sector se mapea a clasificaciones NACE específicas.""",

    "https://esco.ec.europa.eu/es/node/120": """Valores Separados por Comas (CSV)

Los valores separados por comas (CSV) son un formato de datos que separa los campos de datos usando uno o más caracteres específicos (por ejemplo, coma, punto y coma o tabulación). Los registros de datos se organizan con saltos de línea, donde cada registro comienza en una nueva línea, y los archivos típicamente usan la extensión *.csv.

Aplicación en ESCO:
El portal de descarga de ESCO proporciona conjuntos de datos parciales en formato CSV que cubren:
- Conceptos y grupos de ocupaciones
- Conceptos de conocimientos, competencias y habilidades
- Relaciones cruzadas entre ocupaciones, competencias y cualificaciones
- Tablas de mapeo de países EURES

Los archivos CSV de ocupaciones incluyen URIs de conceptos, indicadores de tipo (OG para grupos, OC para ocupaciones), códigos ISCO, términos preferidos, definiciones e información de concepto padre.""",

    "https://esco.ec.europa.eu/es/node/121": """Competencia

ESCO adopta la definición del Marco Europeo de Cualificaciones: "competencia significa la capacidad demostrada de usar conocimientos, habilidades y capacidades personales, sociales y/o metodológicas, en situaciones de trabajo o estudio y en el desarrollo profesional y personal." Las competencias se caracterizan por niveles de responsabilidad y autonomía.

Distinción respecto a las habilidades:
Aunque a veces se usan indistintamente, estos términos difieren en alcance. Las habilidades típicamente implican usar métodos o herramientas específicas para tareas definidas en entornos particulares. La competencia es más amplia, refiriéndose a la capacidad de una persona para aplicar de forma independiente conocimientos y habilidades al enfrentar situaciones imprevistas y nuevos desafíos.

Ejemplo ilustrativo:
Un piloto de aviación civil debe combinar conocimiento de procedimientos de emergencia y averías de equipos con habilidades como leer coordenadas de posición y seguir rutas aéreas. Los pilotos ejercen estas competencias en entornos impredecibles que requieren resolución inmediata de problemas.

Dentro del marco de ESCO, las competencias constituyen parte del pilar de competencias.""",

    "https://esco.ec.europa.eu/es/node/147": """Definición

Una definición en ESCO es "un campo de texto que proporciona una definición formal que es ampliamente aceptada o legalmente vinculante en toda la UE."

Características clave:
Las definiciones en ESCO típicamente provienen de fuentes con autoridad significativa, incluyendo:
- Acuerdos establecidos por los interlocutores sociales a nivel europeo
- Terminología legalmente obligatoria de directivas y regulaciones de la UE

Relación con otros elementos:
Las definiciones difieren de dos conceptos relacionados en el sistema ESCO:
- Descripción: Proporciona información general sobre un concepto
- Nota de alcance: Aclara los límites y la aplicación de un término

Ejemplo:
La documentación ilustra esto con la ocupación "corredor de hipotecas", cuya definición deriva de la Directiva UE 2014/17.""",

    "https://esco.ec.europa.eu/es/node/148": """Descripción

Una descripción en ESCO es "un campo de texto que proporciona una breve explicación del significado del concepto y cómo debe entenderse."

Propósito:
Las descripciones aclaran los límites semánticos para los conceptos ESCO y se proporcionan para cada concepto en el sistema de clasificación.

Categorías principales:

Ocupaciones: Las descripciones incluyen la misión de la ocupación, el contexto de trabajo, el nivel de responsabilidad y la relación con otras ocupaciones dentro de su sector.

Competencias y habilidades: Estas explicaciones elaboran sobre lo que implica la competencia, alineándose con verbos de acción y niveles de detalle en los títulos.

Conceptos de conocimiento: Las descripciones proporcionan una visión más profunda del contenido que se describe.

Directrices de redacción (7 reglas sintácticas):
1. Mantener concisión y complejidad apropiada
2. Usar expresiones simples y oraciones cortas
3. Apuntar a 50-300 caracteres de longitud
4. Evitar la mera reformulación de la etiqueta
5. Excluir referencias nacionales
6. Reutilizar contenido de iniciativas europeas
7. Aplicar redacción consistente entre conceptos relacionados""",

    "https://esco.ec.europa.eu/es/node/199": """Género en ESCO

ESCO diferencia entre dos conceptos de género:
- Género natural: Determinado por atributos como el sexo de una persona
- Género gramatical: Categorías de sustantivos específicas del idioma

Atributos de género en ESCO (v1+):
ESCO indica el género natural para ocupaciones y cualificaciones usando cinco categorías:
- Femenino estándar: "Término recomendado para referirse a una mujer que trabaja en la ocupación"
- Masculino estándar: "Término recomendado para referirse a un hombre que trabaja en la ocupación"
- Femenino: Opción de término femenino alternativo
- Masculino: Opción de término masculino alternativo
- Neutro: Usado cuando el género es desconocido

Aplicaciones prácticas:
Los términos específicos de género apoyan la creación de CV y la correspondencia laboral. Por ejemplo, una mujer describiendo experiencia laboral puede preferir un término feminizado. El término preferido sirve como opción neutral por defecto.

Casos especiales:
Las ocupaciones con un solo género natural pueden tener términos preferidos específicos de género. Los términos ocultos pueden representar variantes de género no estándar.""",

    "https://esco.ec.europa.eu/es/node/200": """Término Oculto

Un término oculto es una categoría de clasificación dentro del sistema terminológico de ESCO. "Un término oculto es un tipo de término, junto al término preferido y no preferido." Cada concepto ESCO contiene un término preferido por idioma, junto con cero o múltiples términos no preferidos y ocultos.

Características: Los términos ocultos representan vocabulario "comúnmente usado en el mercado laboral" pero se consideran "obsoletos, mal escritos o políticamente incorrectos", haciéndolos "invisibles para el usuario final."

Función: Estos términos sirven para "propósitos de indexación, búsqueda y minería de texto." Cuando alguien busca un término oculto, el sistema redirige automáticamente al término preferido del concepto sin mostrar la terminología oculta.""",

    "https://esco.ec.europa.eu/es/node/208": """Datos Abiertos Vinculados (Linked Open Data)

"Los Datos Abiertos Vinculados (LOD) se refieren a un conjunto de mejores prácticas y patrones para hiper-vincular y publicar datos legibles por computadora en la web pública, bajo licencias abiertas que permiten la reutilización de datos."

Características clave:
Dichos datos pueden conectarse a otros conjuntos de datos, permitiendo a los usuarios descubrir redes de información más ricas. En lugar de la búsqueda tradicional por palabras clave, LOD facilita un enfoque de "navegación" o "descubrimiento" para localizar datos.

Aplicación en ESCO:
ESCO publica su clasificación usando la metodología de Datos Abiertos Vinculados para facilitar la reutilización e integración con fuentes de datos externas, incluyendo sistemas nacionales de clasificación ocupacional.""",

    "https://esco.ec.europa.eu/es/node/213": """Ocupación

Según ESCO, una ocupación se describe como: "una agrupación de empleos que involucran tareas similares y que requieren un conjunto similar de competencias."

Distinción clave:
El glosario enfatiza que las ocupaciones no deben confundirse con empleos o títulos de trabajo. Mientras que un empleo "está vinculado a un contexto de trabajo específico y es ejecutado por una persona", las ocupaciones agrupan empleos por características comunes.

Ejemplo práctico:
Un empleo específico sería "gerente de proyecto para el desarrollo del sistema de ventilación de la aeronave Superfly 900." Las ocupaciones relacionadas serían: "Gerente de proyecto", "especialista en motores de aeronaves" o "ingeniero de calefacción, ventilación y aire acondicionado."

Las ocupaciones en ESCO cubren actividades diversas del mercado laboral, incluyendo trabajo no remunerado, posiciones voluntarias, autoempleo y mandatos políticos.""",

    "https://esco.ec.europa.eu/es/node/219": """Cualificación

Según el glosario de ESCO, una cualificación se define como: "el resultado formal de un proceso de evaluación y validación que se obtiene cuando un órgano competente determina que un individuo ha alcanzado resultados de aprendizaje según estándares dados."

Esta definición proviene del Marco Europeo de Cualificaciones (EQF).

La información sobre cualificaciones a nivel europeo se consolida actualmente en Europass, que sirve como repositorio integral de datos de alta calidad sobre cualificaciones, marcos nacionales de cualificaciones y oportunidades de aprendizaje en toda Europa.""",

    "https://esco.ec.europa.eu/es/node/223": """RDF (Marco de Descripción de Recursos)

ESCO define RDF como un formato de datos usado para expresar y organizar información. "El conjunto de datos completo de ESCO puede descargarse en formato turtle desde el Portal de Servicios ESCO."

Puntos clave:
- Formato: Turtle (Terse RDF Triple Language) expresa datos según el modelo del Marco de Descripción de Recursos
- Escala: El conjunto de datos actual de ESCO comprende aproximadamente 6,5 millones de triples de datos
- Aplicación: Los desarrolladores pueden consultar estos datos usando SPARQL o trabajar con ellos a través de bibliotecas RDF como JENA
- Almacenamiento: Se recomienda instalar un almacén RDF (como Apache Fuseki) para cargar y gestionar los datos eficientemente
- Alternativa: La API de ESCO proporciona el método de integración más simple para aplicaciones""",

    "https://esco.ec.europa.eu/es/node/226": """Nota de Alcance

Una nota de alcance en ESCO "se usa para desambiguación. Por lo tanto, dirige a los usuarios: hacia conceptos similares que se consideran incluidos en el alcance y hacia conceptos alternativos que están excluidos."

Las notas de alcance trabajan junto con las descripciones para aclarar límites conceptuales. Emplean hipervínculos para conectar conceptos ESCO relacionados cuando se señalan exclusiones.

Ejemplos prácticos:
1. Ocupación: La entrada de un chef incluye roles relacionados como chefs de banquetes e instructores de formación dentro de su alcance
2. Ocupación con exclusiones: La definición de director de datos excluye explícitamente a científicos de datos y analistas de datos
3. Competencia: Una competencia de evaluación artística se aplica específicamente a creadores o intérpretes que evalúan presentaciones artísticas""",

    "https://esco.ec.europa.eu/es/node/543": """El Modelo Europeo de Aprendizaje (ELM)

El Modelo Europeo de Aprendizaje es "el primer Modelo de Datos multilingüe para la Interoperabilidad de oportunidades de aprendizaje, cualificaciones, acreditación y credenciales en Europa."

Características clave:
- Construido sobre estándares abiertos usando el modelo de datos W3C Verifiable Credential
- Disponible en 30 idiomas
- Contiene más de 560 propiedades para capturar datos relacionados con el aprendizaje
- Soporta aprendizaje formal, no formal e informal

Alcance:
El sistema acomoda contextos educativos diversos incluyendo educación general, formación profesional, educación superior, aprendizaje de adultos y formación del mercado laboral.

Integración con ESCO:
ESCO está integrado dentro del Modelo Europeo de Aprendizaje, permitiendo la referencia fácil de conceptos de competencias relevantes. Los Estados Miembros que publican información de cualificaciones y oportunidades de aprendizaje a través de Europass deben estructurar sus datos según el marco ELM.""",

    "https://esco.ec.europa.eu/es/node/238": """Identificador Uniforme de Recursos (URI)

Según el glosario de ESCO, un URI es un identificador único asignado a cada ocupación, conocimiento, competencia y habilidad en el sistema de clasificación.

Características clave:
"Cada URI es único en la web (universal); permite que datos de diferentes fuentes se vinculen a él; es persistente."

Propósito técnico:
El identificador funciona de manera similar a una dirección web, pero con una distinción crítica: opera como datos legibles por máquina, no solo contenido legible por humanos.

Componente de la Web Semántica:
Los URIs sirven como bloques de construcción esenciales para la infraestructura de la Web Semántica, permitiendo la vinculación e integración sistemática de datos entre plataformas.

La naturaleza persistente de los URIs soporta la compatibilidad retroactiva, asegurando que las referencias permanezcan válidas a través de versiones y actualizaciones de ESCO.""",

    "https://esco.ec.europa.eu/es/node/353": """ESCO en la Búsqueda y Correspondencia de Empleo

ESCO es utilizada por numerosas organizaciones en Europa y a nivel mundial para proporcionar servicios de correspondencia y búsqueda de empleo.

Organizaciones que usan ESCO:
Más de 35 organizaciones implementan la tecnología ESCO, incluyendo:

Plataformas de empleo y reclutadores: 50skills (Islandia), Actonomy (Bélgica), Adzuna (global), Bold (global), Monster, Randstad, entre otros.

Servicios públicos de empleo: Agencias gubernamentales de Albania, Finlandia, Grecia, Islandia, Irlanda, Israel y Malasia.

Herramientas especializadas: Iniciativas de la Comisión Europea como EURES, EUROPASS y la herramienta EU Skills Profile para nacionales de terceros países.

Empresas tecnológicas: Inda, Janzz technology, Textkernel, Techwolf y Visier integran ESCO en sus algoritmos de correspondencia.

Las organizaciones usan ESCO para estandarizar la clasificación de competencias y ocupaciones, permitiendo una correspondencia más precisa entre buscadores de empleo y oportunidades laborales en diferentes idiomas y mercados europeos.""",

    "https://esco.ec.europa.eu/es/node/124": """Correspondencia de Empleo Basada en Competencias

"Un método para encontrar la mejor correspondencia entre buscadores de empleo y vacantes comparando los conocimientos, competencias y habilidades del candidato con los requisitos del empleador."

Cómo funciona:
El enfoque requiere extraer, analizar e interpretar información relevante tanto de vacantes como de perfiles de buscadores de empleo. El marco de tres pilares de ESCO facilita este proceso organizando datos ocupacionales junto con conjuntos correspondientes de competencias que pueden conectarse con cualificaciones.

Beneficios clave:
- Transforma la experiencia laboral y credenciales en perfiles de competencias identificables para una correspondencia más precisa
- Crea mayor visibilidad de las competencias individuales para una alineación laboral precisa
- Permite la correspondencia laboral entre idiomas a través de las capacidades multilingües de ESCO, apoyando iniciativas como EURES""",

    "https://esco.ec.europa.eu/es/node/204": """Búsqueda de Empleo

"La búsqueda de empleo es el proceso de encontrar una selección reducida de un gran número de ofertas de trabajo que sean adecuadas para un candidato específico usando consultas de búsqueda."

Las ofertas aparecen en múltiples plataformas incluyendo sitios web de empleadores, bolsas de trabajo, redes sociales y sitios de servicios de empleo.

Cómo ESCO apoya la búsqueda de empleo:
1. Terminología estandarizada - proporciona conceptos consistentes para ocupaciones, conocimientos, competencias y habilidades
2. Capacidad multilingüe - permite buscar en todas las versiones de idiomas ESCO
3. Funciones de búsqueda inteligente - incorpora sinónimos y relaciones entre conceptos
4. Sugerencias relacionadas - identifica y recomienda conceptos conectados como filtros de búsqueda adicionales

Distinción respecto a la correspondencia de empleo:
A diferencia de la correspondencia basada en competencias, la búsqueda de empleo se basa en criterios proporcionados por el usuario en lugar de comparaciones digitales automáticas con perfiles de candidatos.""",

    "https://esco.ec.europa.eu/es/node/191": """Europass

La Unión Europea revisó el marco Europass en abril de 2018 para modernizar sus servicios, con el objetivo de "simplificar y modernizar sus herramientas y servicios y hacer que Europass sea apto para la era digital."

La plataforma actualizada presenta un e-portfolio digital junto al CV tradicional, proporciona información sobre cualificaciones europeas y oportunidades de aprendizaje, e integra inteligencia de competencias con datos del mercado laboral.

Rol de ESCO en Europass:
ESCO funciona como un activo semántico crucial que apoya la implementación de Europass. Los usuarios pueden aprovechar ESCO de tres maneras principales:

1. Selección de ocupaciones: Los usuarios pueden elegir ocupaciones ESCO al documentar experiencia laboral en su perfil
2. Construcción de competencias: La sección "Mis Competencias" ofrece sugerencias de competencias ESCO para ayudar a desarrollar un perfil personal
3. Etiquetas de intereses: Los usuarios pueden especificar intereses usando ocupaciones y competencias ESCO de listas controladas, que informan recomendaciones personalizadas de cursos y empleos""",

    "https://esco.ec.europa.eu/es/node/227": """Búsqueda de Oportunidades de Aprendizaje

"ESCO puede usarse en herramientas que permiten a los usuarios identificar conocimientos, competencias y habilidades que aumenten su empleabilidad o perspectivas de carrera."

Mecanismo clave:
El sistema opera anotando los resultados de aprendizaje de las cualificaciones con conceptos de competencias ESCO. "Los algoritmos comparan estos resultados de aprendizaje con las necesidades de formación del usuario", y las bases de datos dirigen a las personas hacia programas de formación relevantes basados en las brechas de competencias identificadas.

Propósito:
Este enfoque permite a las personas descubrir oportunidades de aprendizaje "basadas en necesidades reales del mercado laboral y así obtener las competencias adicionales" necesarias.""",

    "https://esco.ec.europa.eu/es/node/196": """Extensión de ESCO

"Una clasificación puede extenderse añadiendo conceptos más detallados y definiendo relaciones jerárquicas entre los nuevos conceptos y la clasificación."

Propósito:
Las secciones de ocupaciones y competencias de ESCO pueden expandirse para lograr mayor especificidad en sectores económicos particulares. Esta expansión permite el desarrollo de aplicaciones enfocadas en sectores con mayor precisión.

Aplicaciones:
El enfoque de extensión apoya herramientas especializadas incluyendo:
- Sistemas de correspondencia laboral
- Iniciativas de planificación de la fuerza laboral
- Plataformas de orientación profesional

Característica de gobernanza clave:
Un aspecto importante de las extensiones ESCO es que una clasificación y su versión expandida pueden ser administradas por organizaciones separadas, permitiendo la gestión distribuida del marco.""",

    "https://esco.ec.europa.eu/es/node/198": """Análisis de Brechas

Un análisis de brechas compara ESCO con clasificaciones ocupacionales nacionales para "identificar brechas reales en la clasificación ESCO, asegurando así su completitud."

Funciones clave:
El análisis sirve múltiples propósitos:
- Señala contenido faltante dentro de ESCO
- Revela diferencias en cuán detallado es ESCO en comparación con sistemas nacionales
- Identifica terminología alternativa adicional aún no incluida
- Valida ocupaciones que carecieron de aporte especializado durante el desarrollo

Implementación:
La Comisión Europea realizó un análisis de brechas contra ocho clasificaciones ocupacionales nacionales durante el desarrollo de ESCO v1. Los resultados fueron revisados y discutidos con el Comité de Mantenimiento de ESCO.""",

    "https://esco.ec.europa.eu/es/node/194": """Marco Europeo de Cualificaciones (EQF)

El EQF es una herramienta de referencia desarrollada por la Comisión Europea que permite la comparación de sistemas de cualificaciones entre países europeos.

Estructura y propósito:
El marco opera como "un marco de 8 niveles, basado en resultados de aprendizaje, para todos los tipos de cualificaciones" que funciona como mecanismo de traducción entre sistemas nacionales. Los niveles van del 1 (más bajo) al 8 (más alto).

Alcance:
Abarca todos los tipos y niveles de cualificaciones en Europa, enfatizando lo que los individuos "saben, comprenden y son capaces de hacer" a través de resultados de aprendizaje.

Desarrollo histórico:
Establecido en 2008, el EQF fue revisado en 2017. Esta actualización mantuvo su misión central mientras fortalecía su efectividad para ayudar a empleadores, trabajadores y estudiantes a comprender cualificaciones de diversas fuentes.

Conexión con ESCO:
El EQF se conecta con ESCO a través de su rol en vincular los resultados de aprendizaje de las cualificaciones con marcos de competencias.""",
}


def build_pdf():
    """Genera el PDF compilado en español."""

    # Load scraped data
    with open('exports/esco_about_scraped.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    pages = data['pages']

    # Merge WebFetch content into pages that failed
    for page in pages:
        if page['status'] != 'ok' and page['url'] in WEBFETCH_CONTENT:
            page['content'] = WEBFETCH_CONTENT[page['url']]
            page['status'] = 'ok_webfetch'

    # Count final status
    ok = sum(1 for p in pages if p['status'] in ('ok', 'ok_webfetch', 'ok_translated'))
    print(f"Páginas con contenido: {ok}/{len(pages)}")

    # ── Build PDF ─────────────────────────────────────────────────────────────

    output_path = 'exports/ESCO_Guia_Completa_ES.pdf'

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=6*mm,
        textColor=HexColor('#1F3864'),
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12*mm,
        textColor=HexColor('#4472C4'),
        alignment=TA_CENTER,
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=12*mm,
        spaceAfter=6*mm,
        textColor=HexColor('#1F3864'),
        borderColor=HexColor('#4472C4'),
        borderWidth=1,
        borderPadding=4,
    )

    page_title_style = ParagraphStyle(
        'PageTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=8*mm,
        spaceAfter=4*mm,
        textColor=HexColor('#2F5496'),
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=3*mm,
        alignment=TA_JUSTIFY,
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=body_style,
        leftIndent=12*mm,
        bulletIndent=6*mm,
    )

    url_style = ParagraphStyle(
        'URLText',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#888888'),
        spaceAfter=2*mm,
    )

    toc_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['Normal'],
        fontSize=10,
        leading=16,
        leftIndent=8*mm,
    )

    toc_section_style = ParagraphStyle(
        'TOCSection',
        parent=styles['Normal'],
        fontSize=11,
        leading=18,
        textColor=HexColor('#1F3864'),
        fontName='Helvetica-Bold',
        spaceBefore=3*mm,
    )

    # ── Build story ───────────────────────────────────────────────────────────

    story = []

    # Cover page
    story.append(Spacer(1, 4*cm))
    story.append(Paragraph(
        "ESCO",
        ParagraphStyle('BigTitle', parent=title_style, fontSize=48)
    ))
    story.append(Paragraph(
        "Clasificaci&oacute;n Europea de Capacidades,<br/>Competencias, Cualificaciones y Ocupaciones",
        title_style
    ))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "Gu&iacute;a Completa en Espa&ntilde;ol",
        subtitle_style
    ))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        f"Compilado por OEDE &mdash; {datetime.now().strftime('%d/%m/%Y')}",
        ParagraphStyle('DateStyle', parent=subtitle_style, fontSize=10, textColor=HexColor('#666666'))
    ))
    story.append(Paragraph(
        f"Fuente: esco.ec.europa.eu &mdash; {ok} p&aacute;ginas extra&iacute;das",
        ParagraphStyle('SourceStyle', parent=subtitle_style, fontSize=9, textColor=HexColor('#999999'))
    ))
    story.append(PageBreak())

    # Table of Contents
    story.append(Paragraph("&Iacute;ndice", section_style))
    story.append(Spacer(1, 4*mm))

    current_section = None
    for page in pages:
        if page['status'] not in ('ok', 'ok_webfetch', 'ok_translated'):
            continue
        if page['section'] != current_section:
            current_section = page['section']
            story.append(Paragraph(
                current_section.replace('&', '&amp;'),
                toc_section_style
            ))
        story.append(Paragraph(
            f"&bull; {page['title'].replace('&', '&amp;')}",
            toc_style
        ))

    story.append(PageBreak())

    # Content pages
    current_section = None
    for page in pages:
        if page['status'] not in ('ok', 'ok_webfetch', 'ok_translated'):
            continue

        # Section header
        if page['section'] != current_section:
            current_section = page['section']
            story.append(Paragraph(
                current_section.replace('&', '&amp;'),
                section_style
            ))

        # Page title
        story.append(Paragraph(
            page['title'].replace('&', '&amp;'),
            page_title_style
        ))

        # URL
        story.append(Paragraph(
            f"Fuente: {page['url']}",
            url_style
        ))

        # Content - process line by line
        content = page['content']
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Escape HTML entities
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            # Detect formatting
            if line.startswith('=' * 10):
                continue  # separator line
            elif line.startswith('---'):
                story.append(Spacer(1, 2*mm))
                continue
            elif line.startswith('&bull;') or line.startswith('- ') or line.startswith('* '):
                clean = line.lstrip('-* ').lstrip('&bull; ')
                story.append(Paragraph(f"&bull; {clean}", bullet_style))
            elif line.startswith('|'):
                # Table-like content - just show as body text
                story.append(Paragraph(line, body_style))
            else:
                # Check if it looks like a sub-heading (short, ends with colon)
                if len(line) < 80 and line.endswith(':'):
                    story.append(Paragraph(
                        f"<b>{line}</b>",
                        ParagraphStyle('SubHead', parent=body_style, spaceBefore=3*mm)
                    ))
                else:
                    story.append(Paragraph(line, body_style))

        story.append(Spacer(1, 4*mm))

    # Build PDF
    doc.build(story)

    file_size = os.path.getsize(output_path)
    print(f"\nPDF generado: {output_path}")
    print(f"Tamaño: {file_size / 1024:.0f} KB")
    print(f"Páginas con contenido: {ok}/{len(pages)}")


if __name__ == '__main__':
    build_pdf()
