"""
Payload builder for browser automation tasks.

This module handles the construction of task instructions and metadata
for browser-use agent execution.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from contracts import BrowserTask, Intent, InfoType, ReservePayload, InfoPayload, RecommendPayload

logger = logging.getLogger(__name__)


class PayloadBuilder:
    """Builds browser automation task payloads and instructions."""
    
    def build_task_instructions(self, task: BrowserTask) -> str:
        """
        Build detailed task instructions for the browser agent.
        
        Args:
            task: Validated browser automation task
            
        Returns:
            str: Formatted task instructions
        """
        if task.intent == Intent.RESERVE:
            return self._build_reservation_instructions(task)
        elif task.intent == Intent.INFO:
            return self._build_info_instructions(task)
        elif task.intent == Intent.RECOMMEND:
            return self._build_recommend_instructions(task)
        else:
            raise ValueError(f"Unsupported intent: {task.intent}")
    
    def build_agent_metadata(self, task: BrowserTask) -> Dict[str, Any]:
        """
        Build metadata for the browser agent configuration.
        
        Args:
            task: Validated browser automation task
            
        Returns:
            Dict: Agent configuration metadata
        """
        return {
            "max_steps": task.policy.max_steps,
            "use_vision": task.policy.use_vision,
            "take_screenshots": task.policy.take_screenshots,
            "max_failures": task.policy.max_failures,
            "business_name": task.business.name,
            "business_website": task.business.website,
            "user_name": task.user.name,
            "intent": task.intent.value,
            "locale": task.locale,
            "timestamp": datetime.now().isoformat()
        }
    
    def _build_reservation_instructions(self, task: BrowserTask) -> str:
        """Build instructions for reservation tasks."""
        payload: ReservePayload = task.payload
        business = task.business
        user = task.user
        
        # Build contact information
        contact_info = []
        if user.email:
            contact_info.append(f"Email: {user.email}")
        if user.phone:
            contact_info.append(f"Phone: {user.phone}")
        contact_str = ", ".join(contact_info)
        
        # Build optional details
        optional_details = []
        if payload.duration_minutes:
            optional_details.append(f"- Duration: {payload.duration_minutes} minutes")
        if payload.notes:
            optional_details.append(f"- Special Requests: {payload.notes}")
        if payload.preferences:
            optional_details.append(f"- Preferences: {payload.preferences}")
        if payload.budget:
            optional_details.append(f"- Budget: ${payload.budget}")
        
        optional_str = "\n".join(optional_details) if optional_details else ""
        
        instructions = f"""
Make a restaurant reservation at {business.name} ({business.website})

**Critical Instructions:**
- Navigate to {business.website} and verify it's the correct restaurant. Ensure that {business.name} and {business.website} match.
- Confirm that this is a restaurant and not another service
- Check if restaurant is open on {payload.date} during {payload.time_window_start}-{payload.time_window_end}. If not return status "restaurant_closed"
- Look for online reservation system (booking form, OpenTable, Resy, etc.)
- If the website explicitly states that no reservations are possible or only via phone, abort the process and return status "no_bookings"
- Fill out reservation form with provided details. Use the same language for filling out the form as the companies website
- If the website does not provide a reservation system, search up the restaurant on OpenTable and setup the reservation there. Do not use a website other than OpenTable. If you cannot find the restaurant on OpenTable, abort the process and return status "no_bookings".
- Take screenshots at key steps for evidence
- If any step fails, provide specific error details
- Return the reservation details as booking_details

**Reservation Details:**
- Name: {user.name}
- Date: {payload.date}
- Time Window: {payload.time_window_start} - {payload.time_window_end}
- Party Size: {payload.party_size}
- Contact: {contact_str}
{optional_str}

**Success Criteria:**
- Reservation must be confirmed with a confirmation number or reference
- All reservation details must match. The groups size must be permmitted by the restaurant and the date and time must match
- All provided details must be accurately entered
"""
        
        logger.debug(f"Built reservation instructions for {business.name}")
        return instructions.strip()
    
    def _build_recommend_instructions(self, task: BrowserTask) -> str:
        """Build instructions for restaurant recommendation tasks."""
        payload: RecommendPayload = task.payload
        
        instructions = f"""Find food recommendations in {payload.area} for this user query: {payload.user_query}

STEPS:
1. Search for highly rated restaurants in {payload.area}
2. Filter results to match user preferences: {payload.user_query}
3. Verify price range is within {payload.budget} euros per person
4. Find the 2 best matches with current information
5. Extract key details: name, cuisine, price range, rating, hours

