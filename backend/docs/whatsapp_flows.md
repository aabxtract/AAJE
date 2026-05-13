# AAJE WhatsApp Flows

AAJE should use voice/chat for daily hustle actions and WhatsApp Flows for admin or sensitive moments.

## Flow Moments

1. Onboarding Profile
   Collects `full_name`, `location`, `business_type`, `account_number`, and `bank_name`.

2. Business Vault Setup
   Collects `primary_business_name`, optional `has_second_business` and `second_business_name`, plus `primary_split`, optional `second_split`, `savings_split`, and `emergency_split`.

3. PIN Setup
   Collects `pin` and `pin_confirm`. The backend validates both values, rejects weak PINs, and stores only the hash.

4. PIN Confirmation
   Collects `pin` for withdrawals and supplier payments. This replaces asking the trader to type the PIN as a normal chat message.

5. Business Passport
   Reserved for a structured view of balances, savings behavior, and credit grade. The sender helper is ready, but no agent currently launches it.

## Environment Variables

Paste the Flow IDs from the Meta Dashboard into:

```env
META_ONBOARDING_PROFILE_FLOW_ID=
META_BUSINESS_SETUP_FLOW_ID=
META_PIN_SETUP_FLOW_ID=
META_PIN_CONFIRM_FLOW_ID=
META_PASSPORT_FLOW_ID=
META_FLOW_PRIVATE_KEY=
META_FLOW_PRIVATE_KEY_PATH=
META_FLOW_PRIVATE_KEY_PASSPHRASE=
```

If a Flow ID is missing, AAJE falls back to the existing chat-based flow for that step.

Use either `META_FLOW_PRIVATE_KEY` with escaped newlines or `META_FLOW_PRIVATE_KEY_PATH`
pointing to the PEM file used for WhatsApp Flow endpoint encryption. Set
`META_FLOW_PRIVATE_KEY_PASSPHRASE` only if the private key is encrypted.

## Flow Endpoint

For any Flow configured with dynamic data or `data_exchange`, set the Meta Flow
endpoint URL to:

```text
{APP_PUBLIC_URL}/webhook/whatsapp/flows
```

For production, `APP_PUBLIC_URL` must be a public HTTPS URL with a valid SSL
certificate. The endpoint decrypts Meta's request, handles the health-check
`ping`, returns `421` when a request cannot be decrypted, and returns Meta's
required encrypted plaintext response. A plain JSON response will fail Meta's
integrity validation.

When configuring the endpoint in Meta:

1. Generate a 2048-bit RSA key pair.
2. Upload the public key to the WhatsApp Flow configuration.
3. Store the matching private key in `META_FLOW_PRIVATE_KEY` or
   `META_FLOW_PRIVATE_KEY_PATH`.
4. Confirm the endpoint health check succeeds before publishing the Flow.

Endpoint-backed Flow JSON must include:

```json
"data_api_version": "3.0"
```

The normal WhatsApp webhook remains:

```text
{APP_PUBLIC_URL}/webhook/whatsapp
```

## Browser Flow Fallback

While Meta Flow integrity or business verification blocks native Flow testing,
AAJE sends WhatsApp CTA links to a browser-rendered compatibility layer instead
of launching native Flows.

The public link format is:

```text
{APP_PUBLIC_URL}/flow?token={SESSION_ID}
```

Set `APP_PUBLIC_URL` to the public HTTPS ngrok or deployed backend URL. The
renderer loads the existing JSON files from `whatsapp_flows/`, preserves the
same payload structure, and submits responses back into the existing
`route_flow_response` backend path. Native WhatsApp Flow sending remains in
`app.services.whatsapp_client.send_flow` so the delivery layer can be swapped
back later.

## Builder Field Names

Use these exact field names in Meta's Flows Builder so the backend can read submissions:

```text
onboarding_profile:
full_name
location
business_type
account_number
bank_name

business_setup:
primary_business_name
has_second_business
second_business_name
primary_split
second_split
savings_split
emergency_split

pin_setup:
pin
pin_confirm

pin_confirm:
pin

business_passport:
full_name
trader_score
credit_grade
recommended_loan_ceiling
```
