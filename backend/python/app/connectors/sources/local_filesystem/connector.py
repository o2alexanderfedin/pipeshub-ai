"""Local Filesystem Connector for PipesHub."""

import asyncio
import hashlib
import mimetypes
import os
import uuid
from logging import Logger
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import chardet
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.config.configuration_service import ConfigurationService
from app.config.constants.arangodb import (
    Connectors,
    MimeTypes,
    OriginTypes,
)
from app.config.constants.http_status_code import HttpStatusCode
from app.connectors.core.base.connector.connector_service import BaseConnector
from app.connectors.core.base.data_processor.data_source_entities_processor import (
    DataSourceEntitiesProcessor,
)
from app.connectors.core.base.data_store.data_store import DataStoreProvider
from app.connectors.core.base.sync_point.sync_point import (
    SyncDataPointType,
    SyncPoint,
    generate_record_sync_point_key,
)
from app.connectors.core.registry.connector_builder import (
    AuthField,
    ConnectorBuilder,
    DocumentationLink,
)
from app.connectors.sources.local_filesystem.common.apps import LocalFilesystemApp
from app.connectors.sources.local_filesystem.watcher import (
    FileChange,
    FileChangeType,
    LocalFileSystemWatcher,
)
from app.models.blocks import Block, BlockType, DataFormat
from app.models.entities import (
    FileRecord,
    Record,
    RecordGroup,
    RecordGroupType,
    RecordType,
)
from app.models.permission import EntityType, Permission, PermissionType
from app.utils.time_conversion import get_epoch_timestamp_in_ms

# Extension to MIME type mapping
EXTENSION_TO_MIME = {
    ".md": MimeTypes.MARKDOWN,
    ".txt": MimeTypes.PLAIN_TEXT,
    ".py": MimeTypes.PLAIN_TEXT,
    ".js": MimeTypes.PLAIN_TEXT,
    ".ts": MimeTypes.PLAIN_TEXT,
    ".json": MimeTypes.JSON,
    ".yaml": MimeTypes.YAML,
    ".yml": MimeTypes.YAML,
    ".html": MimeTypes.HTML,
    ".css": MimeTypes.PLAIN_TEXT,
    ".tsx": MimeTypes.PLAIN_TEXT,
    ".jsx": MimeTypes.PLAIN_TEXT,
    ".go": MimeTypes.PLAIN_TEXT,
    ".rs": MimeTypes.PLAIN_TEXT,
    ".java": MimeTypes.PLAIN_TEXT,
    ".c": MimeTypes.PLAIN_TEXT,
    ".cpp": MimeTypes.PLAIN_TEXT,
    ".h": MimeTypes.PLAIN_TEXT,
    ".hpp": MimeTypes.PLAIN_TEXT,
    ".rb": MimeTypes.PLAIN_TEXT,
    ".php": MimeTypes.PLAIN_TEXT,
    ".sh": MimeTypes.PLAIN_TEXT,
    ".bash": MimeTypes.PLAIN_TEXT,
    ".zsh": MimeTypes.PLAIN_TEXT,
    ".toml": MimeTypes.PLAIN_TEXT,
    ".ini": MimeTypes.PLAIN_TEXT,
    ".cfg": MimeTypes.PLAIN_TEXT,
    ".conf": MimeTypes.PLAIN_TEXT,
    ".xml": MimeTypes.XML,
    ".svg": MimeTypes.PLAIN_TEXT,
    ".pdf": MimeTypes.PDF,
}


