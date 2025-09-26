# ℹ️ Info Agent Test Guide

## 🎯 **Overview**

This guide covers the three distinct information request scenarios designed to test Alfred's information gathering capabilities across different business types and question categories.

## ℹ️ **Info Agent Prompt Structure**

The info agent uses a focused prompt designed for gathering specific information:

### **Key Dynamic Variables:**
- `user_name`: Customer name
- `business_name`: Business name  
- `context_summary`: Short description of the request
- `question_type`: Type of information requested (availability, hours, price, status, policies)
- `context`: Free-form details to clarify the question
- `notes`: Any preferences or additional information

## 🍽️ **Scenario 1: Restaurant Availability Check**

### **Test Command:**
```bash
python3 test_with_real_phone_info.py restaurant
```

### **Scenario Details:**
- **Business**: Bella Vista Restaurant
- **Customer**: Maria Schmidt
- **Question Type**: availability
- **Context**: Looking for dinner reservation for 2 people next weekend
- **Date**: January 27, 2024
- **Party Size**: 2 people
- **Notes**: Anniversary dinner - prefer romantic table

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of Maria Schmidt. I'd like to ask a quick question about check availability for 2 people on January 27, 2024."

### **Role for Jonas:**
🎭 **Play as a restaurant host/hostess handling availability inquiries**
- Ask for more details about the reservation request
- Check availability for the specific date and party size
- Provide available time slots
- Ask about special occasion preferences
- Confirm information clearly

---

## 🏨 **Scenario 2: Hotel Policy Inquiry**

### **Test Command:**
```bash
python3 test_with_real_phone_info.py hotel
```

### **Scenario Details:**
- **Business**: Grand Hotel Berlin
- **Customer**: James Anderson
- **Question Type**: policies
- **Context**: Need to understand cancellation and pet policies for business trip
- **Notes**: Traveling with small dog and need flexible booking for work schedule

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of James Anderson. I'd like to ask a quick question about check policies."

### **Role for Jonas:**
🎭 **Play as a hotel receptionist handling policy inquiries**
- Explain hotel cancellation policies
- Provide information about pet policies
- Discuss flexible booking options
- Explain any fees or restrictions
- Confirm all policy details

---

## 💇 **Scenario 3: Salon Pricing Inquiry**

### **Test Command:**
```bash
python3 test_with_real_phone_info.py hairdresser
```

### **Scenario Details:**
- **Business**: Style Studio Hair Salon
- **Customer**: Sarah Johnson
- **Question Type**: price
- **Context**: Need pricing for haircut and highlights for job interview preparation
- **Notes**: First time client, want to know package deals and individual service prices

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of Sarah Johnson. I'd like to ask a quick question about check pricing information."

### **Role for Jonas:**
🎭 **Play as a salon receptionist handling pricing inquiries**
- Provide detailed pricing for haircut and highlights
- Explain package deals and individual service prices
- Discuss first-time client promotions
- Provide information about appointment booking
- Confirm all pricing details

---

## 🚀 **Running Tests**

### **Individual Test:**
```bash
# Test specific scenario
python3 test_with_real_phone_info.py restaurant
python3 test_with_real_phone_info.py hotel
python3 test_with_real_phone_info.py hairdresser
```

### **All Scenarios (Sequential):**
```bash
# Run all tests with 30-second delays
python3 test_with_real_phone_info.py
```

**Note**: Sequential tests run all 3 info request scenarios with 30-second delays between calls. Complete each call before the next one starts.

## 🎭 **Role-Playing Tips for Jonas**

### **Restaurant Host:**
- Be helpful with availability inquiries
- Ask for specific details (date, time, party size)
- Check the reservation system for available slots
- Offer suggestions for special occasions
- Confirm all details clearly

### **Hotel Receptionist:**
- Be knowledgeable about hotel policies
- Provide clear information about cancellation terms
- Explain pet policies and any restrictions
- Discuss flexible booking options
- Confirm all policy details

### **Salon Receptionist:**
- Be friendly with pricing inquiries
- Provide detailed service pricing
- Explain package deals and promotions
- Discuss appointment scheduling
- Confirm all pricing information

## 📊 **Testing Objectives**

### **For Each Scenario, Test:**
1. **Clear Question**: Does Alfred clearly state what information is needed?
2. **Professional Opening**: Is the opening concise and clear?
3. **Context Handling**: Does Alfred provide relevant context when asked?
4. **Progressive Confirmation**: Does Alfred confirm information as it's received?
5. **Complete Summary**: Does Alfred provide a clear summary at the end?

## 🔍 **What to Look For**

### **Success Indicators:**
- ✅ Alfred opens with clear, concise introduction
- ✅ Context summary is provided appropriately
- ✅ Question type is clearly communicated
- ✅ Additional context is shared when relevant
- ✅ Information is confirmed progressively
- ✅ Clear summary provided at the end

### **Potential Issues:**
- ❌ Unclear question or context
- ❌ Missing relevant details
- ❌ Not confirming information received
- ❌ Incomplete summary
- ❌ Unprofessional tone

## 📋 **Expected Conversation Flow**

### **Typical Flow:**
1. **Opening**: Alfred identifies himself and states the information request
2. **Clarification**: Business asks for more details
3. **Details**: Alfred provides context and specific requirements
4. **Information Gathering**: Business provides the requested information
5. **Confirmation**: Alfred confirms key details as they're received
6. **Summary**: Alfred provides complete summary of information
7. **Closing**: Polite ending with thanks

### **Example Complete Flow:**
```
Alfred: "Hello, this is Alfred calling on behalf of Maria Schmidt. I'd like to ask a quick question about check availability for 2 people on January 27, 2024."

Host: "Sure, what time were you looking for?"

Alfred: "We're looking for dinner reservation for 2 people next weekend. It's for an anniversary dinner and we'd prefer a romantic table."

Host: "I can see we have availability at 7:00 PM and 8:30 PM on January 27th. Both would work well for a romantic dinner."

Alfred: "Just to confirm, you said: January 27th at 7:00 PM or 8:30 PM for 2 people, both suitable for an anniversary dinner. Is that correct?"

Host: "Yes, that's correct."

Alfred: "Thank you very much for your help."
```

## 🎉 **Expected Outcomes**

Each scenario should demonstrate Alfred's ability to:
1. **Clearly state** what information is needed
2. **Provide context** when asked for clarification
3. **Confirm information** progressively as received
4. **Handle business responses** professionally
5. **Summarize key information** clearly before ending

## 🔄 **Agent Selection Verification**

The info agent should be correctly selected:
- **Agent ID**: `agent_9901k61ftvcaenxa1644kgz4ea9p`
- **Agent Name**: "info"
- **Phone Assignment**: Phone number should be assigned to info agent before call

## 📊 **Dynamic Variables Generated**

Perfect alignment with your new prompt structure:

```
user_name: Maria Schmidt
business_name: Bella Vista Restaurant
context_summary: check availability for 2 people on January 27, 2024
question_type: availability
context: Looking for dinner reservation for 2 people next weekend
notes: Anniversary dinner - prefer romantic table
```

This comprehensive testing approach ensures Alfred can handle diverse real-world information request scenarios effectively! 🚀
