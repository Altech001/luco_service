from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from auth.authapp import get_current_user
from db_connect  import get_db
from lucopay.pesapal.pesapal_client import PesapalClientError, get_transaction_status, register_ipn_url, submit_order
import models

from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import json



@asynccontextmanager
async def lifespan(app: APIRouter):
    
    print("Application starting up...")
    print("Attempting to register IPN URL...")
    try:
        await register_ipn_url()
    except PesapalClientError as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!  CRITICAL: FAILED TO REGISTER IPN ON STARTUP !!")
        print(f"!!  ERROR: {e} !!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    yield
    
    print("Application shutting down...")


lucopay_router = APIRouter(
    prefix="/v1/lucopay",
    tags=["Lucopay"],
    lifespan=lifespan
)


#-----------------
# User Models
#-----------------

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    wallet_balance: float
    clerk_user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class WalletTopup(BaseModel):
    amount: float
    
class PaymentRequest(BaseModel):
    amount: float
    email: EmailStr
    phone_number: str
    first_name: str
    last_name: str

@lucopay_router.post("/wallets/topup", response_model=UserResponse)
def topup_wallet(user_id: str, topup: WalletTopup, db: Session = Depends(get_db)):
    
    
    
    if topup.amount <= 0:
        raise HTTPException(status_code=400, detail="Top-up amount must be positive")
    
    db_user = db.query(models.User).filter(models.User.clerk_user_id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.wallet_balance += topup.amount
        
    
    new_transaction = models.Transaction(
        user_id=db_user.id,
        amount=topup.amount,
        transaction_type="credit"
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(db_user)
    return db_user


@lucopay_router.post("/initiate-payment")
async def initiate_payment(payment_request: PaymentRequest):
    """
    Endpoint to initiate a new payment.
    """
    print(f"Initiating payment for {payment_request.email} for amount {payment_request.amount}")
    try:
        order_response = await submit_order(
            amount=payment_request.amount,
            email=payment_request.email,
            phone=payment_request.phone_number,
            first_name=payment_request.first_name,
            last_name=payment_request.last_name,
        )
        return {
            "message": "Order initiated successfully.",
            "redirect_url": order_response.get("redirect_url"),
            "order_tracking_id": order_response.get("order_tracking_id"),
        }
    except PesapalClientError as e:
        print(f"ERROR: Pesapal client failed during payment initiation: {e}")
        raise HTTPException(status_code=500, detail=f"Pesapal API Error: {e.response_text}")

# @lucopay_router.get("/payment-callback")
# async def payment_callback(OrderTrackingId: str):
#     """
#     Handles the user redirect from Pesapal. Fetches the transaction status
#     and displays a dynamic status page.
#     """
#     print(f"Received payment callback for OrderTrackingId: {OrderTrackingId}")
#     context = {}
#     try:
#         status_response = await get_transaction_status(OrderTrackingId)
#         status = status_response.get("payment_status_description", "UNKNOWN").upper()

#         if status == "COMPLETED":
#             context["title"] = "Payment Successful!"
#             context["message"] = "Thank you for your payment."
#             context["status_class"] = "status-success"
#         elif status == "PENDING":
#             context["title"] = "Payment Pending"
#             context["message"] = "Your payment is currently being processed. You will receive a confirmation shortly."
#             context["status_class"] = "status-pending"
#         else: # FAILED or UNKNOWN
#             context["title"] = "Payment Failed"
#             context["message"] = f"Your payment could not be completed. The status is: {status.title()}"
#             context["status_class"] = "status-failed"

#     except PesapalClientError as e:
#         print(f"ERROR: Pesapal client failed during payment callback: {e}")
#         context["title"] = "Error"
#         context["message"] = f"We could not confirm your payment status. Details: {e.response_text}"
#         context["status_class"] = "status-failed"

#     return {
#         "title": context["title"],
#         "message": context["message"],
#         "status_class": context["status_class"],
#         "request": context["request"]
#     }

@lucopay_router.get("/payment-callback")
async def payment_callback(OrderTrackingId: str):
    print(f"Received payment callback for OrderTrackingId: {OrderTrackingId}")
    response = {"status": "error", "title": "Error", "message": "Unknown error", "status_class": "status-failed"}
    try:
        status_response = await get_transaction_status(OrderTrackingId)
        print(f"Status response: {status_response}")
        status = status_response.get("payment_status_description", "UNKNOWN").upper()
        if status == "COMPLETED":
            response.update({
                "status": "success",
                "title": "Payment Successful!",
                "message": "Thank you for your payment.",
                "status_class": "status-success"
            })
        elif status == "PENDING":
            response.update({
                "status": "pending",
                "title": "Payment Pending",
                "message": "Your payment is currently being processed. You will receive a confirmation shortly.",
                "status_class": "status-pending"
            })
        else:
            response.update({
                "status": "failed",
                "title": "Payment Failed",
                "message": f"Your payment could not be completed. The status is: {status.title()}",
                "status_class": "status-failed"
            })
    except PesapalClientError as e:
        print(f"ERROR: Pesapal client failed during payment callback: {e}")
        response["message"] = f"We could not confirm your payment status. Details: {str(e)}"
    except Exception as e:
        print(f"Unexpected error in payment callback: {e}")
        response["message"] = "An unexpected error occurred."

    return response


@lucopay_router.post("/ipn-webhook")
async def ipn_webhook(request: Request, db: Session = Depends(get_db)):
    print(f"Received IPN webhook call from {request.client.host} with path {request.url.path}")
    ipn_data = await request.json()
    print("IPN Payload:", json.dumps(ipn_data, indent=2))

    # Extract details from the IPN payload
    order_tracking_id = ipn_data.get("orderTrackingId")
    payment_status = ipn_data.get("payment_status_description")
    amount_str = ipn_data.get("amount")
    
    # NOTE: The email is often in a nested object. This key might need verification
    # based on the actual Pesapal IPN payload.
    
    email = ipn_data.get("billing_address", {}).get("email_address")

    # Acknowledge receipt to Pesapal immediately.
    response_data = {
        "orderNotificationType": ipn_data.get("orderNotificationType"),
        "orderTrackingId": order_tracking_id,
        "status": "OK"
    }

    # Only process successful, completed payments
    if payment_status == "COMPLETED":
        if not all([amount_str, email]):
            print(f"CRITICAL: IPN {order_tracking_id} is COMPLETED but missing amount or email.")
            return response_data # Acknowledge but do not process

        try:
            amount = float(amount_str)
            # Find the user by email
            db_user = db.query(models.User).filter(models.User.email == email).first()
            if not db_user:
                print(f"CRITICAL: User with email {email} not found for completed payment {order_tracking_id}.")
                return response_data # Acknowledge but do not process

            # Update wallet and create a transaction record, similar to topup_wallet
            db_user.wallet_balance += amount
            
            new_transaction = models.Transaction(
                user_id=db_user.id,
                amount=amount,
                transaction_type="credit"
            )
            db.add(new_transaction)
            db.commit()
            
            print(f"Successfully processed payment for {email}, amount {amount}. Order ID: {order_tracking_id}")

        except (ValueError, TypeError) as e:
            print(f"Error converting amount '{amount_str}' to float for IPN {order_tracking_id}: {e}")
            db.rollback()
        except Exception as e:
            print(f"Error processing completed IPN {order_tracking_id}: {e}")
            db.rollback()
    
    else:
        print(f"IPN received for order {order_tracking_id} with status: {payment_status}. No action taken.")

    return response_data
