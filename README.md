<!-- # luco_service

@lucopay_router.get("/payment-callback")
async def payment_callback(OrderTrackingId: str , db: Session = Depends(get_db)):
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
            print(f"Payment {OrderTrackingId} completed successfully.")

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
 -->
