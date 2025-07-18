# KavakInfoSearchTool

## Descripción

La `KavakInfoSearchTool` es una herramienta que permite realizar búsquedas semánticas de información general de Kavak. Utiliza embeddings para encontrar información relevante sobre propuesta de valor, sucursales, documentación necesaria, período de prueba, evaluación de vehículos, etc.

## Características

- **Búsqueda semántica**: Utiliza embeddings para encontrar información similar a la consulta del usuario
- **Summarizer integrado**: Genera respuestas breves y concisas usando un modelo más pequeño (gpt-4o-mini)
- **Límite configurable**: Permite especificar el número máximo de resultados a buscar
- **Manejo de errores**: Proporciona respuestas útiles cuando no encuentra información

## Uso

### En el AgentService

La herramienta está integrada en el `AgentService` y se ejecuta automáticamente cuando el agente detecta que el usuario está preguntando sobre información general de Kavak.

### Ejemplo de uso directo

```python
from tools.kavak_info_search_tool import KavakInfoSearchTool
from openai import OpenAI

# Inicializar la herramienta
client = OpenAI(api_key="your-api-key")
tool = KavakInfoSearchTool(openai_client=client)

# Ejecutar búsqueda
result = tool.execute({
    "query": "propuesta de valor",
    "max_results": 3
})

print(result)
```

## Parámetros

### Entrada

- `query` (string, requerido): La consulta sobre información de Kavak
  - Ejemplos: "propuesta de valor", "sucursales", "documentación para comprar", "período de prueba"
- `max_results` (integer, opcional): Número máximo de resultados a buscar (por defecto 3)

### Salida

- String con la información resumida y relevante sobre la consulta

## Integración

### En tools/__init__.py

```python
from .kavak_info_search_tool import KavakInfoSearchTool

__all__ = [
    "ExtractUserNameTool",
    "CatalogSearchTool", 
    "CarFinancialTool",
    "KavakInfoSearchTool"  # Nueva herramienta
]
```

### En agent_service.py

```python
# Importar la herramienta
from tools import ExtractUserNameTool, CatalogSearchTool, CarFinancialTool, KavakInfoSearchTool

# Inicializar en el constructor
self.kavak_info_search_tool = KavakInfoSearchTool(openai_client=self.client)

# Agregar a las definiciones de herramientas
tool_metas = [
    self.extract_user_name_tool.get_tool_definition(),
    self.catalog_search_tool.get_tool_definition(),
    self.car_financial_tool.get_tool_definition(),
    self.kavak_info_search_tool.get_tool_definition()  # Nueva herramienta
]

# Manejar en el bucle de ejecución
elif tool_call.function.name == "kavak_info_search":
    args = json.loads(tool_call.function.arguments)
    result = self.kavak_info_search_tool.execute(args)
    # ... manejo de respuesta
```

## Casos de uso

### 1. Información general de Kavak
- Propuesta de valor
- Historia y misión
- Servicios principales

### 2. Ubicaciones y sucursales
- Direcciones de sucursales
- Horarios de atención
- Información de contacto

### 3. Proceso de compra
- Documentación necesaria
- Pasos del proceso
- Requisitos del cliente

### 4. Servicios especiales
- Período de prueba
- Evaluación de vehículos
- Financiamiento
- Garantías

## Dependencias

- `services.kavak_info_service.KavakInfoService`: Para la búsqueda semántica
- `openai.OpenAI`: Para la generación de embeddings y summarización

## Testing

### Script de prueba individual
```bash
python scripts/test_kavak_info_tool.py
```

### Ejemplo con AgentService
```bash
python scripts/example_kavak_info_usage.py
```

## Consideraciones técnicas

1. **Base de datos**: Requiere que la tabla `kavak_info` esté poblada con información de Kavak
2. **Embeddings**: Utiliza el modelo `text-embedding-3-small` para generar embeddings
3. **Summarizer**: Usa `gpt-4o-mini` para generar respuestas breves (máximo 300 tokens)
4. **Fallback**: Si no hay cliente OpenAI disponible, devuelve los resultados sin summarizar

## Mejoras futuras

- [ ] Agregar filtros por tipo de información
- [ ] Implementar cache de embeddings
- [ ] Agregar métricas de relevancia
- [ ] Soporte para búsqueda híbrida (semántica + keywords) 