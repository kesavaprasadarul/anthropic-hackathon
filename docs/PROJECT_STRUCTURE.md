# 📁 Project Structure

## 🏗️ **Overview**

This document describes the organized structure of the Jarvis Calling Module project, which has been restructured for better maintainability and clarity.

## 📂 **Directory Structure**

```
/Users/jonas/anthropic-hackathon/
├── 📁 calling_module/           # Core calling module package
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── contracts.py             # Data structures and contracts
│   ├── input_adapter.py         # Input validation and normalization
│   ├── observability.py         # Logging and metrics
│   ├── outbound_caller.py       # ElevenLabs SDK integration
│   ├── payload_builder.py       # Agent payload construction
│   ├── postcall_handler.py      # Post-call processing
│   ├── router.py                # Main API router
│   └── tool_webhook.py          # Mid-call tool webhooks
│
├── 📁 tests/                    # All test files
│   ├── __init__.py
│   ├── test_calling_module.py   # Unit tests with mocks
│   ├── test_with_real_phone.py  # Reservation agent tests
│   ├── test_with_real_phone_reschedule.py  # Reschedule agent tests
│   ├── test_with_real_phone_cancel.py      # Cancel agent tests
│   ├── test_with_real_phone_info.py        # Info agent tests
│   └── test_postcall_handler.py # Postcall handler tests
│
├── 📁 docs/                     # Documentation
│   ├── PROJECT_STRUCTURE.md     # This file
│   ├── CANCEL_AGENT_TEST_GUIDE.md
│   ├── INFO_AGENT_TEST_GUIDE.md
│   ├── TEST_CALL_GUIDE.md
│   ├── TEST_SCENARIOS_GUIDE.md
│   ├── DYNAMIC_PHONE_ASSIGNMENT.md
│   └── POSTCALL_HANDLER_EXPLANATION.md
│
├── 📁 venv/                     # Virtual environment
│
├── 📄 main.py                   # FastAPI application entry point
├── 📄 requirements.txt          # Python dependencies
├── 📄 env.example               # Environment variables template
├── 📄 README.md                 # Project overview
└── 📄 PHONE_NUMBERS.md          # Phone number configuration
```

## 🧪 **Test Organization**

### **Unit Tests (`test_calling_module.py`)**
- Mock-based tests for individual components
- Input validation tests
- Error handling scenarios
- Integration tests with mocked dependencies

### **Real Phone Tests**
- **`test_with_real_phone.py`** - Reservation agent scenarios
- **`test_with_real_phone_reschedule.py`** - Reschedule agent scenarios  
- **`test_with_real_phone_cancel.py`** - Cancel agent scenarios
- **`test_with_real_phone_info.py`** - Info agent scenarios

### **Specialized Tests**
- **`test_postcall_handler.py`** - Postcall webhook simulation

## 📚 **Documentation Organization**

### **Agent-Specific Guides**
- `CANCEL_AGENT_TEST_GUIDE.md` - Cancel agent testing scenarios
- `INFO_AGENT_TEST_GUIDE.md` - Info agent testing scenarios

### **General Testing Guides**
- `TEST_CALL_GUIDE.md` - General testing instructions
- `TEST_SCENARIOS_GUIDE.md` - Scenario overview

### **Technical Documentation**
- `DYNAMIC_PHONE_ASSIGNMENT.md` - Phone number assignment logic
- `POSTCALL_HANDLER_EXPLANATION.md` - Postcall processing

## 🚀 **Running Tests**

### **From Project Root:**
```bash
# Unit tests
python -m pytest tests/test_calling_module.py

# Real phone tests
python tests/test_with_real_phone.py restaurant
python tests/test_with_real_phone_reschedule.py restaurant
python tests/test_with_real_phone_cancel.py restaurant
python tests/test_with_real_phone_info.py restaurant

# Postcall handler tests
python tests/test_postcall_handler.py
```

### **From Tests Directory:**
```bash
cd tests

# Unit tests
python -m pytest test_calling_module.py

# Real phone tests
python test_with_real_phone.py restaurant
python test_with_real_phone_reschedule.py restaurant
python test_with_real_phone_cancel.py restaurant
python test_with_real_phone_info.py restaurant

# Postcall handler tests
python test_postcall_handler.py
```

## 🎯 **Benefits of This Structure**

### **✅ Organization**
- Clear separation of concerns
- Easy to find specific files
- Logical grouping of related functionality

### **✅ Maintainability**
- Tests are centralized and organized
- Documentation is easily accessible
- Import paths are consistent

### **✅ Scalability**
- Easy to add new test scenarios
- Simple to extend documentation
- Clear structure for new contributors

### **✅ Professional Standards**
- Follows Python project conventions
- Matches industry best practices
- Clean and professional appearance

## 📋 **File Responsibilities**

### **Core Module (`calling_module/`)**
- Business logic and API integration
- Data structures and contracts
- Configuration management
- Observability and logging

### **Tests (`tests/`)**
- Unit testing with mocks
- Integration testing with real APIs
- End-to-end scenario testing
- Postcall webhook simulation

### **Documentation (`docs/`)**
- Agent-specific testing guides
- Technical implementation details
- Usage instructions and examples
- Project structure and organization

### **Root Files**
- Application entry point (`main.py`)
- Dependencies (`requirements.txt`)
- Configuration template (`env.example`)
- Project overview (`README.md`)

This structure provides a clean, professional, and maintainable codebase that follows Python best practices and makes it easy for developers to understand, test, and extend the calling module functionality.
