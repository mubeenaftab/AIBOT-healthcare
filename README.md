# AI Healthcare Bot

**AI Healthcare Bot** is a multi-user healthcare application with a chatbot that assists patients in managing their health concerns. This project is built to facilitate three user roles: **Doctors**, **Patients**, and **Admins**, each with specific features and functionalities.

---

## Table of Contents
- [Features](#features)
- [User Roles](#user-roles)
  - [Doctor](#doctor)
  - [Patient](#patient)
  - [Admin](#admin)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running the Backend](#running-the-backend)
- [Technologies Used](#technologies-used)
  
---

## Features

- **Doctor Management:** View, manage, and update appointments with a notification system for new bookings.
- **Patient Chatbot Assistance:** The chatbot analyzes patient symptoms to provide remedies or suggest specialists for further consultation.
- **Admin Dashboard:** Allows admins to manage users and appointments efficiently.
- **Prescription Management and Reminder System:** Doctors can add prescriptions post-appointment, and patients receive automated reminders for medications.

---

## User Roles

### Doctor

- **Manage Availability**: Add and manage timeslots for patient appointments.
- **View and Update Appointments**: View both active and inactive appointments.
- **Add Prescriptions**: After marking an appointment as inactive, a prescription pop-up appears for the doctor to fill.
- **Receive Notifications**: Real-time notifications via WebSocket on patient bookings.

### Patient

- **Chatbot Symptom Analysis**: The chatbot assesses symptom severity to recommend remedies or doctors.
- **Specialist Recommendations**: Suggests doctors based on the detected specialization for the patient’s symptoms.
- **Prescription Access**: Patients can access their prescriptions through the bot after their consultation.
- **Reminder Activation**: Patients can activate medication reminders and adjust the notification times.
- **Automated Reminders**: At the set time, a reminder notification for taking prescribed medication is generated.

### Admin

- **User and Appointment Management**: Admins can view, edit, or delete doctors, patients, and appointment records.

---

## Getting Started

Follow these instructions to set up and run the backend application on your local machine.

### Prerequisites

- Python 3.8+
- FastAPI
- Uvicorn
- APScheduler (for task scheduling)
- OpenAI API key (for chatbot functionality)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   ```
2. **Navigate to the project directory**:
   ```bash
   cd be-aibot-healthcare
   ```
3. **Set up a virtual environment**:
   ```bash
   python -m venv env
   source env/bin/activate   # On Windows use `env\Scripts\activate`
   ```
4. **Install the required packages**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Add environment variables**: Create a `.env` file in the root directory with the necessary environment variables (e.g., database URL, OpenAI API key).

---

## Environment Variables

The following variables should be added to your `.env` file:

```
DATABASE_URL=your_database_url
OPENAI_API_KEY=your_openai_api_key
# Add any additional variables here
```

---

## Running the Backend

To start the backend server:

1. **Navigate to the backend folder**:
   ```bash
   cd backend
   ```
2. **Run the backend application**:
   ```bash
   uvicorn src.main:backend_app --reload
   ```

The application will be accessible at `http://127.0.0.1:8000`.

---

## Technologies Used

- **FastAPI**: For building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **OpenAI API**: For GPT-powered chatbot assistance
- **APScheduler**: For scheduling reminders
- **WebSockets**: For real-time notifications to doctors

---


**Project developed by Chemsa Technologies**
