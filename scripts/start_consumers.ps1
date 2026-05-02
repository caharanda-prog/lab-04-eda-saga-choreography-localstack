Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m services.inventory_consumer"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m services.payment_consumer"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m services.order_consumer"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m services.audit_consumer"