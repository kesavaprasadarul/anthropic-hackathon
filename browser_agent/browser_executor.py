import asyncio
import logging
import time
from typing import Any, Optional, Dict, List
from datetime import datetime
import json

from browser_use import Agent, ChatGoogle, Browser
from dotenv import load_dotenv

from contracts import BrowserTask, BrowserAutomationResult, Evidence, Status, NextAction, BrowserUseResult
from payload_builder import PayloadBuilder
from result_processor import ResultProcessor
from observability import get_logger, log_execution_metrics

load_dotenv()

logger = get_logger(__name__)


class BrowserExecutionError(Exception):
    """Raised when browser execution fails."""
    pass


class BrowserExecutor:
    """Executes browser automation tasks using browser-use agent."""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the browser executor.
        
        Args:
            model_name: LLM model to use for browser automation
        """
        self.model = ChatGoogle(model=model_name)
        self.payload_builder = PayloadBuilder()
        self.result_processor = ResultProcessor()
        logger.info(f"Initialized BrowserExecutor with model: {model_name}")
    
    async def execute(self, task: BrowserTask) -> str:
        """
        Execute a browser automation task.
        
        Args:
            task: Validated browser automation task
            
        Returns:
            BrowserAutomationResult: Execution result with evidence
        """
        start_time = time.time()
        task_id = task.idempotency_key or f"task_{int(start_time)}"
        
        logger.info(f"Starting browser automation task {task_id} for {task.business.name}")
        
        try:
            # Build task instructions
            instructions = self.payload_builder.build_task_instructions(task)
            metadata = self.payload_builder.build_agent_metadata(task)
            
            logger.debug(f"Built task instructions for {task_id}")
            
            # Create browser agent
            agent = Agent(
                task=instructions,
                browser=Browser(headless=False),
                llm=self.model,
                output_model_schema=BrowserUseResult,
                use_vision=task.policy.use_vision,
                max_failures=task.policy.max_failures,
                generate_gif=False,  # Disable GIF generation for performance
            )
            
            # Execute the automation
            history = await self._execute_with_monitoring(agent, task, task_id)

            final_result = history.final_result()
            parsed: BrowserUseResult = BrowserUseResult.model_validate_json(final_result)
            # Return the final result directly
            return parsed.model_dump_json()
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Browser execution failed: {str(e)}"
            logger.error(f"Task {task_id} failed: {error_msg}")
            
            # Log failure metrics
            log_execution_metrics(
                task_id=task_id,
                business_name=task.business.name,
                intent=task.intent.value,
                execution_time=execution_time,
                steps_taken=0,
                success=False,
                error=error_msg
            )
            
            return self._create_error_result(error_msg, execution_time)
    
    async def _execute_with_monitoring(self, agent: Agent, task: BrowserTask, task_id: str) -> Any:
        """
        Execute agent with monitoring and logging.
        
        Args:
            agent: Browser-use agent instance
            task: Browser automation task
            task_id: Unique task identifier
            
        Returns:
            Execution history from browser agent
        """
        logger.info(f"Executing browser agent for task {task_id}")
        
        try:
            # Execute with timeout based on policy
            timeout_seconds = task.policy.max_steps * 10  # Rough estimate: 10 seconds per step
            
            history = await asyncio.wait_for(
                agent.run(max_steps=task.policy.max_steps),
                timeout=timeout_seconds
            )            
            # Log detailed execution steps
            if hasattr(history, 'history') and history.history:
                self._log_execution_steps(history.history, task_id)
            return history
            
        except asyncio.TimeoutError:
            error_msg = f"Browser automation timed out after {timeout_seconds} seconds"
            logger.error(f"Task {task_id}: {error_msg}")
            raise BrowserExecutionError(error_msg)
        
        except Exception as e:
            error_msg = f"Browser agent execution failed: {str(e)}"
            logger.error(f"Task {task_id}: {error_msg}")
            raise BrowserExecutionError(error_msg)
    
    def _extract_evidence(self, history: Any, start_time: float) -> Evidence:
        """
        Extract evidence from browser automation history.
        
        Args:
            history: Browser agent execution history
            start_time: Task start timestamp
            
        Returns:
            Evidence: Collected evidence from execution
        """
        screenshots = []
        steps_taken = 0
        browsing_summary_parts = []
        
        if hasattr(history, 'history') and history.history:
            steps_taken = len(history.history)
            
            for i, step in enumerate(history.history):
                # Collect screenshot information
                if hasattr(step, 'screenshot') and step.screenshot:
                    screenshots.append(f"Step {i+1}: {step.action}")
                
                # Build browsing summary
                if hasattr(step, 'action') and step.action:
                    action_summary = str(step.action)[:100] + "..." if len(str(step.action)) > 100 else str(step.action)
                    browsing_summary_parts.append(f"Step {i+1}: {action_summary}")
        
        browsing_summary = " | ".join(browsing_summary_parts) if browsing_summary_parts else "No steps recorded"
        duration_seconds = time.time() - start_time
        
        return Evidence(
            screenshots=screenshots,
            browsing_summary=browsing_summary,
            steps_taken=steps_taken,
            duration_seconds=duration_seconds
        )
    
    def _create_result_from_history(self, history: Any, task: BrowserTask, evidence: Evidence) -> BrowserAutomationResult:
        """
        Create automation result directly from browser agent history.
        
        Args:
            history: Browser agent execution history
            task: Original browser automation task
            evidence: Collected execution evidence
            
        Returns:
            BrowserAutomationResult: Standardized result based on history
        """
        try:
            # The history object has methods, not properties
            success = False
            extracted_content = ""
            
            # Method 1: Call is_successful() method if it exists
            if hasattr(history, 'is_successful') and callable(getattr(history, 'is_successful')):
                success = history.is_successful()
                logger.info(f"Method 1 - is_successful(): {success}")
            
            # Method 2: Call extracted_content() method or access property
            if hasattr(history, 'extracted_content'):
                extracted_attr = getattr(history, 'extracted_content')
                if callable(extracted_attr):
                    extracted_content = extracted_attr()
                else:
                    extracted_content = extracted_attr
                logger.info(f"Method 2 - extracted_content type: {type(extracted_content)}, length: {len(extracted_content) if extracted_content else 0}")
            
            # Method 3: Try to iterate over history to get the last result if needed
            if not extracted_content:
                try:
                    for item in history:
                        if hasattr(item, 'extracted_content') and item.extracted_content:
                            extracted_content = item.extracted_content
                            if hasattr(item, 'success') and item.success is not None:
                                success = item.success
                    logger.info(f"Method 3 - iteration success: {success}, content type: {type(extracted_content)}")
                except Exception as e:
                    logger.info(f"Method 3 - iteration failed: {e}")
            
            # Convert list to string if needed
            if isinstance(extracted_content, list):
                # Join list items, filtering out empty ones and taking the most meaningful content
                meaningful_content = [item for item in extracted_content if item and item.strip() and not item.startswith('🔗')]
                if meaningful_content:
                    extracted_content = meaningful_content[-1]  # Take the last meaningful result
                else:
                    extracted_content = ' '.join(str(item) for item in extracted_content if item)
                logger.info(f"Converted list to string - final length: {len(extracted_content)}")
            
            logger.info(f"Final processing - success: {success}, content length: {len(extracted_content) if extracted_content else 0}")
            
            # Determine status based on success
            if success:
                status = Status.COMPLETED
                next_action = NextAction.ADD_TO_CALENDAR if task.intent.value == 'reserve' else NextAction.NONE
            else:
                # Failed - determine specific failure type based on content
                content_lower = str(extracted_content).lower() if extracted_content else ''
                
                if 'keine reservierungen' in content_lower or 'no reservations possible' in content_lower:
                    status = Status.NO_AVAILABILITY
                    next_action = NextAction.SWITCH_CHANNEL
                elif 'closed' in content_lower or 'sunday' in content_lower:
                    status = Status.RESTAURANT_CLOSED
                    next_action = NextAction.RETRY_LATER
                elif 'not available' in content_lower or 'unavailable' in content_lower:
                    status = Status.NO_AVAILABILITY
                    next_action = NextAction.REQUEST_USER_INPUT
                elif 'website' in content_lower and ('access' in content_lower or 'cannot' in content_lower):
                    status = Status.NO_WEBSITE
                    next_action = NextAction.SWITCH_CHANNEL
                else:
                    status = Status.ERROR
                    next_action = NextAction.RETRY_LATER
            
            # Use extracted content as the main message
            message = extracted_content if extracted_content else "Browser automation completed"
            
            return BrowserAutomationResult(
                status=status,
                message=message,
                next_action=next_action,
                core_artifact=None,  # Keep empty as requested
                evidence=evidence,
                error_reason=None,
                missing_fields=None
            )
                
        except Exception as e:
            logger.error(f"Error creating result from history: {str(e)}")
            return BrowserAutomationResult(
                status=Status.ERROR,
                message=f"Failed to process automation results: {str(e)}",
                next_action=NextAction.RETRY_LATER,
                core_artifact=None,
                evidence=evidence,
                error_reason=str(e),
                missing_fields=None
            )
    
    def _log_execution_steps(self, steps: List[Any], task_id: str) -> None:
        """
        Log detailed execution steps for debugging.
        
        Args:
            steps: List of execution steps
            task_id: Task identifier
        """
        logger.debug(f"=== EXECUTION HISTORY FOR TASK {task_id} ===")
        logger.debug(f"Total steps executed: {len(steps)}")
        
        for i, step in enumerate(steps):
            logger.debug(f"--- Step {i+1} ---")
            if hasattr(step, 'action'):
                logger.debug(f"Action: {step.action}")
            if hasattr(step, 'result'):
                result_str = str(step.result)[:200] + "..." if len(str(step.result)) > 200 else str(step.result)
                logger.debug(f"Result: {result_str}")
            if hasattr(step, 'screenshot') and step.screenshot:
                logger.debug("Screenshot taken: Yes")
            if hasattr(step, 'error') and step.error:
                logger.debug(f"Error: {step.error}")
        
        logger.debug("=====================================")
    
    def _create_error_result(self, error_message: str, execution_time: float) -> BrowserAutomationResult:
        """
        Create a standardized error result.
        
        Args:
            error_message: Error description
            execution_time: Time spent before failure
            
        Returns:
            BrowserAutomationResult: Error result
        """
        # Determine status based on error type
        status = Status.ERROR
        next_action = NextAction.RETRY_LATER
        
        if "timeout" in error_message.lower():
            status = Status.TIMEOUT
            next_action = NextAction.RETRY_LATER
        elif "website" in error_message.lower() or "connection" in error_message.lower():
            status = Status.NO_WEBSITE
            next_action = NextAction.SWITCH_CHANNEL
        
        return BrowserAutomationResult(
            status=status,
            message=f"Browser automation failed: {error_message}",
            next_action=next_action,
            evidence=Evidence(
                screenshots=[],
                browsing_summary=f"Execution failed: {error_message}",
                steps_taken=0,
                duration_seconds=execution_time
            ),
            error_reason=error_message
        )


class MockBrowserExecutor(BrowserExecutor):
    """Mock browser executor for testing purposes."""
    
    def __init__(self):
        """Initialize mock executor without real dependencies."""
        self.payload_builder = PayloadBuilder()
        logger.info("Initialized MockBrowserExecutor for testing")
    
    async def execute(self, task: BrowserTask) -> BrowserAutomationResult:
        """
        Mock execution that returns predictable results for testing.
        
        Args:
            task: Browser automation task
            
        Returns:
            BrowserAutomationResult: Mock result
        """
        start_time = time.time()
        task_id = task.idempotency_key or f"mock_task_{int(start_time)}"
        
        logger.info(f"Mock execution for task {task_id}")
        
        # Simulate execution time
        await asyncio.sleep(0.1)
        
        # Create mock evidence
        evidence = Evidence(
            screenshots=["mock_screenshot_1.png", "mock_screenshot_2.png"],
            browsing_summary="Mock execution completed successfully",
            steps_taken=3,
            duration_seconds=time.time() - start_time
        )
        
        # Return mock successful result
        return BrowserAutomationResult(
            status=Status.COMPLETED,
            message="Mock browser automation completed",
            next_action=NextAction.ADD_TO_CALENDAR,
            evidence=evidence
        ), {"success": True, "confirmation_details": "Mock reservation confirmed"}