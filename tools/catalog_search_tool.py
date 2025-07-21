#!/usr/bin/env python3
"""
Tool for catalog search functionality.
"""

import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from pydantic import BaseModel, Field
from prompts.catalog_search import get_catalog_search_normalization_prompt


class CarFilters(BaseModel):
    stock_id: Optional[str] = Field(None, description="ID de stock del auto")
    make: Optional[str] = Field(None, description="Marca del auto")
    model: Optional[str] = Field(None, description="Modelo del auto")
    year: Optional[List[int]] = Field(None, description="Rango de año [mínimo, máximo] o año específico [año, año]")
    price: Optional[List[int]] = Field(None, description="Rango de precio [mínimo, máximo]")
    km: Optional[List[int]] = Field(None, description="Rango de kilometraje [mínimo, máximo]")
    bluetooth: Optional[bool] = Field(None, description="¿Tiene bluetooth?")
    car_play: Optional[bool] = Field(None, description="¿Tiene car play?")
    descripcion: Optional[str] = Field(None, description="Descripción del auto")
    version: Optional[str] = Field(None, description="Versión del auto")
    other_preferences: Optional[str] = Field(None, description="Otras preferencias del usuario")


class CatalogSearchTool:
    """Tool for searching cars in the catalog."""

    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        Initialize the tool.

        Args:
            openai_client: OpenAI client for data normalization
        """
        self.client = openai_client

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition for OpenAI API.

        Returns:
            Dict containing tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": "catalog_search",
                "description": (
                    "Busca en la base de datos de autos usando embeddings para la similitud semántica. "
                    "Puede filtrar por rangos de precio, año, dimensiones y por un kilometraje máximo. "
                    "Devuelve una lista de autos con sus datos estructurados."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "price": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Rango de precio en dólares: [mínimo, máximo]"
                        },
                        "km": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Rango de kilometraje: [mínimo, máximo]"
                        },
                        "make": {"type": "string", "description": "Marca del auto"},
                        "model": {"type": "string", "description": "Modelo del auto"},
                        "year": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "Rango de año [mínimo, máximo] o año específico [año, año]"
                        },
                        "version": {"type": "string", "description": "Versión del auto"},
                        "bluetooth": {"type": "boolean", "description": "¿Tiene bluetooth?"},
                        "car_play": {"type": "boolean", "description": "¿Tiene car play?"},
                        "other": {"type": "string", "description": "Cualquier otro filtro adicional relevante para la busqueda"}
                    },
                    "required": []
                }
            }
        }

    def _normalize_filters(self, args: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Normalize filters using LLM.

        Args:
            args: Raw filter arguments

        Returns:
            Dict: Normalized filters
        """
        if not self.client:
            return args

        brands_list = [
            "Audi", "BMW", "Chevrolet", "Dodge", "Fiat", "Ford", "Honda", "Infiniti", "JAC", "Jeep",
            "KIA", "Land Rover", "Lincoln", "Mazda", "Mercedes Benz", "MG", "Mini", "Nissan", "Peugeot",
            "Renault", "Seat", "Suzuki", "Toyota", "Volkswagen", "Volvo"
        ]
        brands_str = ", ".join(brands_list)

        extraction_prompt = get_catalog_search_normalization_prompt(brands_str)

        try:
            normalize_response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": json.dumps(args)}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            normalized_content = normalize_response.choices[0].message.content
            return json.loads(normalized_content) if normalized_content else args
        except Exception as e:
            print(f"Error normalizando filtros: {e}")
            return args

    def _convert_tool_args_to_filters(self, args: dict) -> dict:
        """
        Convert tool arguments to search filters.

        Args:
            args: Tool call arguments

        Returns:
            dict: Search filters
        """
        filters = {}

        # Convert individual parameters
        if args.get('make'):
            filters['make'] = args['make']
        if args.get('model'):
            filters['model'] = args['model']
        if args.get('version'):
            filters['version'] = args['version']
        if args.get('bluetooth') is not None:
            filters['bluetooth'] = args['bluetooth']
        if args.get('car_play') is not None:
            filters['car_play'] = args['car_play']

        # Convert range parameters
        if args.get('year') and isinstance(args['year'], list) and len(args['year']) == 2:
            filters['year'] = args['year']

        if args.get('price') and isinstance(args['price'], list) and len(args['price']) == 2:
            filters['price'] = args['price']

        if args.get('km') and isinstance(args['km'], list) and len(args['km']) == 2:
            filters['km'] = args['km']

        return filters

    def _search_cars_regular(self, filters: dict | None = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search cars using regular SQL queries with filters.

        Args:
            filters: Optional filters for search
            limit: Maximum number of results to return

        Returns:
            List[Dict[str, Any]]: List of car results
        """
        try:
            from sqlalchemy import text
            from db.session import SessionLocal

            # Build SQL query
            base_sql = """
                SELECT 
                    stock_id,
                    make,
                    model,
                    year,
                    price,
                    km,
                    bluetooth,
                    car_play,
                    descripcion
                FROM cars
                WHERE 1=1
            """

            params = {}

            # Add filters if provided
            if filters:
                if filters.get('make'):
                    base_sql += " AND make ILIKE :make"
                    params['make'] = f"%{filters['make']}%"

                if filters.get('model'):
                    base_sql += " AND model ILIKE :model"
                    params['model'] = f"%{filters['model']}%"

                if filters.get('version'):
                    base_sql += " AND version ILIKE :version"
                    params['version'] = f"%{filters['version']}%"

                if filters.get('descripcion'):
                    base_sql += " AND descripcion ILIKE :descripcion"
                    params['descripcion'] = f"%{filters['descripcion']}%"

                if filters.get('year') and isinstance(filters['year'], list) and len(filters['year']) == 2:
                    min_year, max_year = filters['year']
                    if min_year is not None:
                        base_sql += " AND year >= :year_min"
                        params['year_min'] = min_year
                    if max_year is not None:
                        base_sql += " AND year <= :year_max"
                        params['year_max'] = max_year

                if filters.get('price') and isinstance(filters['price'], list) and len(filters['price']) == 2:
                    min_price, max_price = filters['price']
                    if min_price is not None:
                        base_sql += " AND price >= :price_min"
                        params['price_min'] = min_price
                    if max_price is not None:
                        base_sql += " AND price <= :price_max"
                        params['price_max'] = max_price

                if filters.get('km') and isinstance(filters['km'], list) and len(filters['km']) == 2:
                    min_km, max_km = filters['km']
                    if min_km is not None:
                        base_sql += " AND km >= :km_min"
                        params['km_min'] = min_km
                    if max_km is not None:
                        base_sql += " AND km <= :km_max"
                        params['km_max'] = max_km

                if filters.get('bluetooth') is not None:
                    base_sql += " AND bluetooth = :bluetooth"
                    params['bluetooth'] = filters['bluetooth']

                if filters.get('car_play') is not None:
                    base_sql += " AND car_play = :car_play"
                    params['car_play'] = filters['car_play']

            # Determine ordering based on whether price filter is applied
            if filters and filters.get('price'):
                base_sql += " ORDER BY price ASC LIMIT :limit"
            else:
                base_sql += " ORDER BY year DESC LIMIT :limit"
            params['limit'] = limit
            print(f"🔍 Query final ", base_sql, "con parámetros:", params)
            # Execute query
            session = SessionLocal()

            try:
                sql_query = text(base_sql)
                result = session.execute(sql_query, params)

                # Convert results to list of dictionaries
                cars = []
                for row in result:
                    car = {
                        'stock_id': row.stock_id,
                        'make': row.make,
                        'model': row.model,
                        'year': row.year,
                        'price': float(row.price) if row.price else None,
                        'km': row.km,
                        'bluetooth': row.bluetooth,
                        'car_play': row.car_play,
                        'descripcion': row.descripcion
                    }
                    cars.append(car)

                return cars

            finally:
                session.close()

        except Exception as e:
            print(f"Error in regular car search: {e}")
            return []

    def _format_car_search_results(self, cars: List[Dict[str, Any]]) -> str:
        """
        Format car search results into a readable string.

        Args:
            cars: List of car dictionaries

        Returns:
            str: Formatted results string
        """
        if not cars:
            return "No se encontraron autos que coincidan con tu búsqueda."

        result_lines = [f"Encontré {len(cars)} auto(s) que coinciden con tu búsqueda:"]

        for i, car in enumerate(cars, 1):
            price_str = f"${car['price']:,.0f}" if car['price'] else "Precio no disponible"
            features = []
            if car['bluetooth']:
                features.append("Bluetooth")
            if car['car_play']:
                features.append("CarPlay")
            features_str = ", ".join(features) if features else "Sin características especiales"

            result_lines.append(f"\n{i}. {car['make']} {car['model']} {car['year']}")
            result_lines.append(f"   Stock ID: {car['stock_id']}")
            result_lines.append(f"   Precio: {price_str}")
            result_lines.append(f"   Kilometraje: {car['km']:,} km")
            result_lines.append(f"   Características: {features_str}")
            result_lines.append(f"   Descripción: {car['descripcion']}")
            # Solo mostrar relevancia si existe (búsqueda semántica)
            if 'similarity_score' in car:
                result_lines.append(f"   Relevancia: {car['similarity_score']:.4f}")

        return "\n".join(result_lines)

    def execute(self, args: Dict[str, Any], limit: 5) -> str:
        """
        Execute the catalog search tool.

        Args:
            args: Tool arguments containing search filters
            limit: Maximum number of results to return

        Returns:
            str: Formatted search results
        """
        try:

            # Normalize filters using specialized LLM
            normalized_args = self._normalize_filters(args, model="gpt-4o-mini")

            # Convert normalized args to search filters
            if normalized_args is None:
                search_filters = {}
            elif isinstance(normalized_args, CarFilters):
                search_filters = self._convert_tool_args_to_filters(normalized_args.dict())
            else:
                search_filters = self._convert_tool_args_to_filters(normalized_args)

            search_results = self._search_cars_regular(
                filters=search_filters,
                limit=limit
            )

            # Format results
            formatted_results = self._format_car_search_results(search_results)

            return formatted_results

        except Exception as e:
            return f"Error en búsqueda de catálogo: {e}"
