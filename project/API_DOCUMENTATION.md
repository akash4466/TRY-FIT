# OTP Authentication API Documentation

Production-ready REST API in Python supporting OTP-based authentication for **Signup** and **Login** using mobile numbers.

---

## Technical Features & Security Architecture

1. **HMAC-SHA256 OTP Hashing**: OTP codes are never stored in plain text in the database.
2. **Strict Expiry Policy**: OTPs automatically expire after 5 minutes (`OTP_EXPIRY_MINUTES=5`).
3. **Single Active OTP Enforced**: Requests for new OTPs immediately invalidate prior active OTPs for the same phone number.
4. **Rate Limiting & Cooldown**: Only 1 OTP request allowed every 30 seconds (`OTP_COOLDOWN_SECONDS=30`).
5. **Brute-Force Protection**: Maximum 5 failed verification attempts per OTP code before automatic invalidation (`OTP_MAX_ATTEMPTS=5`).
6. **SQL Injection Prevention**: Parameterized queries using PyMySQL DictCursors.
7. **Input Validation**: Strict regex validation for 10-digit Indian mobile numbers (`^[6-9]\d{9}$`) and RFC-compliant emails.
8. **Pluggable SMS Gateway**: Switch between **Fast2SMS**, **Twilio**, **MSG91**, **ContactWise**, or **Console/Dev** mode via `.env` configuration.

---

## API Endpoints Reference

Base URL: `http://localhost:5000/api`

---

### 1. Send OTP

Generates a 6-digit OTP code, hashes it into the database, and dispatches it via SMS.

- **Method**: `POST`
- **URL**: `/api/send-otp`
- **Headers**: `Content-Type: application/json`

#### Request Body
```json
{
  "phone": "9876543210"
}
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

#### Rate Limit Exceeded (`429 Too Many Requests`)
```json
{
  "success": false,
  "message": "Please wait 24 seconds before requesting a new OTP."
}
```

---

### 2. Verify OTP

Verifies the submitted 6-digit OTP code against the stored HMAC-SHA256 hash.

- **Method**: `POST`
- **URL**: `/api/verify-otp`
- **Headers**: `Content-Type: application/json`

#### Request Body
```json
{
  "phone": "9876543210",
  "otp": "123456"
}
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "OTP verified"
}
```

#### Incorrect OTP (`400 Bad Request`)
```json
{
  "success": false,
  "message": "Incorrect OTP. 4 attempt(s) remaining."
}
```

#### Expired / Max Attempts Exceeded (`400 / 429`)
```json
{
  "success": false,
  "message": "OTP has expired. Please request a new verification code."
}
```

---

### 3. Signup

Registers a new user after successful OTP verification.

- **Method**: `POST`
- **URL**: `/api/signup`
- **Headers**: `Content-Type: application/json`

#### Request Body
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "9876543210"
}
```

#### Success Response (`201 Created`)
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Unverified Phone Error (`400 Bad Request`)
```json
{
  "success": false,
  "message": "Phone number is not verified. Please complete OTP verification first."
}
```

---

### 4. Login

Sends a login OTP to a registered mobile number, or verifies the OTP and returns a JWT session token.

- **Method**: `POST`
- **URL**: `/api/login`
- **Headers**: `Content-Type: application/json`

#### Step A: Request Login OTP
```json
{
  "phone": "9876543210"
}
```
**Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Login OTP sent successfully"
}
```

#### Step B: Verify Login OTP
```json
{
  "phone": "9876543210",
  "otp": "123456"
}
```
**Response (`200 OK`)**:
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