@ConnectorBuilder("Local Filesystem")\
    .in_group("Local Filesystem")\
    .with_auth_type("NONE")\
    .with_description("Sync files from a local filesystem directory")\
    .with_categories(["Storage", "Development"])\
    .configure(lambda builder: builder
        .with_icon("/assets/icons/connectors/filesystem.svg")
        .with_realtime_support(True)
        .add_documentation_link(DocumentationLink(
            "Local Filesystem Setup",
            "https://docs.pipeshub.com/connectors/local-filesystem",
            "docs"
        ))
        .add_documentation_link(DocumentationLink(
            'Pipeshub Documentation',
            'https://docs.pipeshub.com/connectors/local-filesystem/setup',
            'pipeshub'
        ))
        .with_redirect_uri("", False)
        .add_auth_field(AuthField(
            name="watch_path",
            display_name="Watch Path",
            placeholder="/data/local-files",
            description="The directory path to watch for files (inside the container)",
            field_type="TEXT",
            max_length=1024,
            min_length=1
        ))
        .add_auth_field(AuthField(
            name="debounce_seconds",
            display_name="Debounce Seconds",
            placeholder="1.0",
            description="Seconds to wait before processing file changes (default: 1.0)",
            field_type="TEXT",
            max_length=10,
            min_length=1,
            required=False
        ))
        .with_scheduled_config(True, 60)
        .with_sync_strategies(["SCHEDULED", "MANUAL"])
    )\
    .build_decorator()
