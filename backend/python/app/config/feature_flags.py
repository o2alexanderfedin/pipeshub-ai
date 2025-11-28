"""
Feature flag system for Hupyy verification integration.

Uses MongoDB to store and manage feature flags dynamically.
Supports:
- Boolean flags (enabled/disabled)
- Numeric flags (weights, thresholds)
- String flags (configuration values)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel, Field


class FeatureFlagModel(BaseModel):
    """Pydantic model for feature flag."""

    name: str = Field(..., description="Feature flag name")
    value: Union[bool, int, float, str] = Field(..., description="Flag value")
    description: str = Field(default="", description="Flag description")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")


@dataclass
class VerificationFlags:
    """
    Verification feature flags.

    These flags control verification behavior:
    - verification_enabled: Master switch for verification
    - verification_ranking_weight: Weight in ranking formula (0.0 to 0.15)
    - verification_top_k: Number of top results to verify (5-10)
    - verification_timeout_seconds: Timeout for verification (150s default)
    - verification_cache_ttl: Cache TTL in seconds (86400 default)
    """

    verification_enabled: bool = False
    verification_ranking_weight: float = 0.0
    verification_top_k: int = 5
    verification_timeout_seconds: int = 150
    verification_cache_ttl: int = 86400


class FeatureFlagService:
    """Service for managing feature flags in MongoDB."""

    COLLECTION_NAME = "feature_flags"

    def __init__(
        self, database: AsyncIOMotorDatabase, logger: Optional[logging.Logger] = None
    ) -> None:
        """
        Initialize feature flag service.

        Args:
            database: MongoDB database instance
            logger: Optional logger instance
        """
        self.db = database
        self.collection = database[self.COLLECTION_NAME]
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    async def create(
        cls, mongo_uri: str, database_name: str, logger: Optional[logging.Logger] = None
    ) -> "FeatureFlagService":
        """
        Create FeatureFlagService instance.

        Args:
            mongo_uri: MongoDB connection URI
            database_name: Database name
            logger: Optional logger instance

        Returns:
            Initialized FeatureFlagService
        """
        client = AsyncIOMotorClient(mongo_uri)
        database = client[database_name]
        service = cls(database, logger)

        # Initialize default flags if they don't exist
        await service.initialize_default_flags()

        return service

    async def initialize_default_flags(self) -> None:
        """Initialize default verification flags if they don't exist."""
        default_flags = {
            "verification_enabled": {
                "value": False,
                "description": "Master switch for Hupyy verification",
            },
            "verification_ranking_weight": {
                "value": 0.0,
                "description": "Weight for verification scores in ranking (0.0-0.15)",
            },
            "verification_top_k": {
                "value": 5,
                "description": "Number of top results to verify (5-10)",
            },
            "verification_timeout_seconds": {
                "value": 150,
                "description": "Timeout for Hupyy API calls (seconds)",
            },
            "verification_cache_ttl": {
                "value": 86400,
                "description": "Cache TTL in seconds (24 hours)",
            },
        }

        for name, config in default_flags.items():
            exists = await self.collection.find_one({"name": name})
            if not exists:
                await self.collection.insert_one(
                    {"name": name, "value": config["value"], "description": config["description"]}
                )
                self.logger.info(f"✅ Initialized feature flag: {name}")

    async def get_flag(self, name: str, default: Any = None) -> Any:
        """
        Get feature flag value.

        Args:
            name: Flag name
            default: Default value if flag not found

        Returns:
            Flag value or default
        """
        try:
            flag = await self.collection.find_one({"name": name})
            if flag:
                return flag.get("value", default)
            return default
        except Exception as e:
            self.logger.error(f"Failed to get flag {name}: {str(e)}")
            return default

    async def set_flag(
        self, name: str, value: Union[bool, int, float, str], description: str = ""
    ) -> bool:
        """
        Set feature flag value.

        Args:
            name: Flag name
            value: Flag value
            description: Optional description

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.collection.update_one(
                {"name": name}, {"$set": {"value": value, "description": description}}, upsert=True
            )
            self.logger.info(f"✅ Set feature flag: {name} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set flag {name}: {str(e)}")
            return False

    async def get_verification_flags(self) -> VerificationFlags:
        """
        Get all verification-related flags.

        Returns:
            VerificationFlags instance with current values
        """
        return VerificationFlags(
            verification_enabled=await self.get_flag("verification_enabled", False),
            verification_ranking_weight=await self.get_flag("verification_ranking_weight", 0.0),
            verification_top_k=await self.get_flag("verification_top_k", 5),
            verification_timeout_seconds=await self.get_flag("verification_timeout_seconds", 150),
            verification_cache_ttl=await self.get_flag("verification_cache_ttl", 86400),
        )

    async def update_verification_flags(
        self,
        verification_enabled: Optional[bool] = None,
        verification_ranking_weight: Optional[float] = None,
        verification_top_k: Optional[int] = None,
        verification_timeout_seconds: Optional[int] = None,
        verification_cache_ttl: Optional[int] = None,
    ) -> bool:
        """
        Update verification flags.

        Args:
            verification_enabled: Enable/disable verification
            verification_ranking_weight: Ranking weight (0.0-0.15)
            verification_top_k: Number of results to verify
            verification_timeout_seconds: Timeout in seconds
            verification_cache_ttl: Cache TTL in seconds

        Returns:
            True if all updates successful, False otherwise
        """
        updates = {
            "verification_enabled": verification_enabled,
            "verification_ranking_weight": verification_ranking_weight,
            "verification_top_k": verification_top_k,
            "verification_timeout_seconds": verification_timeout_seconds,
            "verification_cache_ttl": verification_cache_ttl,
        }

        success = True
        for name, value in updates.items():
            if value is not None:
                result = await self.set_flag(name, value)
                success = success and result

        return success

    async def list_all_flags(self) -> Dict[str, Any]:
        """
        List all feature flags.

        Returns:
            Dictionary of flag names to values
        """
        try:
            flags = {}
            async for flag in self.collection.find():
                flags[flag["name"]] = flag.get("value")
            return flags
        except Exception as e:
            self.logger.error(f"Failed to list flags: {str(e)}")
            return {}
