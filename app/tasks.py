"""
Background task utilities for FastAPI
"""
import asyncio
import logging
from typing import Any, Callable, Optional

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


async def run_background_task(
    func: Callable,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Wrapper for running background tasks with error handling.
    
    This function can be used to wrap any async function that should
    run in the background, providing centralized error handling.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    """
    try:
        await func(*args, **kwargs)
    except Exception as e:
        logger.error(
            f"Background task {func.__name__} failed: {e}",
            exc_info=True,
        )


def add_background_task(
    tasks: BackgroundTasks,
    func: Callable,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Add a background task with error handling wrapper.
    
    This is a convenience function that wraps the task in error handling
    before adding it to BackgroundTasks.
    
    Args:
        tasks: FastAPI BackgroundTasks instance
        func: Async function to execute in background
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    """
    tasks.add_task(run_background_task, func, *args, **kwargs)


class TaskQueue:
    """
    Simple in-memory task queue for background operations.
    
    This can be used for queuing tasks that need to be processed
    asynchronously, with optional retry logic.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize task queue.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self._queue: asyncio.Queue = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._max_workers = max_workers
        self._running = False
    
    async def start(self):
        """Start the task queue workers"""
        if self._running:
            return
        
        self._running = True
        self._workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self._max_workers)
        ]
        logger.info(f"Task queue started with {self._max_workers} workers")
    
    async def stop(self):
        """Stop the task queue workers"""
        if not self._running:
            return
        
        self._running = False
        
        # Wait for all tasks to complete
        await self._queue.join()
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("Task queue stopped")
    
    async def enqueue(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ):
        """
        Add a task to the queue.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        await self._queue.put((func, args, kwargs))
    
    async def _worker(self, name: str):
        """Worker coroutine that processes tasks from the queue"""
        logger.info(f"Task queue worker {name} started")
        
        while self._running:
            try:
                # Wait for a task with timeout
                func, args, kwargs = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
                
                try:
                    await run_background_task(func, *args, **kwargs)
                finally:
                    self._queue.task_done()
                    
            except asyncio.TimeoutError:
                # Timeout is expected, continue loop
                continue
            except Exception as e:
                logger.error(f"Worker {name} error: {e}", exc_info=True)
                if not self._queue.empty():
                    self._queue.task_done()
        
        logger.info(f"Task queue worker {name} stopped")


# Global task queue instance (optional)
_task_queue: Optional[TaskQueue] = None


def get_task_queue() -> TaskQueue:
    """Get or create singleton task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue

