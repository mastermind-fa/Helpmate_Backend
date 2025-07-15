from fastapi.responses import HTMLResponse

@app.get("/payment/success", response_class=HTMLResponse)
def payment_success():
    return """
    <html><head><title>Payment Success</title></head>
    <body style='font-family:sans-serif;text-align:center;padding-top:50px;'>
      <h1 style='color:green;'>Payment Successful!</h1>
      <p>Your payment was processed successfully. You can close this window and return to the app.</p>
    </body></html>
    """

@app.get("/payment/fail", response_class=HTMLResponse)
def payment_fail():
    return """
    <html><head><title>Payment Failed</title></head>
    <body style='font-family:sans-serif;text-align:center;padding-top:50px;'>
      <h1 style='color:red;'>Payment Failed</h1>
      <p>Your payment was not successful. Please try again or contact support.</p>
    </body></html>
    """

@app.get("/payment/cancel", response_class=HTMLResponse)
def payment_cancel():
    return """
    <html><head><title>Payment Cancelled</title></head>
    <body style='font-family:sans-serif;text-align:center;padding-top:50px;'>
      <h1 style='color:orange;'>Payment Cancelled</h1>
      <p>You have cancelled the payment. You can try again from the app.</p>
    </body></html>
    """ 