# Try-Fit (Online Clothes Trial Booking System)

## System Activity Diagram

The diagram below maps out the end-to-end workflow between the **User** and the **System**, including email-based OTP verification, catalog browsing, and trial booking payment processing.

```mermaid
graph TD
    %% Swimlanes
    subgraph User["👤 User Swimlane"]
        Start((Start)) --> OpenWeb["Open Website"]
        OpenWeb --> Auth["Login / Sign Up"]
        Auth --> EnterEmail["Enter Email Address"]
        EnterOTP["Enter OTP Code"] --> Browse["Browse Clothes Catalog"]
        Browse --> SelectCloth["Select a Cloth"]
        SelectCloth --> ChooseDate["Choose Trial Date"]
        ChooseDate --> BookingDetails["Enter Trial Booking Details"]
        BookingDetails --> PayFee["Pay Trial Fee"]
        RetryPay["Retry Payment"] --> PayFee
        GenConf --> ViewConf["View Booking Confirmation"]
        ViewConf --> EndNode((End))
    end

    subgraph System["⚙️ System Swimlane"]
        EnterEmail --> SendOTP["Send OTP via Gmail"]
        SendOTP --> VerifyOTP["Verify OTP Code"]
        VerifyOTP --> OTPCheck{"OTP Valid?"}
        OTPCheck -- No --> EnterOTP
        OTPCheck -- Yes --> DisplayList["Display Clothes List"]
        DisplayList --> Browse
        PayFee --> ProcPay["Process Payment"]
        ProcPay --> PayCheck{"Payment Successful?"}
        PayCheck -- No --> RetryPay
        PayCheck -- Yes --> SaveBooking["Save Booking Details"]
        SaveBooking --> GenConf["Generate Confirmation"]
    end

    %% Node Styling
    classDef startEnd fill:#22c55e,stroke:#15803d,color:#ffffff,stroke-width:2px;
    classDef endStyle fill:#ef4444,stroke:#b91c1c,color:#ffffff,stroke-width:2px;
    classDef action fill:#1e293b,stroke:#475569,color:#f8fafc,stroke-width:1px;
    classDef decision fill:#334155,stroke:#64748b,color:#f8fafc,stroke-width:1px;

    class Start startEnd;
    class EndNode endStyle;
    class OpenWeb,Auth,EnterEmail,EnterOTP,Browse,SelectCloth,ChooseDate,BookingDetails,PayFee,RetryPay,ViewConf,SendOTP,VerifyOTP,DisplayList,ProcPay,SaveBooking,GenConf action;
    class OTPCheck,PayCheck decision;
```

---

## Process Breakdown

### 1. Authentication & Security Flow
1. **User**: Opens the website and clicks **Login / Sign Up**.
2. **User**: Submits their registered **Email Address**.
3. **System**: Generates a 6-digit OTP and dispatches it via Gmail SMTP (`polakash918@gmail.com`).
4. **System**: Verifies the submitted OTP code.
   - **Invalid**: System prompts the user to re-enter the code.
   - **Valid**: System authorizes the user session and renders the clothes catalog.

### 2. Clothing Selection & Trial Booking
1. **User**: Browses the available clothing collection (Men, Women, Sarees, Kurtis, Shoes, etc.).
2. **User**: Selects a garment and chooses an available trial date.
3. **User**: Enters trial delivery address and booking details.
4. **User**: Submits trial fee payment.

### 3. Payment & Booking Confirmation
1. **System**: Processes the transaction via payment gateway.
   - **Payment Failed**: Returns user to the payment retry step.
   - **Payment Successful**: Saves trial booking records in the MySQL database and generates booking confirmation receipt.
2. **User**: Views booking confirmation on dashboard.
