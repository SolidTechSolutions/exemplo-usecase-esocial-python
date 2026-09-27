"""
[EN]    Signs an eSocial event XML (any S-xxxx event) with the employer's e-CPF/e-CNPJ
        certificate, using a SolidSign KMS-custodied certificate
        (POST /solidsign/dsig/xml/sign-kms). Always signs the ENTIRE document with the same
        fixed parameters, regardless of event type.

[PT-BR] Assina o XML de um evento eSocial (qualquer evento S-xxxx) com o certificado
        e-CPF/e-CNPJ do empregador, via KMS SolidSign. Sempre assina o DOCUMENTO INTEIRO.
"""

import logging
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def sign(content: bytes, filename: str, kms_code: str) -> Optional[bytes]:
    base_url = os.getenv("SOLIDSIGN_API_BASE_URL", "").rstrip("/")
    authorization = os.getenv("SOLIDSIGN_API_AUTHORIZATION", "")

    sign_url = base_url + "/solidsign/dsig/xml/sign-kms"
    headers = {"Authorization": authorization}
    files = {"document[0]": (filename, content, "application/xml")}
    data = {
        "kmsCode": kms_code,
        "profile": os.getenv("SOLIDSIGN_ESOCIAL_PROFILE", "XML_INTERNATIONAL"),
        "hashAlgorithm": os.getenv("SOLIDSIGN_ESOCIAL_HASH_ALGORITHM", "SHA256"),
        "signaturePackaging": os.getenv("SOLIDSIGN_ESOCIAL_SIGNATURE_PACKAGING", "ENVELOPED"),
        "canonicalizationMethod": os.getenv("SOLIDSIGN_ESOCIAL_CANONICALIZATION_METHOD", "INCLUSIVE"),
        "isRemoveXPathExclusionFilter": os.getenv("SOLIDSIGN_ESOCIAL_REMOVE_XPATH_FILTER", "true"),
        "isRemoveNamespacePrefixFromNodeNames": os.getenv("SOLIDSIGN_ESOCIAL_REMOVE_NAMESPACE_PREFIX", "true"),
    }

    try:
        resp = requests.post(sign_url, headers=headers, files=files, data=data, timeout=120)
        resp.raise_for_status()
        sign_resp = resp.json()

        documents = sign_resp.get("documents", [])
        if not documents:
            logger.error("SolidSign response had no documents.")
            return None

        doc = documents[0]
        links_obj = doc.get("_links") or {}
        download_url = (links_obj.get("self") or {}).get("href")
        if not download_url:
            download_url = next(
                (lnk["href"] for lnk in doc.get("links", []) if lnk.get("rel") == "self"), None,
            )
        if not download_url:
            logger.error("SolidSign response had no download link.")
            return None

        dl = requests.get(download_url, headers=headers, timeout=120)
        return dl.content if dl.status_code == 200 else None

    except requests.HTTPError as e:
        logger.error("SolidSign API error %s: %s", e.response.status_code, e.response.text)
    except Exception as e:
        logger.error("Unexpected error during eSocial event signing: %s", e)

    return None
