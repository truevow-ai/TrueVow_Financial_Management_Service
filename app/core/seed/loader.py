"""YAML seed data loader"""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.logging import logger

# Import models
from app.modules.general_ledger.models.legal_entity_model import LegalEntity
from app.modules.general_ledger.models.book_model import Book, BookType
from app.modules.general_ledger.models.dimension_model import Dimension, DimensionValue


class SeedLoader:
    """Load seed data from YAML files"""
    
    def __init__(self, session: AsyncSession, user_id: Optional[str] = None):
        self.session = session
        self.user_id = user_id  # For created_by/updated_by fields
    
    async def load_from_file(self, file_path: Path) -> Dict[str, Any]:
        """Load seed data from YAML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"Loaded seed data from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading seed file {file_path}: {e}")
            raise
    
    async def load_entities(self, entities_data: list):
        """Load entities and their books from seed data"""
        logger.info(f"Loading {len(entities_data)} entities")
        
        entity_map = {}  # Track created entities by code
        
        for entity_data in entities_data:
            code = entity_data.get("code")
            name = entity_data.get("name")
            country = entity_data.get("country")
            functional_currency = entity_data.get("functional_currency")
            books = entity_data.get("books", [])
            
            if not all([code, name, country, functional_currency]):
                logger.warning(f"Skipping incomplete entity data: {entity_data}")
                continue
            
            # Check if entity already exists
            result = await self.session.execute(
                select(LegalEntity).where(LegalEntity.code == code)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.info(f"Entity {code} already exists, skipping")
                entity_map[code] = existing
                continue
            
            # Create entity
            entity = LegalEntity(
                code=code,
                name=name,
                country=country,
                functional_currency=functional_currency,
                is_active=True,
                created_by=self.user_id,
                updated_by=self.user_id
            )
            self.session.add(entity)
            await self.session.flush()  # Get the ID
            entity_map[code] = entity
            logger.info(f"Created entity: {code} - {name}")
            
            # Create books for this entity
            for book_type_str in books:
                try:
                    book_type = BookType[book_type_str]
                except KeyError:
                    logger.warning(f"Invalid book type: {book_type_str}, skipping")
                    continue
                
                # Check if book already exists
                result = await self.session.execute(
                    select(Book).where(
                        Book.legal_entity_id == entity.id,
                        Book.book_type == book_type
                    )
                )
                existing_book = result.scalar_one_or_none()
                
                if existing_book:
                    logger.info(f"Book {book_type.value} for {code} already exists, skipping")
                    continue
                
                # Create book
                book = Book(
                    legal_entity_id=entity.id,
                    book_type=book_type,
                    name=f"{name} - {book_type.value}",
                    is_active=True,
                    created_by=self.user_id,
                    updated_by=self.user_id
                )
                self.session.add(book)
                logger.info(f"Created book: {code} - {book_type.value}")
        
        await self.session.flush()
        logger.info(f"Loaded {len(entity_map)} entities with their books")
    
    async def load_dimensions(self, dimensions_data: dict):
        """Load dimensions and their values from seed data"""
        logger.info(f"Loading dimensions: {list(dimensions_data.keys())}")
        
        for dimension_code, values_list in dimensions_data.items():
            if not isinstance(values_list, list):
                logger.warning(f"Dimension {dimension_code} values must be a list, skipping")
                continue
            
            # Check if dimension already exists
            result = await self.session.execute(
                select(Dimension).where(Dimension.code == dimension_code)
            )
            dimension = result.scalar_one_or_none()
            
            if not dimension:
                # Create dimension
                dimension = Dimension(
                    code=dimension_code,
                    name=dimension_code.replace("_", " ").title(),
                    description=f"{dimension_code} dimension",
                    created_by=self.user_id,
                    updated_by=self.user_id
                )
                self.session.add(dimension)
                await self.session.flush()
                logger.info(f"Created dimension: {dimension_code}")
            
            # Create dimension values
            for value_data in values_list:
                if isinstance(value_data, dict):
                    value_code = value_data.get("code") or value_data.get("value")
                    value_name = value_data.get("name") or value_code
                else:
                    # Simple string value
                    value_code = str(value_data).upper().replace(" ", "_")
                    value_name = str(value_data)
                
                if not value_code:
                    continue
                
                # Check if value already exists
                result = await self.session.execute(
                    select(DimensionValue).where(
                        DimensionValue.dimension_code == dimension_code,
                        DimensionValue.value_code == value_code
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    logger.debug(f"Dimension value {dimension_code}.{value_code} already exists, skipping")
                    continue
                
                # Create dimension value
                dim_value = DimensionValue(
                    dimension_code=dimension_code,
                    value_code=value_code,
                    value_name=value_name,
                    created_by=self.user_id,
                    updated_by=self.user_id
                )
                self.session.add(dim_value)
                logger.debug(f"Created dimension value: {dimension_code}.{value_code} = {value_name}")
        
        await self.session.flush()
        logger.info("Loaded all dimensions and values")
    
    async def load_coa_template(self, coa_data: dict):
        """Load chart of accounts template"""
        # TODO: Implement CoA loading when needed
        logger.info("Loading chart of accounts template")
        pass
    
    async def load_all(self, seed_file_path: Path):
        """Load all seed data from YAML file"""
        data = await self.load_from_file(seed_file_path)
        
        # Load entities (and their books)
        if "entities" in data:
            await self.load_entities(data["entities"])
        
        # Load dimensions
        if "dimensions" in data:
            await self.load_dimensions(data["dimensions"])
        
        # Load CoA template
        if "coa_template" in data:
            await self.load_coa_template(data["coa_template"])
        
        # Commit all changes
        await self.session.commit()
        logger.info("Seed data loading completed successfully")