REQUIREMENTS:
- Must match user preferences exactly
- Price must be within {payload.budget}€ budget
- Provide 2 top recommendations
- Include specific details (hours, location, prices)
- Response must be under 6 sentences
- Take screenshots of restaurant pages for evidence"""
        
        logger.debug(f"Built recommendation instructions for area: {payload.area}, budget: {payload.budget}")
        return instructions.strip()
    
    def _build_info_instructions(self, task: BrowserTask) -> str:
        """Build instructions for information request tasks."""
        payload: InfoPayload = task.payload
        business = task.business
        
        # Build context information
        context_parts = []
        if payload.context_date:
            context_parts.append(f"- Context Date: {payload.context_date}")
        if payload.context_time:
            context_parts.append(f"- Context Time: {payload.context_time}")
        
        context_str = "\n".join(context_parts) if context_parts else ""
        
        # Map info types to specific instructions
        info_type_instructions = {
            InfoType.OPENING_HOURS: "Find the restaurant's operating hours, including any special holiday hours or closures",
            InfoType.PRICING: "Find menu prices, price ranges, or any pricing information available",
            InfoType.DIETARY_INFORMATION: "Find information about dietary options (vegetarian, vegan, gluten-free, allergen info)",
            InfoType.AVAILABILITY: "Check current availability for reservations or walk-ins"
        }
        
        specific_instruction = info_type_instructions.get(
            payload.info_type, 
            f"Find information about {payload.info_type.value}"
        )
        
        instructions = f"""
Get {payload.info_type.value} information from {business.name} ({business.website})

**Instructions:**
- Navigate to {business.website}
- Confirm that this is a restaurant and not another service
- {specific_instruction}
- Look for relevant information in menus, about pages, contact pages, or reservation systems
- Extract and format the requested information clearly and accurately
- Take screenshots of relevant information sources
- If information is not available on the website, clearly state this
{context_str}

**Information Requirements:**
- Information must be current and accurate
- Include specific details when available (hours, prices, options)
- Note the source of the information (which page/section)
- If information varies by date/time, include those details
- Output the information in a short and concise manner
"""
        
        logger.debug(f"Built info instructions for {business.name}, type: {payload.info_type}")
        return instructions.strip()

    def get_return_format_schema(self, intent: Intent) -> Dict[str, Any]:
        """
        Get the expected return format schema for validation.
        
        Args:
            intent: The task intent type
            
        Returns:
            Dict: JSON schema for expected return format
        """
        if intent == Intent.RESERVE:
            return {
                "type": "object",
                "required": ["success", "error_type"],
                "properties": {
                    "success": {"type": "boolean"},
                    "confirmation_details": {"type": "string"},
                    "confirmed_date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$"},
                    "confirmed_time": {"type": "string", "pattern": r"^\d{2}:\d{2}$"},
                    "party_size": {"type": "integer", "minimum": 1},
                    "error_type": {"type": "string"},
                    "screenshots_taken": {"type": "array", "items": {"type": "string"}},
                    "next_steps": {"type": "string"}
                }
            }
        elif intent == Intent.INFO:
            return {
                "type": "object", 
                "required": ["info_found", "data"],
                "properties": {
                    "info_found": {"type": "boolean"},
                    "data": {"type": "string"},
                    "source_section": {"type": "string"},
                    "last_updated": {"type": "string"},
                    "additional_context": {"type": "string"},
                    "screenshots_taken": {"type": "array", "items": {"type": "string"}},
                    "limitations": {"type": "string"}
                }
            }
        elif intent == Intent.RECOMMEND:
            return {
                "type": "object",
                "required": ["recommendations_found", "recommendations"],
                "properties": {
                    "recommendations_found": {"type": "boolean"},
                    "recommendations": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "cuisine_type": {"type": "string"},
                                "price_range": {"type": "string"},
                                "rating": {"type": "string"},
                                "location": {"type": "string"},
                                "hours": {"type": "string"},
                                "website": {"type": "string"}
                            },
                            "required": ["name", "cuisine_type", "price_range"]
                        }
                    },
                    "search_area": {"type": "string"},
                    "budget_range": {"type": "string"},
                    "screenshots_taken": {"type": "array", "items": {"type": "string"}},
                    "limitations": {"type": "string"}
                }
            }
        else:
            raise ValueError(f"No schema defined for intent: {intent}")