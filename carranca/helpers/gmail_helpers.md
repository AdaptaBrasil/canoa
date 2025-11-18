# 🔑 Gmail API Authentication in Canoa

The Canoa project utilizes the **Gmail API** for sending emails and supports two distinct authentication methods: **Service Account (Domain-Wide Delegation - DWD)** for server-to-server automation, and **OAuth 2.0** for user-authenticated flows.

The key to a successful deployment lies in matching the appropriate authentication method to the correct credential file and ensuring the primary helper file is configured.

---

## 1. The Unified Python Sender and Authentication Clients

The project uses three modular files to manage the email functionality, promoting **clarity and maintainability**:

* **`gmail_api_helper.py` (Unified Sender):**
    This is the **only file** you interact with in your application logic. It contains the unified `send_mail()` function, which automatically selects the authentication method based on the application's configuration flag (`USE_SERVICE_ACCOUNT_DWD`).
* **`gmail_dwd_helper.py`:**
    Handles the **Domain-Wide Delegation (DWD)** authentication logic using the Service Account key.
* **`gmail_oauth_helper.py`:**
    Handles the **OAuth 2.0** flow, which requires user consent and manages the `token.json` lifecycle.

---

## 2. Credential Files and Storage

The authentication method used at runtime is determined by which credential file is present or enabled in your configuration. All credential files must reside in your local configuration path, typically in the `carranca/LocalStorage/` directory.

| File Name | Authentication Method | Purpose |
| :--- | :--- | :--- |
| **`canoa-gmail-key.json`** | **Service Account (DWD)** | Your **private key** used for automated, server-to-server tasks that impersonate a user in a Google Workspace domain. |
| **`canoa-gmail-oauth.json`** | **OAuth 2.0 Client Secrets** | The file used to initiate the interactive user login flow (Client Secrets). |
| **`token.json`** | **OAuth 2.0 Token** | The **refresh token** generated after the first successful user login, allowing subsequent, non-interactive use. |

---

## 3. Authentication Summary and Use Cases

| Authentication Method | Authentication Client File | Primary Use Case |
| :--- | :--- | :--- |
| **Service Account (DWD)** | `gmail_dwd_helper.py` | **CURRENT PRIMARY CHOICE.** For high-volume, automated **server-side tasks** (e.g., sending system notifications, scheduled reports, welcome emails) without requiring a user to be logged in. |
| **OAuth 2.0 (User Consent)** | `gmail_oauth_helper.py` | For applications where a specific **end-user logs in** and grants permission for the application to act on their behalf. |

---

## 🔗 Google Cloud Console Resources

To manage and generate the necessary credentials for both methods, use the following link:

* **Google Cloud Console Gmail API Library:** [https://console.cloud.google.com/apis/library/gmail.googleapis.com](https://console.cloud.google.com/apis/library/gmail.googleapis.com)