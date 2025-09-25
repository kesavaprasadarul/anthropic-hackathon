# Test Scenarios Guide - Alfred Reservation Agent

## 🎯 **Overview**

This guide covers the three distinct reservation scenarios designed to test Alfred's capabilities across different booking types and business contexts.

## 🍽️ **Scenario 1: Restaurant Reservation**

### **Test Command:**
```bash
python3 test_with_real_phone.py restaurant
```

### **Scenario Details:**
- **Business**: Bella Vista Restaurant
- **Customer**: Maria Schmidt
- **Date**: January 20, 2024 at 19:00-21:00
- **Party Size**: 2 people
- **Occasion**: Anniversary dinner for 5th wedding anniversary
- **Budget**: €60–100 per person
- **Duration**: 2 hours (typical for restaurants)

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of Maria Schmidt. I'd like to make a reservation at Bella Vista Restaurant. The request is: Anniversary dinner for our 5th wedding anniversary. We're looking for availability in these windows: January 20, 2024 — 07:00 PM to 09:00 PM. It's for 2 people. Anniversary dinner for our 5th wedding anniversary Budget range: €60–100 per person Could you let me know what works?"

### **Role for Jonas:**
🎭 **Play as a restaurant host/hostess taking reservations**
- Ask about dietary restrictions
- Suggest wine pairings
- Confirm table preferences (window, quiet area)
- Ask for contact information for confirmation

---

## 🏨 **Scenario 2: Hotel Booking**

### **Test Command:**
```bash
python3 test_with_real_phone.py hotel
```

### **Scenario Details:**
- **Business**: Grand Hotel Berlin
- **Customer**: James Anderson
- **Check-in**: February 15, 2024 at 15:00-17:00
- **Guests**: 2 people
- **Purpose**: Business trip for tech conference
- **Requirements**: Quiet room with good WiFi
- **Budget**: €120–180 per night
- **Duration**: Multi-night stay

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of James Anderson. I'd like to make a reservation at Grand Hotel Berlin. The request is: Business trip for tech conference, need quiet room with good WiFi. We're looking for availability in these windows: February 15, 2024 — 03:00 PM to 05:00 PM. It's for 2 people. Business trip for tech conference, need quiet room with good WiFi Budget range: €120–180 per night Could you let me know what works?"

### **Role for Jonas:**
🎭 **Play as a hotel receptionist taking bookings**
- Ask about length of stay
- Suggest room types (business suite, executive floor)
- Confirm amenities (WiFi, breakfast, parking)
- Ask about check-out date

---

## 💇 **Scenario 3: Hairdresser Appointment**

### **Test Command:**
```bash
python3 test_with_real_phone.py hairdresser
```

### **Scenario Details:**
- **Business**: Style Studio Hair Salon
- **Customer**: Sarah Johnson
- **Date**: January 25, 2024 at 14:00-16:00
- **Services**: Haircut and highlights
- **Purpose**: Job interview next week
- **Budget**: €80–120 total
- **Duration**: 2 hours (typical for cut + highlights)

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of Sarah Johnson. I'd like to make a reservation at Style Studio Hair Salon. The request is: Haircut and highlights for job interview next week. We're looking for availability in these windows: January 25, 2024 — 02:00 PM to 04:00 PM. It's for 1 people. Haircut and highlights for job interview next week Budget range: €80–120 total Could you let me know what works?"

### **Role for Jonas:**
🎭 **Play as a salon receptionist booking appointments**
- Ask about specific services needed
- Suggest stylists based on hair type
- Confirm consultation time
- Ask about hair history/previous treatments


## 🚀 **Running Tests**

### **Individual Test:**
```bash
# Test specific scenario
python3 test_with_real_phone.py restaurant
python3 test_with_real_phone.py hotel
python3 test_with_real_phone.py hairdresser
```

### **All Scenarios (Sequential):**
```bash
# Run all tests with 30-second delays
python3 test_with_real_phone.py
```

**Note**: Sequential tests run all 3 reservation scenarios with 30-second delays between calls. Complete each call before the next one starts.

## 🎭 **Role-Playing Tips for Jonas**

### **Restaurant Host:**
- Be warm and welcoming
- Ask about special occasions
- Suggest appetizers or wine
- Confirm dietary restrictions

### **Hotel Receptionist:**
- Be professional and efficient
- Ask about check-in/out dates
- Suggest room upgrades
- Confirm amenities and services

### **Salon Receptionist:**
- Be friendly and knowledgeable
- Ask about hair history
- Suggest appropriate services
- Confirm stylist preferences


## 📊 **Testing Objectives**

### **For Each Scenario, Test:**
1. **Natural Conversation Flow** - Does Alfred sound natural?
2. **Context Awareness** - Does Alfred understand the booking type?
3. **Information Handling** - Does Alfred provide correct details?
4. **Professional Tone** - Is Alfred polite and professional?
5. **Dynamic Variables** - Are all variables correctly populated?
6. **Confirmation Process** - Does Alfred confirm details properly?

## 🔍 **What to Look For**

### **Success Indicators:**
- ✅ Alfred introduces himself properly
- ✅ All dynamic variables are correctly used
- ✅ Context is appropriate for booking type
- ✅ Professional and polite tone
- ✅ Proper confirmation process
- ✅ Handles business responses naturally

### **Potential Issues:**
- ❌ Missing or incorrect dynamic variables
- ❌ Inappropriate context for booking type
- ❌ Unprofessional tone
- ❌ Confusion about booking details
- ❌ Poor handling of business responses

## 📋 **Test Results Tracking**

After each test, note:
- **Call Duration**: How long did the conversation last?
- **Success**: Was the booking/inquiry handled successfully?
- **Issues**: Any problems or confusion?
- **Improvements**: What could be better?
- **Dynamic Variables**: Were all variables used correctly?

## 🎉 **Expected Outcomes**

Each scenario should demonstrate Alfred's ability to:
1. **Adapt to different business types** (restaurant vs hotel vs salon)
2. **Use appropriate context** for each booking type
3. **Handle varying budgets and requirements**
4. **Maintain professional conversation flow**
5. **Properly confirm booking details**

This comprehensive testing approach ensures Alfred can handle diverse real-world booking scenarios effectively! 🚀
