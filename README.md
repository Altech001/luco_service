<!-- # luco_service

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
#             print(f"Payment {OrderTrackingId} completed successfully.")

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

 -->
