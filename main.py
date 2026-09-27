"""
[EN]    eSocial use case — single sign-evento endpoint, KMS custody.
        Start: uvicorn main:app --port 8105 --reload

[PT-BR] Caso de uso eSocial — endpoint único de assinatura, custódia KMS.
        Iniciar: uvicorn main:app --port 8105 --reload
"""

import logging

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import Response

import service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

app = FastAPI(title="SolidSign — eSocial Use Case")


@app.post("/api/esocial/sign-evento")
async def sign_evento(
    document: UploadFile = File(...),
    kmsCode: str = Form(...),
):
    content = await document.read()
    signed = service.sign(content, document.filename, kmsCode)
    if signed:
        return Response(
            content=signed, media_type="application/xml",
            headers={"Content-Disposition": 'attachment; filename="evento_esocial_signed.xml"'},
        )
    return Response(content="Signing failed. Check logs.", status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8105)
