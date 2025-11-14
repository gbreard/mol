"""
Schemas Pydantic para validar respuestas de la API de Bumeran
=============================================================

Define modelos de datos para validar la estructura de:
- Ofertas individuales
- Respuestas de la API
- Planes de publicación

Uso:
    from bumeran_schemas import BumeranOfertaAPI, BumeranAPIResponse

    # Validar una oferta
    oferta = BumeranOfertaAPI(**raw_data)

    # Validar respuesta completa
    response = BumeranAPIResponse(**api_data)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class PlanPublicacion(BaseModel):
    """Plan de publicación de la oferta"""
    id: Optional[int] = None
    nombre: Optional[str] = None

    class Config:
        extra = 'allow'  # Permitir campos adicionales


class BumeranOfertaAPI(BaseModel):
    """
    Modelo de validación para una oferta de Bumeran desde la API

    Campos críticos (obligatorios):
    - id: ID único de la oferta
    - titulo: Título de la oferta
    - empresa: Nombre de la empresa
    - fechaPublicacion: Fecha de publicación

    Campos opcionales:
    - Todos los demás campos son opcionales para permitir flexibilidad
    """

    # === CAMPOS CRÍTICOS (OBLIGATORIOS) ===
    id: int = Field(..., description="ID único de la oferta")
    titulo: str = Field(..., min_length=1, description="Título de la oferta")
    empresa: str = Field(..., min_length=1, description="Nombre de la empresa")
    fechaPublicacion: str = Field(..., description="Fecha de publicación (formato DD-MM-YYYY)")

    # === CAMPOS IMPORTANTES (OPCIONALES PERO COMUNES) ===
    idEmpresa: Optional[int] = None
    detalle: Optional[str] = Field(None, description="Descripción completa de la oferta")
    confidencial: Optional[bool] = False

    # Ubicación y modalidad
    localizacion: Optional[str] = None
    modalidadTrabajo: Optional[str] = None
    tipoTrabajo: Optional[str] = None

    # Fechas adicionales
    fechaHoraPublicacion: Optional[str] = None
    fechaModificado: Optional[str] = None

    # Detalles de la oferta
    cantidadVacantes: Optional[int] = None
    aptoDiscapacitado: Optional[bool] = False

    # Categorización
    idArea: Optional[int] = None
    idSubarea: Optional[int] = None
    idPais: Optional[int] = None

    # Información de empresa
    logoURL: Optional[str] = None
    validada: Optional[bool] = False
    empresaPro: Optional[bool] = False
    promedioEmpresa: Optional[float] = None

    # Plan de publicación
    planPublicacion: Optional[PlanPublicacion] = None

    # Otros campos
    portal: Optional[str] = None
    tipoAviso: Optional[str] = None
    tienePreguntas: Optional[bool] = False
    salarioObligatorio: Optional[bool] = False
    altaRevisionPerfiles: Optional[bool] = False
    guardado: Optional[bool] = False
    gptwUrl: Optional[str] = None

    class Config:
        extra = 'allow'  # Permitir campos adicionales no definidos

    @field_validator('id')
    @classmethod
    def validate_id_positive(cls, v):
        """Validar que el ID sea positivo"""
        if v <= 0:
            raise ValueError(f"ID debe ser positivo, recibido: {v}")
        return v

    @field_validator('titulo', 'empresa')
    @classmethod
    def validate_not_empty(cls, v):
        """Validar que título y empresa no estén vacíos"""
        if not v or not v.strip():
            raise ValueError("Campo no puede estar vacío")
        return v.strip()

    @field_validator('fechaPublicacion')
    @classmethod
    def validate_fecha_format(cls, v):
        """Validar formato de fecha DD-MM-YYYY"""
        if not v:
            raise ValueError("Fecha de publicación es obligatoria")

        # Validar formato básico (DD-MM-YYYY)
        parts = v.split('-')
        if len(parts) != 3:
            raise ValueError(f"Formato de fecha inválido: {v}. Esperado: DD-MM-YYYY")

        day, month, year = parts
        if not (len(day) == 2 and len(month) == 2 and len(year) == 4):
            raise ValueError(f"Formato de fecha inválido: {v}. Esperado: DD-MM-YYYY")

        return v


class BumeranAPIResponse(BaseModel):
    """
    Modelo de validación para la respuesta completa de la API de Bumeran

    Estructura esperada:
    {
        "content": [...],  # Lista de ofertas
        "total": 1234,      # Total de ofertas disponibles
        "page": 0,          # Página actual
        "pageSize": 20      # Tamaño de página
    }
    """

    content: List[Dict[str, Any]] = Field(..., description="Lista de ofertas (sin validar internamente)")
    total: int = Field(..., ge=0, description="Total de ofertas disponibles")
    page: Optional[int] = Field(0, ge=0, description="Número de página (0-indexed)")
    pageSize: Optional[int] = Field(20, ge=1, le=100, description="Ofertas por página")

    class Config:
        extra = 'allow'  # Permitir campos adicionales (ej: filters, facets, etc.)

    @field_validator('content')
    @classmethod
    def validate_content_is_list(cls, v):
        """Validar que content sea una lista"""
        if not isinstance(v, list):
            raise ValueError(f"'content' debe ser una lista, recibido: {type(v)}")
        return v

    def validate_ofertas(self) -> tuple[List[BumeranOfertaAPI], List[Dict]]:
        """
        Valida cada oferta en 'content' contra el schema BumeranOfertaAPI

        Returns:
            Tupla con:
            - Lista de ofertas válidas (BumeranOfertaAPI)
            - Lista de ofertas inválidas (dict con error)
        """
        ofertas_validas = []
        ofertas_invalidas = []

        for idx, oferta_raw in enumerate(self.content):
            try:
                oferta_validada = BumeranOfertaAPI(**oferta_raw)
                ofertas_validas.append(oferta_validada)
            except Exception as e:
                ofertas_invalidas.append({
                    'index': idx,
                    'oferta_id': oferta_raw.get('id', 'unknown'),
                    'error': str(e),
                    'raw_data': oferta_raw
                })

        return ofertas_validas, ofertas_invalidas


class ValidationResult(BaseModel):
    """Resultado de validación de una respuesta de API"""

    success: bool = Field(..., description="True si la respuesta es válida")
    total_ofertas: int = Field(..., ge=0, description="Total de ofertas en la respuesta")
    ofertas_validas: int = Field(..., ge=0, description="Número de ofertas que pasaron validación")
    ofertas_invalidas: int = Field(..., ge=0, description="Número de ofertas que fallaron validación")
    errores: List[str] = Field(default_factory=list, description="Lista de errores encontrados")
    warnings: List[str] = Field(default_factory=list, description="Lista de advertencias")

    @property
    def tasa_exito(self) -> float:
        """Calcula la tasa de éxito de validación"""
        if self.total_ofertas == 0:
            return 0.0
        return (self.ofertas_validas / self.total_ofertas) * 100

    def __str__(self) -> str:
        return (
            f"ValidationResult(success={self.success}, "
            f"válidas={self.ofertas_validas}/{self.total_ofertas} ({self.tasa_exito:.1f}%), "
            f"errores={len(self.errores)})"
        )


# ===== FUNCIONES HELPER =====

def validar_respuesta_api(response_data: Dict[str, Any]) -> ValidationResult:
    """
    Valida una respuesta completa de la API de Bumeran

    Args:
        response_data: Dict con la respuesta de la API

    Returns:
        ValidationResult con estadísticas de validación
    """
    result = ValidationResult(
        success=False,
        total_ofertas=0,
        ofertas_validas=0,
        ofertas_invalidas=0
    )

    try:
        # Validar estructura de respuesta
        api_response = BumeranAPIResponse(**response_data)
        result.total_ofertas = len(api_response.content)

        # Validar cada oferta individualmente
        ofertas_validas, ofertas_invalidas = api_response.validate_ofertas()

        result.ofertas_validas = len(ofertas_validas)
        result.ofertas_invalidas = len(ofertas_invalidas)

        # Agregar errores de validación
        for oferta_invalida in ofertas_invalidas:
            error_msg = (
                f"Oferta ID {oferta_invalida['oferta_id']} (index {oferta_invalida['index']}): "
                f"{oferta_invalida['error']}"
            )
            result.errores.append(error_msg)

        # Advertencias si hay ofertas inválidas
        if ofertas_invalidas:
            tasa_fallo = (len(ofertas_invalidas) / result.total_ofertas) * 100
            result.warnings.append(
                f"{len(ofertas_invalidas)} ofertas ({tasa_fallo:.1f}%) fallaron validación"
            )

        # Marcar como exitoso si al menos 80% de ofertas son válidas
        result.success = result.tasa_exito >= 80.0

    except Exception as e:
        result.success = False
        result.errores.append(f"Error validando estructura de respuesta: {str(e)}")

    return result


if __name__ == "__main__":
    # Ejemplo de uso
    print(__doc__)
    print()
    print("Ejemplo de validación:")
    print("="*70)

    # Ejemplo de oferta válida
    oferta_ejemplo = {
        "id": 1118014800,
        "titulo": "Analista de Datos",
        "empresa": "Tech Corp",
        "fechaPublicacion": "30-10-2025",
        "detalle": "Buscamos analista con experiencia en Python y SQL",
        "localizacion": "Capital Federal"
    }

    try:
        oferta_validada = BumeranOfertaAPI(**oferta_ejemplo)
        print(f"✅ Oferta válida: {oferta_validada.titulo} - {oferta_validada.empresa}")
    except Exception as e:
        print(f"❌ Error: {e}")
