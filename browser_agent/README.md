# Browser Agent - Restaurant Automation System

A modular browser automation system for restaurant reservations and information retrieval, built on the browser-use framework with enterprise-grade architecture.

## Features

- **Restaurant Reservations**: Automated reservation booking with comprehensive validation
- **Business Information**: Retrieve opening hours, contact info, and availability
- **Modular Architecture**: Clean separation of concerns with protocol-based interfaces
- **Comprehensive Observability**: Structured logging, metrics, and health monitoring
- **Error Handling**: Robust error handling with detailed status reporting
- **JSON Serialization**: Full datetime and complex object serialization support

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Router        │    │ Input Adapter   │    │ Payload Builder │
│ (Public API)    │────│ (Validation)    │────│ (Instructions)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Browser Executor│────│ Result Processor│    │   Contracts     │
│ (Automation)    │    │ (Normalization) │    │ (Data Models)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────┐
                    │  Observability  │
                    │ (Logging/Metrics)│
                    └─────────────────┘
```

### Core Modules

#### `contracts.py`
Central data structures and protocol interfaces:
- **BrowserTask**: Input task definition with business info and parameters
- **BrowserAutomationResult**: Standardized result format with status, content, and evidence
- **ReservationParams**: Comprehensive reservation data model with JSON serialization
- **Status/NextAction Enums**: Standardized status vocabulary
- **Protocol Interfaces**: BrowserExecutor, InputValidator, ResultProcessor

#### `router.py`
Public API interface providing:
- **execute_automation()**: Core automation execution
- **make_reservation()**: Convenient reservation API
- **get_business_info()**: Information retrieval API
- Request coordination and component orchestration

#### `input_adapter.py`
Input validation and normalization:
- Cross-field validation (email, phone, dates)
- Business data validation
- Error result creation with detailed messages

#### `payload_builder.py`
Task instruction generation:
- Browser agent instruction building
- Metadata and context preparation
- Return format schema definition

#### `browser_executor.py`
Browser automation execution:
- browser-use agent integration
- Execution monitoring and logging
- Evidence collection and step tracking
- Mock executor for testing

#### `result_processor.py`
Result processing and normalization:
- Raw result parsing and cleanup
- Status mapping and standardization
- Booking reference extraction
- Artifact organization

#### `observability.py`
Comprehensive monitoring:
- Structured logging with PII protection
- Execution metrics and performance tracking
- Health monitoring and diagnostics
- Sensitive data redaction

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
import browser_agent
from contracts import ReservationParams, InfoType
import datetime

# Make a restaurant reservation
result = await browser_agent.make_reservation(
    business_name="Restaurant Name",
    website="https://restaurant.com",
    reservation_params=ReservationParams(
        name="John Doe",
        date=datetime.date(2025, 1, 15),
        time_window_start=datetime.time(19, 0),
        time_window_end=datetime.time(20, 0),
        email="john@example.com",
        phone_number="+1234567890",
        party_size=4,
        duration_minutes=120,
        notes="Anniversary dinner"
    )
)

print(f"Status: {result.status}")
print(f"Booking Reference: {result.booking_reference}")

# Get business information
info_result = await browser_agent.get_business_info(
    business_name="Restaurant Name",
    website="https://restaurant.com",
    info_type=InfoType.OPENING_HOURS,
    context_date=datetime.date(2025, 1, 15)
)

print(f"Opening Hours: {info_result.content}")
```

## API Reference

### Core Functions

#### `make_reservation(business_name, website, reservation_params)`
Create a restaurant reservation.

**Parameters:**
- `business_name` (str): Name of the restaurant
- `website` (str): Restaurant website URL
- `reservation_params` (ReservationParams): Reservation details

**Returns:** BrowserAutomationResult with booking status and reference

#### `get_business_info(business_name, website, info_type, context_date=None, context_time=None)`
Retrieve business information.

**Parameters:**
- `business_name` (str): Name of the business
- `website` (str): Business website URL
- `info_type` (InfoType): Type of information to retrieve
- `context_date` (date, optional): Date context for queries
- `context_time` (time, optional): Time context for queries

**Returns:** BrowserAutomationResult with requested information

### Status Types

```python
from contracts import Status

Status.SUCCESS          # Operation completed successfully
Status.FAILURE          # Operation failed
Status.PARTIAL_SUCCESS  # Partially completed
Status.ERROR           # System error occurred
Status.INVALID_INPUT   # Input validation failed
Status.NOT_SUPPORTED   # Operation not supported
Status.RATE_LIMITED    # Rate limit exceeded
Status.TIMEOUT         # Operation timed out
```

### Information Types

```python
from contracts import InfoType

InfoType.OPENING_HOURS    # Business hours
InfoType.CONTACT_INFO     # Phone, email, address
InfoType.AVAILABILITY     # Current availability
InfoType.MENU            # Menu information
InfoType.PRICING         # Pricing information
InfoType.REVIEWS         # Customer reviews
```

## Testing

Run the test suite to verify functionality:

```bash
python browser_agent_test.py
```

The test suite includes:
- Business information retrieval
- Successful reservation scenarios
- Failure case handling (closed restaurants, capacity limits)
- Error validation and reporting

## Configuration

### Environment Variables

```bash
# Optional: Configure logging level
export LOG_LEVEL=INFO

# Optional: Browser automation timeout
export BROWSER_TIMEOUT=30

# Optional: Mock mode for testing
export MOCK_BROWSER=true
```

### Logging Configuration

The system uses structured logging with automatic PII redaction:

```python
from observability import get_logger

logger = get_logger(__name__)
logger.info("Processing reservation", extra={
    "business_name": "Restaurant",
    "party_size": 4,
    "email": "***@***.com"  # Automatically redacted
})
```

## Error Handling

All operations return standardized results with comprehensive error information:

```python
result = await browser_agent.make_reservation(...)

if result.status == Status.FAILURE:
    print(f"Error: {result.content}")
    if result.errors:
        for error in result.errors:
            print(f"  - {error}")
```

## Development

### Project Structure

```
├── browser_agent.py         # Main entry point and re-exports
├── contracts.py             # Data models and interfaces
├── router.py               # Public API coordination
├── input_adapter.py        # Input validation
├── payload_builder.py      # Task instruction generation
├── browser_executor.py     # Browser automation execution
├── result_processor.py     # Result processing
├── observability.py        # Logging and monitoring
├── browser_agent_test.py   # Test suite
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

### Adding New Features

1. **Define contracts**: Add new data models to `contracts.py`
2. **Update validation**: Extend `input_adapter.py` for new inputs
3. **Build instructions**: Update `payload_builder.py` for new task types
4. **Process results**: Extend `result_processor.py` for new result formats
5. **Add API endpoints**: Update `router.py` with new public functions
6. **Add tests**: Create test cases in `browser_agent_test.py`

## Dependencies

- **browser-use (0.7.9)**: Core browser automation framework
- **pydantic**: Data validation and serialization
- **asyncio**: Asynchronous execution support

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues and questions:
1. Check the test suite for usage examples
2. Review the observability logs for debugging
3. Create an issue with reproduction steps and logs