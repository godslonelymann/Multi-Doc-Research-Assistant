from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import settings

CHUNK_SIZE_BYTES = 1024 * 1024
PDF_SIGNATURE = b"%PDF"


class FileStorageService:
    def __init__(self, upload_dir: str | None = None) -> None:
        self.upload_dir = Path(upload_dir or settings.upload_dir)
        self.max_upload_size_mb = settings.max_upload_size_mb
        self.max_upload_size_bytes = self.max_upload_size_mb * 1024 * 1024

    def ensure_upload_dir(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload: UploadFile, file_type: str) -> tuple[str, Path]:
        self.ensure_upload_dir()
        original_name = upload.filename or "uploaded-document"
        suffix = Path(original_name).suffix.lower()
        stored_name = f"{uuid4().hex}{suffix}"
        destination = self.upload_dir / stored_name

        try:
            total_bytes = 0
            first_chunk = await upload.read(CHUNK_SIZE_BYTES)
            self._validate_initial_chunk(first_chunk, file_type)

            with destination.open("wb") as output:
                if first_chunk:
                    total_bytes += len(first_chunk)
                    self._enforce_size_limit(total_bytes)
                    await run_in_threadpool(output.write, first_chunk)

                while True:
                    chunk = await upload.read(CHUNK_SIZE_BYTES)
                    if not chunk:
                        break
                    self._validate_content_chunk(chunk, file_type)
                    total_bytes += len(chunk)
                    self._enforce_size_limit(total_bytes)
                    await run_in_threadpool(output.write, chunk)
        except Exception:
            if destination.exists():
                await run_in_threadpool(destination.unlink)
            raise
        finally:
            await upload.close()

        return stored_name, destination

    def _validate_initial_chunk(self, chunk: bytes, file_type: str) -> None:
        if not chunk:
            raise ValueError("Uploaded file is empty")
        if file_type == "pdf" and not chunk.startswith(PDF_SIGNATURE):
            raise ValueError("Uploaded PDF does not have a valid PDF signature")
        if file_type == "txt" and b"\x00" in chunk:
            raise ValueError("Uploaded TXT file appears to be binary data")

    def _validate_content_chunk(self, chunk: bytes, file_type: str) -> None:
        if file_type == "txt" and b"\x00" in chunk:
            raise ValueError("Uploaded TXT file appears to be binary data")

    def _enforce_size_limit(self, total_bytes: int) -> None:
        if total_bytes > self.max_upload_size_bytes:
            raise ValueError(f"Uploaded file exceeds the {self.max_upload_size_mb} MB size limit")
