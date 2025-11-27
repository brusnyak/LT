"""
Async Scheduler
Utility for running async functions in a scheduler
"""

import asyncio
import logging
import threading
from typing import Callable, Any, Dict, Optional
from functools import wraps

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

class AsyncScheduler:
    """
    Scheduler that can run async functions
    """
    
    def __init__(self):
        """Initialize the async scheduler"""
        self.scheduler = BackgroundScheduler()
        self.loop = None
        self._thread = None
        self._running = False
    
    def start(self):
        """Start the scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("AsyncScheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("AsyncScheduler shut down")
    
    def add_job(self, func, *args, **kwargs):
        """
        Add a job to the scheduler
        
        Args:
            func: Function to run (can be async)
            *args: Arguments to pass to scheduler.add_job
            **kwargs: Keyword arguments to pass to scheduler.add_job
        
        Returns:
            Job: The scheduled job
        """
        # Extract function arguments if they exist
        func_args = kwargs.pop('args', ())
        func_kwargs = kwargs.pop('kwargs', {})
        
        # Wrap the function to handle async functions
        @wraps(func)
        def wrapper():
            try:
                result = func(*func_args, **func_kwargs)
                # If the function returns a coroutine, run it in the event loop
                if asyncio.iscoroutine(result):
                    self._run_coroutine(result)
            except Exception as e:
                logger.error(f"Error in scheduled job {func.__name__}: {e}")
        
        # Add the wrapped function to the scheduler
        return self.scheduler.add_job(wrapper, *args, **kwargs)

    def _run_coroutine(self, coro):
        """
        Run a coroutine in the event loop
        
        Args:
            coro: Coroutine to run
        """
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in the main thread with a running loop
                asyncio.create_task(coro)
            else:
                # We're in a different thread, use a new event loop
                asyncio.run(coro)
        except RuntimeError:
            # No event loop in this thread, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(coro)