"""CLI commands for seeding database"""
import asyncio
from pathlib import Path
from typing import Optional
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine
from app.core.seed.loader import SeedLoader
from app.core.logging import logger


async def seed_step_with_retry(step_name: str, step_fn, max_retries: int = 3):
    """Execute a single seed step with retry on connection reset"""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[{step_name}] Attempt {attempt}/{max_retries}")
            await step_fn()
            logger.info(f"[{step_name}] SUCCESS")
            return
        except (ConnectionResetError, OSError, asyncio.CancelledError) as e:
            logger.warning(f"[{step_name}] Connection error on attempt {attempt}: {e}")
            if attempt < max_retries:
                # Dispose engine and wait before retry
                await engine.dispose()
                wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                logger.info(f"[{step_name}] Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"[{step_name}] FAILED after {max_retries} attempts")
                raise
        except Exception as e:
            logger.error(f"[{step_name}] Non-retryable error: {e}")
            raise


async def seed_database(seed_file: str = "app/core/seed/seed_data.yaml", user_id: Optional[str] = None, step: Optional[str] = None):
    """Seed database from YAML file with step-by-step execution"""
    seed_path = Path(seed_file)
    
    if not seed_path.exists():
        logger.error(f"Seed file not found: {seed_path}")
        return
    
    # Load seed data (await the coroutine)
    loader = SeedLoader(None, user_id=user_id)
    data = await loader.load_from_file(seed_path)
    
    # Define steps
    steps = {
        "legal_entity": lambda: _seed_entities(data, user_id),
        "book": lambda: _seed_books(data, user_id),
        "dimension": lambda: _seed_dimensions(data, user_id),
        "period": lambda: _seed_periods(data, user_id),
    }
    
    if step:
        if step not in steps:
            logger.error(f"Unknown step: {step}. Available: {', '.join(steps.keys())}")
            return
        await seed_step_with_retry(step, steps[step])
    else:
        # Run all steps in sequence
        for step_name, step_fn in steps.items():
            await seed_step_with_retry(step_name, step_fn)


async def _seed_entities(data, user_id):
    """Seed legal entities"""
    async with AsyncSessionLocal() as session:
        loader = SeedLoader(session, user_id=user_id)
        await loader.load_entities(data["entities"])
        await session.commit()


async def _seed_books(data, user_id):
    """Seed books"""
    async with AsyncSessionLocal() as session:
        loader = SeedLoader(session, user_id=user_id)
        await loader.load_books(data["books"])
        await session.commit()


async def _seed_dimensions(data, user_id):
    """Seed dimensions"""
    async with AsyncSessionLocal() as session:
        loader = SeedLoader(session, user_id=user_id)
        if "dimensions" in data:
            await loader.load_dimensions(data["dimensions"])
        await session.commit()


async def _seed_periods(data, user_id):
    """Seed accounting periods"""
    async with AsyncSessionLocal() as session:
        loader = SeedLoader(session, user_id=user_id)
        if "periods" in data:
            await loader.load_periods(data["periods"])
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_database())
