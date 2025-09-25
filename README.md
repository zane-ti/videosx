# Video Store Full - Backend + React frontend

This project includes:
- Flask backend with user auth (buyers & sellers), upload endpoint, Stripe checkout creation and webhook handler, temporary download tokens.
- React frontend (in `frontend/`) that fetches products and initiates checkout.
- Dockerfile (multi-stage) that builds React and runs Flask with Gunicorn.
- render.yaml for Render.com Docker deployment.

Important notes:
- Replace placeholder user password hashes in `schema_full.sql` if you want seeded users.
- Set these environment variables in Render (or Docker): FLASK_SECRET_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET.
- Upload your MP4 files to the `videos/` directory or use the seller upload endpoint.
- For Stripe webhooks to work on Render, set the webhook endpoint to `https://<your-service>.onrender.com/stripe/webhook` and set the webhook secret into STRIPE_WEBHOOK_SECRET.
- This is a starter implementation. For production: protect uploads, use object storage (S3/R2), implement proper order-item mapping, validate webhooks, secure file serving, and implement rate-limiting.

To build locally:
- Backend: `pip install -r requirements.txt` then `python app.py`
- Frontend: `cd frontend && npm install && npm run build` (or use Dockerfile)