class LocalFilesystemConnector(BaseConnector):
    """
    Connector for synchronizing files from a local filesystem directory.
    Supports real-time file watching and incremental syncs.
    """

    def __init__(
        self,
        logger: Logger,
        data_entities_processor: DataSourceEntitiesProcessor,
        data_store_provider: DataStoreProvider,
        config_service: ConfigurationService,
    ) -> None:
        super().__init__(
            LocalFilesystemApp(),
            logger,
            data_entities_processor,
            data_store_provider,
            config_service
        )

        self.connector_name = Connectors.LOCAL_FILESYSTEM

        # Initialize sync point
        self._create_sync_points()

        # Configuration
        self.watch_path: str = ""
        self.debounce_seconds: float = 1.0
        self.batch_size = 100
        self.watcher: Optional[LocalFileSystemWatcher] = None

        # Content extraction configuration
        self.content_extraction_enabled: bool = True
        self.max_file_size_mb: int = 10
        self.encoding_fallback: str = "utf-8"

        # Supported file extensions
        self.supported_extensions: Set[str] = {
            ".md", ".txt", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
            ".html", ".css", ".tsx", ".jsx", ".go", ".rs", ".java", ".c",
            ".cpp", ".h", ".hpp", ".rb", ".php", ".sh", ".bash", ".zsh",
            ".toml", ".ini", ".cfg", ".conf", ".xml", ".svg", ".pdf"
        }

        # Directories to ignore
        self.ignore_directories: List[str] = [
            "node_modules", ".git", "__pycache__", "venv", ".venv",
            "env", ".env", ".idea", ".vscode", "dist", "build",
            "target", ".next", ".nuxt", "coverage", ".pytest_cache",
            ".mypy_cache", ".tox", "eggs", "*.egg-info"
        ]

    def _create_sync_points(self) -> None:
        """Initialize sync points for tracking changes."""
        self.record_sync_point = SyncPoint(
            connector_name=self.connector_name,
            org_id=self.data_entities_processor.org_id,
            sync_data_point_type=SyncDataPointType.RECORDS,
            data_store_provider=self.data_store_provider
        )

    async def init(self) -> bool:
        """
        Initialize the Local Filesystem connector.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Try org-specific config first, then fall back to general config
            config = await self.config_service.get_config(
                f"/services/connectors/localfilesystem/config/{self.data_entities_processor.org_id}"
            ) or await self.config_service.get_config(
                "/services/connectors/localfilesystem/config"
            )

            if not config:
                self.logger.warning("Local Filesystem configuration not found, using defaults.")
                config = {}

            auth_config = config.get("auth", {})

            # Use default if watch_path is empty or not provided
            self.watch_path = auth_config.get("watch_path", "") or "/data/local-files"
            debounce_str = auth_config.get("debounce_seconds", "1.0")
            try:
                self.debounce_seconds = float(debounce_str)
            except ValueError:
                self.debounce_seconds = 1.0

            # Read content extraction configuration
            content_config = config.get("content_extraction", {})
            self.content_extraction_enabled = content_config.get("enabled", True)
            self.max_file_size_mb = content_config.get("max_file_size_mb", 10)
            self.encoding_fallback = content_config.get("encoding_fallback", "utf-8")

            self.logger.info(
                f"Content extraction: enabled={self.content_extraction_enabled}, "
                f"max_size_mb={self.max_file_size_mb}"
            )

            if not os.path.exists(self.watch_path):
                self.logger.error(f"Watch path does not exist: {self.watch_path}")
                return False

            if not os.path.isdir(self.watch_path):
                self.logger.error(f"Watch path is not a directory: {self.watch_path}")
                return False

            self.logger.info(f"Local Filesystem connector initialized for: {self.watch_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Local Filesystem connector: {e}", exc_info=True)
            return False

    async def test_connection_and_access(self) -> bool:
        """
        Test the connection to the local filesystem.

        Returns:
            True if connection test was successful, False otherwise
        """
        try:
            if not os.path.exists(self.watch_path):
                self.logger.error(f"Watch path does not exist: {self.watch_path}")
                return False

            if not os.access(self.watch_path, os.R_OK):
                self.logger.error(f"Watch path is not readable: {self.watch_path}")
                return False

            # Try to list files
            files = os.listdir(self.watch_path)
            self.logger.info(f"Connection test successful. Found {len(files)} items in {self.watch_path}")
            return True

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}", exc_info=True)
            return False

    async def get_signed_url(self, record: Record) -> Optional[str]:
        """
        Get a URL for accessing the file (returns local file path).

        Args:
            record: The record to get URL for

        Returns:
            The file path or None
        """
        if record.external_record_id:
            return f"file://{record.external_record_id}"
        return None

    async def stream_record(self, record: Record) -> StreamingResponse:
        """
        Stream the content of a local file.

        Args:
            record: The record to stream

        Returns:
            StreamingResponse with the file content

        Raises:
            HTTPException if file cannot be streamed
        """
        file_path = record.external_record_id
        self.logger.info(f"🔍 Stream request for record {record.id}")
        self.logger.info(f"🔍 File path: {file_path}")
        self.logger.info(f"🔍 Record name: {record.record_name}")

        if not file_path:
            self.logger.error(f"❌ No file path in record {record.id}")
            raise HTTPException(
                status_code=HttpStatusCode.NOT_FOUND.value,
                detail="File not found"
            )

        exists = os.path.exists(file_path)
        self.logger.info(f"🔍 File exists: {exists}")

        if not exists:
            # Log parent directory contents to debug
            parent_dir = os.path.dirname(file_path)
            if os.path.exists(parent_dir):
                contents = os.listdir(parent_dir)[:10]
                self.logger.error(f"❌ File not found: {file_path}")
                self.logger.error(f"❌ Parent dir {parent_dir} contains: {contents}")
            else:
                self.logger.error(f"❌ Parent directory doesn't exist: {parent_dir}")
            raise HTTPException(
                status_code=HttpStatusCode.NOT_FOUND.value,
                detail="File not found"
            )

        if not os.access(file_path, os.R_OK):
            raise HTTPException(
                status_code=HttpStatusCode.FORBIDDEN.value,
                detail="File not readable"
            )

        def file_iterator():
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk

        mime_type = record.mime_type if record.mime_type else "application/octet-stream"
        filename = os.path.basename(file_path)

        return StreamingResponse(
            file_iterator(),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    def _generate_file_id(self, file_path: str) -> str:
        """Generate a unique ID for a file based on its path."""
        return hashlib.sha256(file_path.encode()).hexdigest()[:32]

    def _get_mime_type(self, file_path: str) -> str:
        """Get the MIME type for a file."""
        ext = Path(file_path).suffix.lower()
        if ext in EXTENSION_TO_MIME:
            mime_enum = EXTENSION_TO_MIME[ext]
            return mime_enum.value if hasattr(mime_enum, 'value') else str(mime_enum)

        # Fallback to mimetypes library
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"

    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should be processed based on extension and path."""
        path_obj = Path(file_path)

        # Check extension
        if path_obj.suffix.lower() not in self.supported_extensions:
            return False

        # Check for ignored directories
        parts = path_obj.parts
        for directory in self.ignore_directories:
            if directory in parts:
                return False

        return True

    def _get_relative_path(self, file_path: str) -> str:
        """Get the path relative to the watch directory."""
        return os.path.relpath(file_path, self.watch_path)

    def _get_parent_group_id(self, file_path: str) -> str:
        """Get the parent directory as a group ID."""
        rel_path = self._get_relative_path(file_path)
        parent_dir = os.path.dirname(rel_path)
        if parent_dir and parent_dir != ".":
            return f"dir/{parent_dir}"
        return "dir/root"

    async def _read_file_content(
        self,
        file_path: str,
        max_size_bytes: Optional[int] = None
    ) -> Optional[str]:
        """
        Read file content with encoding detection and size limits.

        Args:
            file_path: Absolute path to file
            max_size_bytes: Skip files larger than this (default from config)

        Returns:
            File content as string, or None if unreadable

        Behavior:
            - Returns None if file > max_size_bytes (logs info, not error)
            - Detects encoding using chardet
            - Falls back to UTF-8 if detection fails
            - Catches decode errors and returns None with warning
            - Catches permission errors and returns None with warning
            - Catches other exceptions as errors
        """
        if max_size_bytes is None:
            max_size_bytes = self.max_file_size_mb * 1024 * 1024

        try:
            # Check file size first
            file_size = os.path.getsize(file_path)
            if file_size > max_size_bytes:
                self.logger.info(
                    f"Skipping content for large file: {file_path} "
                    f"({file_size} bytes > {max_size_bytes} bytes limit)"
                )
                return None

            # Read a chunk for encoding detection
            with open(file_path, 'rb') as f:
                # Read up to 1MB for encoding detection
                chunk_size = min(file_size, 1024 * 1024)
                raw_data = f.read(chunk_size)

            # Detect encoding
            detection = chardet.detect(raw_data)
            encoding = detection.get('encoding') or self.encoding_fallback
            confidence = detection.get('confidence', 0.0)

            self.logger.debug(
                f"Detected encoding for {file_path}: {encoding} "
                f"(confidence: {confidence:.2f})"
            )

            # Read file with detected encoding
            try:
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    content = f.read()
                return content

            except UnicodeDecodeError:
                # Try fallback encoding
                self.logger.warning(
                    f"Cannot decode {file_path} with {encoding}, "
                    f"trying fallback {self.encoding_fallback}"
                )
                with open(file_path, 'r', encoding=self.encoding_fallback, errors='replace') as f:
                    content = f.read()
                return content

        except FileNotFoundError:
            self.logger.warning(f"File disappeared during read: {file_path}")
            return None

        except PermissionError:
            self.logger.warning(f"Permission denied reading: {file_path}")
            return None

        except Exception as e:
            self.logger.error(
                f"Unexpected error reading {file_path}: {e}",
                exc_info=True
            )
            return None

    async def _create_file_record(
        self,
        file_path: str,
        existing_record: Optional[FileRecord] = None
    ) -> Tuple[FileRecord, List[Permission]]:
        """Create a FileRecord from a file path."""
        path_obj = Path(file_path)
        stat = os.stat(file_path)

        # Calculate relative path from watch_path for database storage
        try:
            relative_path = str(path_obj.relative_to(Path(self.watch_path)))
        except ValueError:
            # File outside watch_path (shouldn't happen)
            self.logger.warning(f"File {file_path} outside watch path {self.watch_path}")
            relative_path = file_path

        # Extract extension safely
        extension = path_obj.suffix.lstrip('.') if path_obj.suffix else ""

        # Read file content with size limit and encoding detection
        content = None
        if self.content_extraction_enabled:
            max_size_bytes = self.max_file_size_mb * 1024 * 1024
            content = await self._read_file_content(file_path, max_size_bytes)

        # Generate unique ID
        file_id = existing_record.id if existing_record else str(uuid.uuid4())
        version = (existing_record.version + 1) if existing_record else 0

        record = FileRecord(
            id=file_id,
            record_name=path_obj.name,
            external_record_id=file_path,
            connector_name=self.connector_name,
            record_type=RecordType.FILE,
            record_group_type=RecordGroupType.KB,
            external_record_group_id=self._get_parent_group_id(file_path),
            origin=OriginTypes.CONNECTOR,
            org_id=self.data_entities_processor.org_id,
            source_updated_at=int(stat.st_mtime * 1000),
            updated_at=get_epoch_timestamp_in_ms(),
            version=version,
            external_revision_id=str(int(stat.st_mtime)),
            weburl=f"file://{file_path}",
            mime_type=self._get_mime_type(file_path),
            extension=extension,  # Ensure always populated
            path=relative_path,  # Set path field
            is_file=True,
            size_in_bytes=stat.st_size,
            inherit_permissions=True,
        )

        # Populate block_containers with file content
        if content is not None:
            text_block = Block(
                type=BlockType.TEXT,
                format=DataFormat.TXT,
                data=content
            )
            record.block_containers.blocks.append(text_block)
            self.logger.debug(
                f"Content loaded: {path_obj.name} ({len(content)} chars, "
                f"{stat.st_size} bytes)"
            )
        else:
            if self.content_extraction_enabled:
                self.logger.warning(
                    f"No content for {path_obj.name} (unreadable or too large)"
                )

        # Create default permissions (all users in org have read access)
        permissions = [
            Permission(
                external_id=self.data_entities_processor.org_id,
                type=PermissionType.READ,
                entity_type=EntityType.ORG
            )
        ]

        return record, permissions

    async def _scan_directory(self) -> List[str]:
        """Scan the watch directory for all supported files."""
        files = []

        for root, dirs, filenames in os.walk(self.watch_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_directories and
                      not any(d.endswith(pattern.lstrip('*')) for pattern in self.ignore_directories if '*' in pattern)]

            for filename in filenames:
                file_path = os.path.join(root, filename)
                if self._should_process_file(file_path):
                    files.append(file_path)

        return files

    async def _sync_directory_structure(self) -> None:
        """Create record groups for directory structure."""
        self.logger.info("Syncing directory structure...")

        directories = set()
        for root, dirs, _ in os.walk(self.watch_path):
            # Filter ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_directories]

            for d in dirs:
                dir_path = os.path.join(root, d)
                rel_path = self._get_relative_path(dir_path)
                directories.add(rel_path)

        # Create record groups for directories
        record_groups = []
        for dir_path in sorted(directories):
            parts = Path(dir_path).parts
            parent_id = None
            if len(parts) > 1:
                parent_id = f"dir/{'/'.join(parts[:-1])}"

            record_group = RecordGroup(
                name=Path(dir_path).name,
                org_id=self.data_entities_processor.org_id,
                external_group_id=f"dir/{dir_path}",
                description=f"Local directory: {dir_path}",
                connector_name=self.connector_name,
                group_type=RecordGroupType.KB,
                parent_external_group_id=parent_id,
                inherit_permissions=True,
            )

            # All users have read access
            permissions = [
                Permission(
                    external_id=self.data_entities_processor.org_id,
                    type=PermissionType.READ,
                    entity_type=EntityType.ORG
                )
            ]

            record_groups.append((record_group, permissions))

        if record_groups:
            await self.data_entities_processor.on_new_record_groups(record_groups)
            self.logger.info(f"Synced {len(record_groups)} directories")

    async def run_sync(self) -> None:
        """Run a full synchronization of the local filesystem."""
        try:
            self.logger.info(f"Starting Local Filesystem full sync for: {self.watch_path}")

            # Sync directory structure first
            await self._sync_directory_structure()

            # Scan for all files
            files = await self._scan_directory()
            self.logger.info(f"Found {len(files)} files to sync")

            # Process files in batches
            batch_records: List[Tuple[FileRecord, List[Permission]]] = []

            for file_path in files:
                try:
                    record, permissions = await self._create_file_record(file_path)
                    batch_records.append((record, permissions))

                    if len(batch_records) >= self.batch_size:
                        await self.data_entities_processor.on_new_records(batch_records)
                        self.logger.info(f"Processed batch of {len(batch_records)} records")
                        batch_records = []
                        await asyncio.sleep(0.1)

                except Exception as e:
                    self.logger.error(f"Error processing file {file_path}: {e}")
                    continue

            # Process remaining records
            if batch_records:
                await self.data_entities_processor.on_new_records(batch_records)
                self.logger.info(f"Processed final batch of {len(batch_records)} records")

            # Update sync point
            sync_key = generate_record_sync_point_key("localfs", "files", "global")
            await self.record_sync_point.update_sync_point(
                sync_key,
                {"timestamp": get_epoch_timestamp_in_ms()}
            )

            self.logger.info("Local Filesystem full sync completed")

        except Exception as e:
            self.logger.error(f"Error in Local Filesystem sync: {e}", exc_info=True)
            raise

    async def run_incremental_sync(self) -> None:
        """Run an incremental sync (same as full sync for filesystem)."""
        await self.run_sync()

    async def _handle_file_changes(self, changes: List[FileChange]) -> None:
        """Handle file change events from the watcher."""
        self.logger.info(f"Processing {len(changes)} file changes")

        for change in changes:
            try:
                if change.change_type == FileChangeType.CREATED:
                    if self._should_process_file(change.path):
                        record, permissions = await self._create_file_record(change.path)
                        await self.data_entities_processor.on_new_records([(record, permissions)])
                        self.logger.debug(f"Indexed new file: {change.path}")

                elif change.change_type == FileChangeType.MODIFIED:
                    if self._should_process_file(change.path):
                        # Get existing record
                        async with self.data_store_provider.transaction() as tx_store:
                            existing = await tx_store.get_record_by_external_id(
                                connector_name=self.connector_name,
                                external_id=change.path
                            )

                        record, permissions = await self._create_file_record(change.path, existing)

                        if existing:
                            await self.data_entities_processor.on_record_content_update(record)
                        else:
                            await self.data_entities_processor.on_new_records([(record, permissions)])

                        self.logger.debug(f"Updated file: {change.path}")

                elif change.change_type == FileChangeType.DELETED:
                    await self.data_entities_processor.on_record_deleted(
                        record_id=change.path
                    )
                    self.logger.debug(f"Removed file: {change.path}")

                elif change.change_type == FileChangeType.MOVED:
                    # Delete old, create new
                    await self.data_entities_processor.on_record_deleted(
                        record_id=change.path
                    )

                    if change.dest_path and self._should_process_file(change.dest_path):
                        record, permissions = await self._create_file_record(change.dest_path)
                        await self.data_entities_processor.on_new_records([(record, permissions)])

                    self.logger.debug(f"Moved file: {change.path} -> {change.dest_path}")

            except Exception as e:
                self.logger.error(f"Error handling file change {change.path}: {e}", exc_info=True)

    def start_watcher(self) -> bool:
        """Start the file system watcher for real-time updates."""
        if self.watcher and self.watcher.is_running():
            self.logger.warning("Watcher is already running")
            return True

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.watcher = LocalFileSystemWatcher(
            logger=self.logger,
            watch_path=self.watch_path,
            callback=self._handle_file_changes,
            debounce_seconds=self.debounce_seconds,
            supported_extensions=self.supported_extensions,
            ignore_directories=self.ignore_directories
        )

        return self.watcher.start(event_loop=loop)

    def stop_watcher(self) -> None:
        """Stop the file system watcher."""
        if self.watcher:
            self.watcher.stop()
            self.watcher = None

    def handle_webhook_notification(self, notification: Dict) -> None:
        """Handle webhook notifications (not used for filesystem)."""
        self.logger.info("Webhook notification received (not implemented for filesystem)")

    def cleanup(self) -> None:
        """Cleanup resources used by the connector."""
        self.logger.info("Cleaning up Local Filesystem connector")
        self.stop_watcher()

    @classmethod
    async def create_connector(
        cls,
        logger: Logger,
        data_store_provider: DataStoreProvider,
        config_service: ConfigurationService
    ) -> "BaseConnector":
        """
        Factory method to create a Local Filesystem connector instance.

        Args:
            logger: Logger instance
            data_store_provider: Data store provider for database operations
            config_service: Configuration service for accessing configuration

        Returns:
            Initialized LocalFilesystemConnector instance
        """
        data_entities_processor = DataSourceEntitiesProcessor(
            logger, data_store_provider, config_service
        )
        await data_entities_processor.initialize()

        return LocalFilesystemConnector(
            logger, data_entities_processor, data_store_provider, config_service
        )
